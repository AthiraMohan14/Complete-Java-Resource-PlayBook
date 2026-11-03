# Reactive Programming with Spring WebFlux

!!! note "In simple words"
    Reactive code describes what to do when data arrives, instead of waiting for each step. WebFlux serves requests with a few event-loop threads, and returns `Mono` for one value or `Flux` for many values.

## Why it matters

Blocking code ties up a thread for each waiting request. A reactive stack can serve many mostly-waiting connections with few threads, and it handles streams of data with backpressure. Interviewers ask about WebFlux to test whether you know what "non-blocking" actually buys you, when it does not help, and how it differs from Spring MVC.

## How it works

A reactive stream is a publisher that sends values to a subscriber. The subscriber controls how many values it can take, which is called backpressure. Reactor, the library behind WebFlux, implements this with two types. Nothing runs until something subscribes, so a pipeline is a description of work, not the work itself.

When a request arrives, WebFlux runs the following steps. The Spring snippets show the shape of the code; they are not compiled as part of this page.

1. A request arrives on a Netty event-loop thread, and WebFlux finds the handler method.
2. The handler returns a `Mono` or `Flux` immediately, without waiting for the data.
3. The framework subscribes to that publisher, and each element is written to the response as it arrives.
4. Any `block()` call on an event-loop thread is rejected by Reactor with an `IllegalStateException`. Blocking work must move to a scheduler such as `Schedulers.boundedElastic()`.
5. The pipeline completes or fails, and the connection is closed or reused.

```mermaid
sequenceDiagram
    participant Client
    participant Loop as Netty event loop
    participant Handler as Controller
    participant Store as Reactive store
    Client->>Loop: request
    Loop->>Handler: find handler
    Handler-->>Loop: returns Mono
    Loop->>Store: subscribe
    Store-->>Loop: element emitted
    Loop-->>Client: write element
    Store-->>Loop: complete
    Loop-->>Client: response done
```

### Reactive streams in brief

Reactor offers `Mono` and `Flux` as its two types. The example below shows that nothing runs until `subscribe` is called.

```java
import java.time.Duration;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

class ReactorBasics {
    public static void main(String[] args) throws InterruptedException {
        Mono<String> greeting = Mono.just("hello");      // nothing has run yet
        Flux<Integer> numbers = Flux.range(1, 3)
                .map(n -> n * 10);

        greeting.subscribe(System.out::println);         // work starts here
        numbers.subscribe(System.out::println);
        Flux.interval(Duration.ofMillis(100)).take(2)
                .subscribe(System.out::println);
        Thread.sleep(300);                               // keep the JVM alive for the interval demo
    }
}
```

### Four principles behind reactive design

The Reactive Manifesto describes four goals for reactive systems. Naming them helps explain why the style exists:

- **Responsive:** the system answers within a bounded time, even when parts of it are slow or failing.
- **Resilient:** failure is contained in one component and handled by its caller, instead of spreading.
- **Elastic:** the system grows and shrinks with the load, without a fixed ceiling in its design.
- **Message-driven:** components communicate through asynchronous messages or events, so they stay loosely coupled and the sender does not wait.

These are goals, not features. A WebFlux application that calls a blocking database is not elastic, whatever its annotations say.

### Reactive compared with async/await

Both styles avoid waiting on the thread, but they describe the work differently. Async/await is a sequence of steps that look blocking and pause at each `await`. Reactive code describes a pipeline of transformations that runs as data arrives.

| Aspect | Async/await | Reactive (Reactor) |
|---|---|---|
| How you describe work | Sequential steps with `await` between them | A pipeline of operators applied to a stream |
| Number of values | One result per call | Zero or one (`Mono`), or many over time (`Flux`) |
| Backpressure | Not part of the model | Built in. The subscriber controls the rate |
| Error handling | `try` and `catch` around each step | Error signals that operators such as `onErrorResume` handle |
| Cancellation | Depends on the library | Propagates upstream when the subscriber cancels |
| Ease of learning | Familiar to most developers | Steeper, because of the operator vocabulary |
| Best fit | A few concurrent async calls | Streams of events, many concurrent requests, and backpressure |

On Java 21, virtual threads give blocking code much of the scalability that once justified the reactive style. Reactive code still wins for streaming and backpressure. Async/await is simpler for a handful of independent calls.

### Mono and Flux

| Type | Elements | Typical source |
|---|---|---|
| `Mono<T>` | 0 or 1 | One record by id, or a single HTTP response |
| `Flux<T>` | 0 to N | A query result, or a stream of events |

