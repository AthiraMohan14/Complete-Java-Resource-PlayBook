# Reactive Programming with Spring WebFlux

Spring WebFlux is the reactive web layer of Spring. It handles requests on a small number of event-loop threads and treats responses as streams of `Mono` (zero or one value) and `Flux` (zero to many values). Interviewers ask about it to test whether you know what "non-blocking" actually buys you, when it does not help, and how it differs from Spring MVC.

## Core concepts

### Reactive streams in one paragraph

A reactive stream is a publisher that emits values to a subscriber, with the subscriber controlling how many it can take (backpressure). Reactor, the library behind WebFlux, implements this with two types. Nothing runs until something subscribes, so a pipeline is a description of work rather than the work itself.

```java
import java.time.Duration;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

class ReactorBasics {
    public static void main(String[] args) throws InterruptedException {
        Mono<String> greeting = Mono.just("hello");   // nothing has run yet
        Flux<Integer> numbers = Flux.range(1, 3)
                .map(n -> n * 10);

        greeting.subscribe(System.out::println);       // work starts here
        numbers.subscribe(System.out::println);
        Flux.interval(Duration.ofMillis(100)).take(2)
                .subscribe(System.out::println);
        Thread.sleep(300);                             // keep the JVM alive for the interval demo
    }
}
```

### Four principles behind reactive design

The Reactive Manifesto describes four goals that reactive systems aim for. Interviewers like to hear them named, because they explain why the style exists at all:

- **Responsive:** the system answers within a bounded time, even when parts of it are slow or failing.
- **Resilient:** failure is contained in one component and handled by the caller, not spread across the system.
- **Elastic:** the system grows and shrinks with the load, without a fixed ceiling built into the design.
- **Message-driven:** components communicate through asynchronous messages or events, which keeps them loosely coupled and lets the sender continue without waiting.

These are goals, not features. A WebFlux application that calls a blocking database is not elastic, whatever its annotations say.

### Reactive compared with async/await

Both styles avoid waiting on the thread, but they describe the work differently. Async/await is a sequence of steps that look blocking and are paused at each `await`. Reactive code describes a pipeline of transformations that runs when data arrives.

| Aspect | Async/await | Reactive (Reactor) |
|---|---|---|
| How you describe work | Sequential steps with `await` between them | A pipeline of operators applied to a stream |
| Number of values | One result per call | Zero or one (`Mono`), or many over time (`Flux`) |
| Backpressure | Not part of the model | Built in; the subscriber controls the rate |
| Error handling | `try` and `catch` around each step | Error signals that operators such as `onErrorResume` handle |
| Cancellation | Depends on the library | Propagates upstream when the subscriber cancels |
| Ease of learning | Familiar to most developers | Steeper, because of the operator vocabulary |
| Best fit | A few concurrent async calls | Streams of events, many concurrent requests, and backpressure |

On Java 21 the virtual-thread model gives blocking code much of the scalability that once justified the reactive style. Reactive code still wins for streaming and backpressure, and async/await is simpler when the workload is a handful of independent calls.

### Mono and Flux

| Type | Elements | Typical source |
|---|---|---|
| `Mono<T>` | 0 or 1 | One record by id, a single HTTP response |
| `Flux<T>` | 0 to N | A query result, a stream of events |

`Mono.empty()` completes without a value, which is different from `null`. Use `switchIfEmpty` or `defaultIfEmpty` to say what should happen in that case.

### Operators you will be asked about

```java
import java.util.List;
import reactor.core.publisher.Flux;

class Operators {
    static void demo() {
        Flux.just(1, 2, 3, 4)
                .filter(n -> n % 2 == 0)     // keep 2, 4
                .map(n -> n * 3)             // 6, 12
                .subscribe(System.out::println);

        Flux.just("alice", "bob")
                .flatMap(name -> Flux.just(name.toUpperCase(), name.length() + ""))
                .subscribe(System.out::println);   // flatMap merges inner publishers

        Flux.merge(Flux.just(1, 2), Flux.just(3, 4))   // interleaved; order may vary
                .subscribe(System.out::println);

        Flux.zip(Flux.just("a", "b"), Flux.just(1, 2))
                .map(t -> t.getT1() + t.getT2())       // "a1", "b2"
                .subscribe(System.out::println);

        List<Integer> collected = Flux.range(1, 5).collectList().block(); // blocking; tests only
        System.out.println(collected);
    }
}
```

