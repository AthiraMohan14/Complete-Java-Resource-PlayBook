# Async Work and Threading in Spring Boot

Spring lets you run work off the request thread with `@Async`, return results as `CompletableFuture`, and size the executors that do the work. Interviewers ask about this to see whether you understand where the work actually runs, why an `@Async` annotation sometimes does nothing, and when virtual threads make a reactive stack unnecessary.

## Core concepts

### Enabling @Async

`@Async` only works after you turn on async processing with `@EnableAsync`. Spring then wraps the bean in a proxy, and each call to an annotated method is handed to a `TaskExecutor` instead of running on the caller's thread.

```java
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration
@EnableAsync
class AsyncSettings {
}
```

### Return types

An `@Async` method can return `void`, `Future<T>`, or `CompletableFuture<T>`. A `void` method is fire-and-forget: the caller gets nothing back, and failures go to an uncaught-exception handler. A `CompletableFuture` lets the caller compose, wait for, or time out the result.

```java
import java.util.concurrent.CompletableFuture;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
class ReceiptMailer {

    @Async
    public void sendReceipt(String address) {
        // runs on an executor thread; the caller does not wait
    }

    @Async
    public CompletableFuture<Boolean> sendReceiptChecked(String address) {
        boolean delivered = address.contains("@");   // stand-in for a real send
        return CompletableFuture.completedFuture(delivered);
    }
}
```

A plain `String` or `boolean` return type is ignored for asynchrony, because the method still runs synchronously from the caller's point of view. Return a `CompletableFuture` when you need a result.

### The self-invocation trap

The proxy only intercepts calls that come from outside the bean. If a method in the same class calls an `@Async` method directly, the call runs synchronously. The fix is to move the async method into another bean, which is the cleanest option. Injecting the bean into itself also works, but it is a sign the class has too many jobs.

```java
import org.springframework.stereotype.Service;

@Service
class OrderService {

    private final ReceiptMailer mailer;

    OrderService(ReceiptMailer mailer) {   // a different bean, so the proxy is used
        this.mailer = mailer;
    }

    void complete(String address) {
        mailer.sendReceipt(address);       // asynchronous
    }
}
```

### Configuring a TaskExecutor

Spring Boot auto-configures an executor named `applicationTaskExecutor`, backed by a `ThreadPoolTaskExecutor`. If you define your own bean of type `Executor` or `TaskExecutor`, Boot backs off from its default, so check which executor your `@Async` methods actually use.

```java
import java.util.concurrent.Executor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Configuration
class ExecutorSettings {

    @Bean(name = "mailExecutor")
    Executor mailExecutor() {
        ThreadPoolTaskExecutor pool = new ThreadPoolTaskExecutor();
        pool.setCorePoolSize(4);
        pool.setMaxPoolSize(8);
        pool.setQueueCapacity(200);
        pool.setThreadNamePrefix("mail-");
        pool.setWaitForTasksToCompleteOnShutdown(true);
        pool.setAwaitTerminationSeconds(30);
        pool.initialize();
        return pool;
    }
}
```

Name the executor on the annotation to route work to it:

```java
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
class ReportJobs {

    @Async("reportExecutor")   // needs a bean called "reportExecutor"
    public void buildNightlyReport() {
        // long-running work kept away from the mail pool
    }
}
```

Size the pool for the kind of work. I/O-bound work tolerates more threads than CPU-bound work, and the queue capacity decides how much waiting is allowed before callers are rejected.

### Composing CompletableFuture results

`CompletableFuture` lets you describe a pipeline of steps. Pass your own executor to `supplyAsync`, because the default common pool is shared by the whole JVM and is a poor place for blocking I/O.

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import org.springframework.stereotype.Service;

@Service
class PriceService {

    private final Executor ioPool;

    PriceService(Executor ioPool) {
        this.ioPool = ioPool;
    }