`Mono.empty()` completes without a value, which is different from `null`. Use `switchIfEmpty` or `defaultIfEmpty` to say what should happen in that case.

### Operators you will be asked about

```java
import java.util.List;
import reactor.core.publisher.Flux;

class Operators {
    static void demo() {
        Flux.just(1, 2, 3, 4)
                .filter(n -> n % 2 == 0)     // keeps 2 and 4
                .map(n -> n * 3)             // 6 and 12
                .subscribe(System.out::println);

        Flux.just("alice", "bob")
                .flatMap(name -> Flux.just(name.toUpperCase(), name.length() + ""))
                .subscribe(System.out::println);   // flatMap merges the inner publishers

        Flux.merge(Flux.just(1, 2), Flux.just(3, 4))   // interleaved; the order may vary
                .subscribe(System.out::println);

        Flux.zip(Flux.just("a", "b"), Flux.just(1, 2))
                .map(t -> t.getT1() + t.getT2())       // "a1" and "b2"
                .subscribe(System.out::println);

        List<Integer> collected = Flux.range(1, 5).collectList().block(); // blocking; for tests only
        System.out.println(collected);
    }
}
```

Use `map` for a synchronous one-to-one transform. Use `flatMap` when each element leads to another asynchronous call. `flatMap` does not keep order by default, so use `concatMap` when order matters.

### Annotated controllers

WebFlux supports the same annotations as MVC, such as `@RestController`, `@GetMapping`, and `@RequestBody`. The difference is the return type. Return a `Mono` or `Flux`, and the framework subscribes to it while it writes the response.

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

`onErrorReturn` takes a value of the element type, so `onErrorReturn(ResponseEntity.notFound().build())` does not fit a `Mono<ResponseEntity<Account>>` stream. Use `defaultIfEmpty` for the empty case, and `onErrorResume` for failures.

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

WebSockets are also supported through the reactive WebSocket API. A session has inbound and outbound streams. Use WebSockets when clients must send data as well as receive it. Server-Sent Events are simpler when the server is the only sender.

## Reactive data access

Repositories that return `Mono` and `Flux` exist for stores with a reactive driver. Spring Data offers reactive variants for MongoDB, Cassandra, Redis, and R2DBC.

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

For relational databases, R2DBC is the non-blocking counterpart of JDBC. Add `spring-boot-starter-data-r2dbc` and the driver for your database. For PostgreSQL, that is the `org.postgresql:r2dbc-postgresql` driver. R2DBC does not map relationships or lazy-load them, so write the queries explicitly.

Reactive MongoDB follows the same shape. The `spring-boot-starter-data-mongodb-reactive` starter gives you `ReactiveMongoRepository`, whose methods return `Mono` and `Flux`, and `ReactiveMongoTemplate` for queries that need more control. Documents arrive one at a time, so a large result set can stream to a client without being held in memory. A write returns a `Mono`, and nothing is written until you subscribe to it or return it from a handler. Keep the reactive driver for the whole path. A blocking Mongo call inside a `Flux` pipeline has the same problem as a blocking JDBC call.

## WebClient for outbound calls

`WebClient` is the reactive HTTP client. It returns `Mono` and `Flux`, and it is the recommended client for WebFlux applications. For blocking code, Spring recommends `RestClient`, and `RestTemplate` is in maintenance mode.

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

Retries belong on the call, but only for failures that are safe to repeat. Pair `retry` with a backoff, using `retryWhen(Retry.backoff(...))`, so that a struggling service is not hammered.

## Error handling operators

| Operator | Effect |
|---|---|
| `onErrorReturn(value)` | Replace an error with one fallback value |
| `onErrorResume(fn)` | Replace an error with another `Mono` or `Flux` |
| `onErrorMap(fn)` | Translate the exception type |
| `doOnError(...)` | A side effect such as logging. The error still propagates |
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

`StepVerifier`, from `reactor-test`, subscribes to a publisher and checks each signal. `WebTestClient` tests a WebFlux application over HTTP.

```java
import reactor.test.StepVerifier;

class FallbackTest {
    void fallsBackToCache() {
        StepVerifier.create(Fallbacks.priceFor("A-1"))
                .expectNext("cached")
                .verifyComplete();
    }
}
```

`Fallbacks` is the class from the previous section. Use `StepVerifier.withVirtualTime` for operators that depend on time, so the test does not need to sleep.

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