Use `map` for a synchronous one-to-one transform, and `flatMap` when each element leads to another asynchronous call. `flatMap` does not preserve order by default; use `concatMap` if the order matters.

### Annotated controllers

WebFlux supports the same annotations as MVC (`@RestController`, `@GetMapping`, `@RequestBody`). The difference is the return type: return a `Mono` or `Flux` and the framework subscribes to it while writing the response.

```java
import java.net.URI;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

record Account(String id, String owner) { }

interface AccountStore {
    Mono<Account> findById(String id);
    Mono<Account> save(Account account);
    Flux<Account> findAll();
}

@RestController
@RequestMapping("/api/accounts")
class AccountController {

    private final AccountStore store;

    AccountController(AccountStore store) {
        this.store = store;
    }

    @GetMapping("/{id}")
    Mono<ResponseEntity<Account>> get(@PathVariable String id) {
        return store.findById(id)
                .map(ResponseEntity::ok)
                .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    @PostMapping
    Mono<ResponseEntity<Account>> create(@RequestBody Account account) {
        return store.save(account)
                .map(saved -> ResponseEntity
                        .created(URI.create("/api/accounts/" + saved.id()))
                        .body(saved));
    }

    @GetMapping
    Flux<Account> list() {
        return store.findAll();
    }
}
```

Note that `onErrorReturn` takes a value of the element type, so `onErrorReturn(ResponseEntity.notFound().build())` does not fit a `Mono<ResponseEntity<Account>>` stream. Use `defaultIfEmpty` for the empty case and `onErrorResume` for failures.

### Streaming responses

A `Flux` can be sent as Server-Sent Events. Each element becomes one event:

```java
import java.time.Duration;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
class PriceTicker {

    @GetMapping(value = "/api/prices/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    Flux<ServerSentEvent<String>> prices() {
        return Flux.interval(Duration.ofSeconds(1))
                .take(10)
                .map(seq -> ServerSentEvent.<String>builder()
                        .id(String.valueOf(seq))
                        .event("price")
                        .data("103." + seq)
                        .build());
    }
}
```

WebSockets are also supported through the reactive WebSocket API, which exposes a session with inbound and outbound streams. Use it when clients must send data as well as receive it; SSE is simpler when the server is the only sender.

## Reactive data access

Repositories that return `Mono` and `Flux` are available for stores that have a reactive driver. Spring Data offers reactive variants for MongoDB, Cassandra, Redis, and R2DBC.

```java
import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

interface CustomerRepository extends ReactiveCrudRepository<Customer, Long> {
    Mono<Customer> findByEmail(String email);
    Flux<Customer> findByCountry(String country);
}

record Customer(Long id, String email, String country) { }
```

For relational databases, R2DBC is the non-blocking counterpart of JDBC. Add `spring-boot-starter-data-r2dbc` and the driver for your database (for PostgreSQL, the `org.postgresql:r2dbc-postgresql` driver). R2DBC has no lazy-loading or mapping of relationships, so plan queries explicitly.

Reactive MongoDB follows the same shape. The `spring-boot-starter-data-mongodb-reactive` starter gives you `ReactiveMongoRepository`, whose methods return `Mono` and `Flux`, and a `ReactiveMongoTemplate` for queries that need more control. Documents are read as they arrive, so a large result set can be streamed to a client without building the whole list in memory. Writes return a `Mono` that you must subscribe to or return from a handler, or the write never happens. Keep the reactive driver for the whole path; a blocking Mongo call inside a `Flux` pipeline has the same problem as a blocking JDBC call.