    CompletableFuture<Integer> total(int unitPrice, int quantity) {
        CompletableFuture<Integer> base =
                CompletableFuture.supplyAsync(() -> unitPrice * quantity, ioPool);
        CompletableFuture<Integer> tax =
                CompletableFuture.supplyAsync(() -> (unitPrice * quantity) / 10, ioPool);
        return base.thenCombine(tax, Integer::sum);   // runs once both are done
    }
}
```

The operators you will be asked about:

| Method | Purpose |
|---|---|
| `thenApply` | Transform a result (synchronous mapping) |
| `thenCompose` | Chain a step that itself returns a future |
| `thenCombine` | Merge two independent futures |
| `allOf` / `anyOf` | Wait for all, or for the first |
| `exceptionally` | Supply a fallback value for a failure |
| `handle` | Receive either the result or the exception |
| `orTimeout` / `completeOnTimeout` | Fail or fall back after a deadline (Java 9+) |

`exceptionally` only sees failures from earlier stages in the chain. Put it after the step that might fail.

### A controller that returns a CompletableFuture

Spring MVC accepts a `CompletableFuture` as a controller return value. The request thread is released while the work runs, and the response is written when the future completes. This is the usual way to fan out several independent calls: start them together, then combine them with `allOf`.

```java
import java.util.List;
import java.util.concurrent.CompletableFuture;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record Price(long cents) { }
record ProductPage(String sku, Price price, int unitsInStock, List<String> reviews) { }

interface PricingClient { CompletableFuture<Price> priceFor(String sku); }
interface StockClient { CompletableFuture<Integer> unitsFor(String sku); }
interface ReviewClient { CompletableFuture<List<String>> latestFor(String sku); }

@RestController
@RequestMapping("/api/product-pages")
class ProductPageController {

    private final PricingClient pricing;
    private final StockClient stock;
    private final ReviewClient reviews;

    ProductPageController(PricingClient pricing, StockClient stock, ReviewClient reviews) {
        this.pricing = pricing;
        this.stock = stock;
        this.reviews = reviews;
    }

    @GetMapping("/{sku}")
    CompletableFuture<ResponseEntity<ProductPage>> page(@PathVariable String sku) {
        CompletableFuture<Price> price = pricing.priceFor(sku);     // all three start now
        CompletableFuture<Integer> units = stock.unitsFor(sku);
        CompletableFuture<List<String>> latest = reviews.latestFor(sku);

        return CompletableFuture.allOf(price, units, latest)
                .thenApply(done -> ResponseEntity.ok(
                        new ProductPage(sku, price.join(), units.join(), latest.join())));
    }
}
```

The three calls overlap, so the response takes about as long as the slowest call, not the sum of all three. `allOf` returns a `CompletableFuture<Void>` that completes only when every input has completed, which is why the `join` calls inside `thenApply` do not block. If any input fails, `allOf` fails too, so attach `exceptionally` or `exceptionallyCompose` when a partial page is acceptable.

### Falling back when a dependency fails

A cascading failure happens when one slow or broken dependency makes the callers fail too. A fallback stage can keep the flow going. `exceptionallyCompose` is the variant to use when the fallback is itself asynchronous, because it returns a future rather than a plain value.

```java
import java.util.concurrent.CompletableFuture;
import org.springframework.stereotype.Service;

interface PaymentClient { CompletableFuture<String> charge(String orderId, long cents); }
interface PendingQueue { CompletableFuture<Void> enqueue(String orderId); }

@Service
class CheckoutFlow {

    private final PaymentClient payments;
    private final PendingQueue pending;

    CheckoutFlow(PaymentClient payments, PendingQueue pending) {
        this.payments = payments;
        this.pending = pending;
    }