WebFlux and Netty are configured in `application.yml`, like the rest of Boot. The keys below are the ones you most often need to tune. Check the property names against your Boot version, because they change between releases.

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

Three of these settings protect the service. The codec limit stops one large body from filling memory. The pool bound caps database connections, and `max-acquire-time` turns pool exhaustion into a quick error rather than an unbounded wait. The Netty connection timeout closes stalled connections. Client-side timeouts on `WebClient` calls matter just as much, because a slow outbound call holds its pipeline open until a timeout fires.

There is no property under `spring.webflux` that sets the number of Netty event-loop threads. Netty sizes them from the CPU count, and tuning them is rarely the first fix.

## WebFlux or MVC

| Aspect | Spring MVC | Spring WebFlux |
|---|---|---|
| Server model | One thread per request (blocking) | A few event-loop threads (non-blocking) |
| Typical server | Tomcat | Netty by default |
| Database driver | JDBC or JPA | R2DBC or another reactive driver |
| Code style | Imperative | Declarative operators |
| Debugging | Simple stack traces | Assembly traces are needed for context |
| Team fit | Most teams | Teams comfortable with streams |

MVC on Java 21 virtual threads can also serve many blocking requests. That often removes the main reason to adopt WebFlux, so do not assume WebFlux is faster for every workload. Choose it for many concurrent, mostly waiting connections, streaming responses, or a pipeline of reactive dependencies.

## Backpressure

Backpressure lets a subscriber slow a fast producer. Reactor offers overflow operators such as `onBackpressureBuffer`, `onBackpressureDrop`, and `onBackpressureLatest`. An unbounded buffer only moves the problem into memory, so set a capacity whenever you buffer.

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

## Where it is used

- **Streaming APIs:** Server-Sent Events for live prices, progress, or notifications.
- **Fan-out gateways:** a service that calls several reactive backends and merges the results.
- **High-concurrency edges:** many open connections that mostly wait on I/O.
- **Reactive data stores:** MongoDB, Redis, or R2DBC pipelines end to end.

## Benefits

- A small number of threads can serve many waiting connections.
- Backpressure protects the subscriber from being flooded.
- Operators express timeouts, fallbacks, and merges in a compact way.
- Streaming responses use little memory.

## Cons and limits

- The benefit only exists when the whole path is non-blocking. One blocking call on an event-loop thread removes it.
- The operator vocabulary is steep for most teams.
- Stack traces are harder to read, because the work runs in many small steps.
- On Java 21, virtual threads let blocking MVC code handle many requests, which narrows the gap.

## Best practices

- Never call `block()` inside a request handler or on an event-loop thread.
- Move blocking work onto `Schedulers.boundedElastic()` with `subscribeOn`.
- Subscribe to every `Mono` and `Flux` you create, or return it to a caller that does.
- Use `concatMap` when order matters, and `flatMap` when it does not.
- Set timeouts on every outbound call, and bound every buffer.
- Carry trace and security context through the reactive context, not through thread-locals.
- Choose WebFlux for concurrency and streaming needs, not by default.

!!! tip "Interview tip"
    **Q: If WebFlux is non-blocking, why not use it everywhere?**
    It helps only when the whole path is non-blocking, from the server through to the database and outbound calls. One blocking JDBC call in the chain ties up an event-loop thread, and the reactive code becomes harder to read without a speed-up. On Java 21, virtual threads let blocking MVC code handle many concurrent requests, so the choice depends on the workload and the team, not on a universal rule.

## Quick recap

- `Mono` is zero or one element. `Flux` is zero to many. Nothing runs until something subscribes.
- Controllers can return `Mono` and `Flux`. `map` and `flatMap` build the pipeline.
- Handle errors with `onErrorResume`, `onErrorReturn`, and `timeout`. Keep fallbacks the right type.
- Use `WebClient` for outbound calls. Use `StepVerifier` and `WebTestClient` for tests.
- Never block on an event-loop thread. Choose WebFlux for concurrency and streaming needs.

## Official documentation

- [Spring Framework reference](https://docs.spring.io/spring-framework/reference/)
- [Spring Boot reference](https://docs.spring.io/spring-boot/reference/index.html)
- [Spring Data JPA reference](https://docs.spring.io/spring-data/jpa/reference/index.html)

**See also:** [Spring Async and Threading](spring-async-and-threading.md) | [HTTP Clients and Testing](http-clients-and-testing.md) | [Exception Handling](exception-handling.md) | [Spring MVC](../08-spring-core/spring-mvc.md)