## WebClient for outbound calls

`WebClient` is the reactive HTTP client. It returns `Mono` and `Flux` and is the recommended client for WebFlux applications. Spring recommends `RestClient` for blocking code, and `RestTemplate` is in maintenance mode.

```java
import java.time.Duration;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

class CatalogClient {

    private final WebClient client;

    CatalogClient(WebClient.Builder builder) {
        this.client = builder.baseUrl("https://catalog.example.com").build();
    }

    Mono<String> itemName(String id) {
        return client.get()
                .uri("/items/{id}", id)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError,
                          response -> Mono.error(new IllegalArgumentException("unknown item " + id)))
                .bodyToMono(String.class)
                .timeout(Duration.ofSeconds(2));   // fail the stream if the call is slow
    }
}
```

Retries belong on the call, but only for failures that are safe to repeat. Pair `retry` with a backoff (`retryWhen(Retry.backoff(...))`) so that a struggling service is not hammered.

## Error handling operators

| Operator | Effect |
|---|---|
| `onErrorReturn(value)` | Replace an error with a single fallback value |
| `onErrorResume(fn)` | Replace an error with another `Mono` or `Flux` |
| `onErrorMap(fn)` | Translate the exception type |
| `doOnError(...)` | Side effect such as logging; the error still propagates |
| `timeout(duration)` | Signal an error if no element arrives in time |

```java
import java.time.Duration;
import reactor.core.publisher.Mono;

class Fallbacks {
    static Mono<String> priceFor(String sku) {
        return fetchLivePrice(sku)
                .timeout(Duration.ofMillis(500))
                .onErrorResume(ex -> Mono.just("cached"));   // fall back to a cached value
    }

    private static Mono<String> fetchLivePrice(String sku) {
        return Mono.error(new IllegalStateException("provider down"));
    }
}
```

## Testing reactive code

`StepVerifier` (from `reactor-test`) subscribes to a publisher and checks each signal. `WebTestClient` tests a running or mocked WebFlux application over HTTP.

```java
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

class FallbackTest {
    void fallsBackToCache() {
        StepVerifier.create(Fallbacks.priceFor("A-1"))
                .expectNext("cached")
                .verifyComplete();
    }
}
```

`Fallbacks` is the class from the previous section. Use `StepVerifier.withVirtualTime` for operators that depend on time, so the test does not sleep.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.test.web.reactive.server.WebTestClient;

@WebFluxTest(AccountController.class)
class AccountControllerTest {

    @Autowired
    WebTestClient web;

    void unknownAccountIsNotFound() {
        web.get().uri("/api/accounts/missing")
                .exchange()
                .expectStatus().isNotFound();
    }
}
```

The slice test needs a mocked `AccountStore` bean, which you supply with `@MockitoBean` or a test configuration.

## Configuration

WebFlux and Netty are configured in `application.yml` like the rest of Boot. The keys below are the ones you will most often need to tune. Check the property names against the Boot version you run, because they change between releases.

```yaml
spring:
  webflux:
    base-path: /api              # prefix for every handler
  codec:
    max-in-memory-size: 2MB      # cap on a buffered request or response body
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/orders
    username: app
    password: ${DB_PASSWORD}     # supplied by the environment, never committed
    pool:
      initial-size: 5
      max-size: 20               # upper bound on open connections
      max-idle-time: 30m
      max-acquire-time: 5s       # fail fast instead of queueing forever
server:
  netty:
    connection-timeout: 5s       # close connections that stall