    CompletableFuture<String> checkout(String orderId, long cents) {
        return payments.charge(orderId, cents)
                .thenApply(receiptId -> "CONFIRMED:" + receiptId)
                .exceptionallyCompose(ex ->                  // payment failed or timed out
                        pending.enqueue(orderId)             // record it for a later retry
                               .thenApply(ignored -> "PENDING"));
    }
}
```

Two details matter here. The fallback must report honestly: `PENDING` tells the caller that the money has not moved, so the order flow has to handle it. Second, an exception that passes through a dependent stage is often wrapped in a `CompletionException`, so unwrap it with `getCause()` when you need the original type.

### Virtual threads

Java 21 finalised virtual threads. A virtual thread is cheap to create, and blocking it frees the carrier thread, so blocking code scales far better than it did with platform threads. In Spring Boot 3.2 and later, you can ask the framework to use them for request handling and for the default task executor:

```properties
spring.threads.virtual.enabled=true
```

If you need a custom executor for `@Async`, `SimpleAsyncTaskExecutor` can create virtual threads when you enable them explicitly:

```java
import org.springframework.core.task.SimpleAsyncTaskExecutor;
import org.springframework.core.task.TaskExecutor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class VirtualExecutorSettings {

    @Bean(name = "virtualExecutor")
    TaskExecutor virtualExecutor() {
        SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor("vt-");
        executor.setVirtualThreads(true);   // without this, it creates platform threads
        return executor;
    }
}
```

`SimpleAsyncTaskExecutor` does not pool threads. Without virtual threads it starts a new platform thread per task, which can grow without limit, so do not use it unbounded in production.

The property above also covers the servlet container on Boot 3.2 and later. If you want to control the request executor yourself, for example on an older Boot line or with a different executor policy, register a Tomcat customizer. It swaps the connector's executor for one that starts a virtual thread per task:

```java
import java.util.concurrent.Executors;
import org.apache.coyote.ProtocolHandler;
import org.springframework.boot.web.embedded.tomcat.TomcatProtocolHandlerCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class TomcatThreadingConfig {

    @Bean
    TomcatProtocolHandlerCustomizer<ProtocolHandler> virtualThreadRequests() {
        return protocol -> protocol.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    }
}
```

Each request then gets its own virtual thread, so a blocking handler parks cheaply. Keep the database connection pool bounded, because the threads are no longer the limit: the pool is.

### Scheduled tasks with @Scheduled

`@Scheduled` runs a method on a timer. It needs `@EnableScheduling` on a configuration class, and the method must return `void` and take no arguments.

```java
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Configuration
@EnableScheduling
class SchedulingSettings {
}

@Component
class MaintenanceJobs {

    @Scheduled(fixedRate = 60_000)                  // start every 60 s, measured start to start
    void heartbeat() {
    }

    @Scheduled(fixedDelay = 30_000, initialDelay = 10_000)   // 30 s after the previous run ends
    void syncCatalog() {
    }

    @Scheduled(cron = "0 30 2 * * *", zone = "Europe/London")  // 02:30 every day
    void nightlyCleanup() {
    }
}
```

The three attributes answer different questions. `fixedRate` keeps a steady cadence, measured from one start to the next. `fixedDelay` waits a fixed time after each run finishes, so runs never stack up. `cron` uses six fields in Spring's order: second, minute, hour, day of month, month, and day of week. Use `initialDelay` to avoid starting everything at once when the application boots.

Three operational points come up in interviews:

- By default, all scheduled methods share one thread. A slow job delays the others. Raise `spring.task.scheduling.pool.size` when jobs overlap in time.
- Every instance of the service runs its own copy of each job. For a job that must run once across a cluster, use a lock, for example a database lock or a library such as ShedLock.
- A scheduled method that throws is logged, and the schedule continues. Do not rely on the exception to stop the job.

### Choosing between the three approaches

| Feature | `@Async` | `CompletableFuture` | Virtual threads |
|---|---|---|---|
| How you enable it | `@EnableAsync` plus the annotation | Plain Java; no annotation | Java 21, or `spring.threads.virtual.enabled` on Boot 3.2+ |
| Code shape | Method call that runs elsewhere | Explicit pipeline of stages | Ordinary blocking code |
| Return value | `void`, `Future`, or `CompletableFuture` | Always a future | Plain value |
| Composing results | Limited to what the return type allows | Strong: combine, chain, race, `allOf` | Not needed; call in sequence on the same thread |
| Error handling | Uncaught-exception handler for `void` | `exceptionally`, `handle`, `exceptionallyCompose` | Normal `try` and `catch` |
| Main risk | Self-invocation and wrong executor | Hard-to-read chains, forgotten `join` | Pinning on `synchronized` blocks, and unbounded concurrency |
| Best fit | Fire-and-forget work behind a service call | Fan-out and composition of several calls | Many blocking calls on Java 21 |

These are not mutually exclusive. A common combination is `@Async` on a virtual-thread executor for background work, with `CompletableFuture` used to compose the results.
With virtual threads, you can write a blocking sequence and let the thread wait cheaply:

```java
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
class FulfilmentService {

    @Async("virtualExecutor")
    public void fulfil(String orderId) {
        // each step blocks like ordinary code; the virtual thread parks while waiting
        reserveStock(orderId);
        chargeCard(orderId);
        notifyCustomer(orderId);
    }

    private void reserveStock(String orderId) { }
    private void chargeCard(String orderId) { }
    private void notifyCustomer(String orderId) { }
}
```

On Java 21, a virtual thread that blocks while holding a `synchronized` monitor is pinned to its carrier thread. Prefer `ReentrantLock` in code that blocks for a long time.

### Exceptions in async code

Exceptions behave differently depending on the return type:

- For `CompletableFuture` results, the exception is stored in the future. The caller sees it through `join`, `get`, or `exceptionally`.
- For `void` methods, the exception never reaches the caller. Register an `AsyncUncaughtExceptionHandler` by implementing `AsyncConfigurer`, so the failure is logged with the method name and parameters.

```java
import java.util.concurrent.Executor;
import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration
@EnableAsync
class AsyncErrors implements AsyncConfigurer {

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) ->
                System.err.println("Async failure in " + method.getName() + ": " + ex.getMessage());
    }
}
```

In a real service, use a logger rather than `System.err`, and do not log raw parameters that may hold personal data.

## How it works / Step by step

1. `@EnableAsync` registers an interceptor that wraps beans with `@Async` methods.
2. A call from outside the bean goes through the proxy, which packages the call as a task.
3. The task is submitted to the named executor, or to the default one.
4. The caller receives immediately: `void` returns nothing, and a future returns a handle.
5. When the task finishes, a `CompletableFuture` completes with the value or the exception. A failing `void` task goes to the uncaught-exception handler.

## Common pitfalls

- Calling an `@Async` method from the same class, so it runs synchronously.
- Forgetting `@EnableAsync`, so the annotation is silently ignored.
- Using the common `ForkJoinPool` for blocking I/O because `supplyAsync` was called without an executor.
- Returning a plain value from an `@Async` method and expecting the caller to receive it.
- Defining your own `Executor` bean without realising Boot's default executor is now replaced.
- Using an unbounded executor, which lets a traffic spike create unlimited threads or queue memory.
- Losing the request context (security principal, MDC log fields) on the executor thread unless you propagate it.

!!! tip "Interview tip"
    **Q: Does `@Async` make my method run in parallel with the caller?**
    Only if the call goes through the proxy and the executor has a free thread. A self-invoked method runs synchronously, and a method returning a plain value gives the caller nothing to wait on. Return a `CompletableFuture` when the caller needs the result, and mention the executor choice and the self-invocation trap.

## Quick recap

- `@Async` needs `@EnableAsync`, works only through the proxy, and should return `void`, `Future`, or `CompletableFuture`.
- Name your executor, bound its pool and queue, and check which executor Boot provides.
- Pass an explicit executor to `CompletableFuture.supplyAsync`.
- Use virtual threads (Java 21+, `spring.threads.virtual.enabled` on Boot 3.2+) for blocking I/O, and avoid `synchronized` around long blocking calls.
- Handle async failures per return type: the future for values, the uncaught-exception handler for `void`.

**See also:** [Executors and Futures](../02c-concurrency-io/executors-futures.md) | [Threads Basics](../02c-concurrency-io/threads-basics.md) | [Java 21 Features](../03a-modern-java/java21-features.md) | [Reactive WebFlux](reactive-webflux.md) | [Boot Basics and Configuration](boot-basics-configuration.md)