```

Three of these settings protect the service. The codec limit stops one large body from filling memory. The pool bound caps database connections, and `max-acquire-time` turns a pool exhaustion into a quick error rather than an unbounded wait. The Netty connection timeout closes stalled connections. Client-side timeouts on `WebClient` calls matter just as much, because a slow outbound call holds its pipeline open until a timeout fires.

There is no property that sets the number of Netty event-loop threads in `spring.webflux`. Netty sizes them from the CPU count, and tuning them is rarely the first fix.

## WebFlux or MVC

| Aspect | Spring MVC | Spring WebFlux |
|---|---|---|
| Server model | Thread per request (blocking) | Few event-loop threads (non-blocking) |
| Typical server | Tomcat | Netty by default |
| Database driver | JDBC, JPA | R2DBC or a reactive driver |
| Code style | Imperative | Declarative operators |
| Debugging | Simple stack traces | Assembly traces needed for context |
| Team fit | Most teams | Teams comfortable with streams |

MVC running on Java 21 virtual threads can also serve many blocking requests. That often removes the main reason to adopt WebFlux, so do not assume WebFlux is faster for every workload. Choose it when you have many concurrent, mostly waiting connections, streaming responses, or a pipeline of reactive dependencies.

## Backpressure

Backpressure lets a subscriber slow a fast producer. Reactor operators for overflow include `onBackpressureBuffer`, `onBackpressureDrop`, and `onBackpressureLatest`. An unbounded buffer only moves the problem into memory, so set a capacity when you use it.

```java
import reactor.core.publisher.BufferOverflowStrategy;
import reactor.core.publisher.Flux;

class Pressure {
    static void demo() {
        Flux.range(1, 1_000_000)
                .onBackpressureBuffer(1_000, BufferOverflowStrategy.ERROR)   // bounded; errors on overflow
                .subscribe(n -> { });
    }
}
```

## How it works / Step by step

1. A request arrives at the Netty event loop, and WebFlux finds the handler method.
2. The handler returns a `Mono` or `Flux` without waiting for the data.
3. The framework subscribes, and each element is written to the response as it arrives.
4. Any `block()` call on an event-loop thread is rejected by Reactor, which raises an `IllegalStateException`. Blocking work must move to a scheduler such as `Schedulers.boundedElastic()`.
5. The pipeline completes or errors, and the connection is closed or reused.

## Common pitfalls

- Calling `block()` inside a request handler, which fails at runtime.
- Using JDBC or a blocking HTTP client inside a `Mono.fromCallable` on the event loop. Wrap it with `subscribeOn(Schedulers.boundedElastic())`.
- Building a `Mono` or `Flux` and never subscribing. The controller subscribes for you, but a fire-and-forget call in a service does nothing without `subscribe()`.
- Using `flatMap` where order matters. Use `concatMap`.
- Trusting `spring.webflux` settings to tune Netty threads. There is no `spring.webflux.thread-pool-size` property; Netty sizes its event loops itself.
- Losing the trace or security context across operators. Use the reactive context and reactive security support instead of thread-locals.
- Choosing WebFlux for a blocking JDBC application, which gains little and adds complexity.

!!! tip "Interview tip"
    **Q: If WebFlux is non-blocking, why not use it everywhere?**
    It only helps when the whole path is non-blocking, from the server to the database and outbound calls. One blocking JDBC call in the chain ties up an event-loop thread, and the reactive code becomes harder to read without a speed-up. On Java 21, virtual threads let blocking MVC code handle many concurrent requests, so the choice is about the workload and team, not a universal rule.

## Quick recap

- `Mono` is zero or one element; `Flux` is zero to many. Nothing runs until subscription.
- Controllers can return `Mono` and `Flux`; `map` and `flatMap` build the pipeline.
- Handle errors with `onErrorResume`, `onErrorReturn`, and `timeout`, and keep fallbacks type-correct.
- Use `WebClient` for outbound calls, `StepVerifier` and `WebTestClient` for tests.
- Never block on an event-loop thread. Choose WebFlux for concurrency and streaming needs, not by default.

**See also:** [Spring Async and Threading](spring-async-and-threading.md) | [HTTP Clients and Testing](http-clients-and-testing.md) | [Exception Handling](exception-handling.md) | [Spring MVC](../08-spring-core/spring-mvc.md)
