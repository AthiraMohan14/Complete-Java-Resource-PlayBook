# HTTP Clients and Testing in Spring Boot

Spring Boot applications call other services and must be tested at several levels. For HTTP clients, the questions are about timeouts, retries, and which client to choose. For testing, the questions are about test scope: which parts of the context to load, what to mock, and when to use a real database. Interviewers ask these to see whether you can keep tests fast without losing confidence.

## Core concepts

### Choosing an HTTP client

| Client | Model | Status |
|---|---|---|
| `RestTemplate` | Blocking | Maintenance mode; know it, do not start new code with it |
| `RestClient` | Blocking, fluent API | Recommended for synchronous calls (Spring Framework 6.1 and later) |
| `WebClient` | Reactive, non-blocking | Recommended for reactive stacks or high fan-out |
| OpenFeign | Declarative interface | Good when you want client interfaces generated from annotations |

### RestClient

`RestClient` offers a fluent API over the same HTTP infrastructure. Set the base URL and timeouts once on the builder.

```java
import java.net.http.HttpClient;
import java.time.Duration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

record PaymentStatus(String id, String state) {}

class PaymentApi {
    private final RestClient client;

    PaymentApi() {
        HttpClient http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(2))
                .build();
        this.client = RestClient.builder()
                .baseUrl("https://payments.example.com")
                .requestFactory(new JdkClientHttpRequestFactory(http))
                .build();
    }

    PaymentStatus status(String id) {
        return client.get()
                .uri("/payments/{id}", id)
                .retrieve()
                .body(PaymentStatus.class);
    }
}
```

Set a read timeout as well as a connect timeout. Without them, a stuck remote call holds a thread indefinitely. Check the request-factory API for your Spring version, since timeout configuration differs between factories.

### WebClient

`WebClient` returns reactive types (`Mono` and `Flux`) and does not block the calling thread.

```java
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

class ReactivePaymentApi {
    private final WebClient web = WebClient.builder()
            .baseUrl("https://payments.example.com")
            .build();

    Mono<PaymentStatus> status(String id) {
        return web.get()
                .uri("/payments/{id}", id)
                .retrieve()
                .bodyToMono(PaymentStatus.class);
    }
}

record PaymentStatus(String id, String state) {}
```

Nothing happens until someone subscribes to the `Mono`. Returning it without subscribing is a common mistake.

### Declarative clients with OpenFeign

With `spring-cloud-starter-openfeign` and `@EnableFeignClients`, you declare an interface and Spring generates the implementation.

```java
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(name = "payments", url = "https://payments.example.com")
interface PaymentFeignClient {
    @GetMapping("/payments/{id}")
    PaymentStatus status(@PathVariable("id") String id);
}

record PaymentStatus(String id, String state) {}
```

Feign is a Spring Cloud component, so it fits naturally in service-to-service setups. See [Spring Cloud](../14-microservices/spring-cloud.md).

### Timeouts, retries, and error handling

Three rules cover most cases:

1. Always set timeouts. A call with no timeout can hang forever.
2. Retry only idempotent operations, or operations protected by an idempotency key. Retrying a non-idempotent `POST` can double-charge a customer.
3. Use exponential backoff with a cap, and a maximum number of attempts, so retries do not amplify an outage.

Spring Retry provides declarative retries:

```java
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;

@Service
class StatusService {

    @Retryable(retryFor = ResourceAccessException.class, maxAttempts = 3,
            backoff = @Backoff(delay = 200, multiplier = 2))
    PaymentStatus fetch(String id) {
        // call the remote service here
        throw new ResourceAccessException("simulated timeout");
    }

    @Recover
    PaymentStatus fallback(ResourceAccessException ex, String id) {
        return new PaymentStatus(id, "UNKNOWN");
    }
}

record PaymentStatus(String id, String state) {}
```

`@Retryable` requires `@EnableRetry` on a configuration class. Recovery methods must have the same return type and the exception as their first parameter. Resilience4j offers more options for production (circuit breakers, bulkheads); see [Resilience Patterns](../14-microservices/resilience-patterns.md).

## Testing

### Test scope

Start with the narrowest test that proves the behaviour, and move up only when needed.

| Annotation | Loads | Use for |
|---|---|---|
| none (plain JUnit) | Nothing | Pure logic |
| `@WebMvcTest(Controller.class)` | Web layer for one controller | Request mapping, validation, status codes |
| `@DataJpaTest` | JPA repositories and an embedded database by default | Queries and mappings |
| `@RestClientTest(Client.class)` | One REST client plus a mock server | Outbound HTTP calls |
| `@SpringBootTest` | Full application context | End-to-end wiring |

### Slice tests with MockMvc

```java
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(OrderApiController.class)
class OrderApiControllerTest {

    @Autowired MockMvc mvc;
    @MockitoBean OrderService orders;

    @Test
    void returnsOrder() throws Exception {
        when(orders.describe(1L)).thenReturn("book");

        mvc.perform(get("/api/orders/1"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$").exists());
    }
}

interface OrderService {
    String describe(long id);
}
```

`OrderApiController` here is the controller from the Actuator page, updated to inject `OrderService`. `@MockBean` was deprecated in Spring Boot 3.4 and removed in Spring Boot 4.0. Current projects use `@MockitoBean` from `org.springframework.test.context.bean.override.mockito`, as shown above. Older code still uses `@MockBean`.

### Client tests with MockRestServiceServer

`@RestClientTest` configures a mock server for your REST client, so you can test serialisation and URLs without a network call.

```java
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;

@RestClientTest(PaymentApi.class)
class PaymentApiTest {

    @Autowired PaymentApi api;
    @Autowired MockRestServiceServer server;

    void readsStatus() {
        server.expect(requestTo("https://payments.example.com/payments/p1"))
              .andRespond(withSuccess("{\"id\":\"p1\",\"state\":\"PAID\"}", MediaType.APPLICATION_JSON));

        // assert on api.status("p1") here
    }
}
```

`PaymentApi` is the client from the RestClient example. It needs to be a Spring bean and built from the auto-configured builder for the mock server to intercept its calls, so this sketch shows the approach rather than a drop-in test.

### Full context tests and real dependencies

`@SpringBootTest` loads everything. Use it for a few end-to-end checks, not for every case, because context startup is slow. Spring caches contexts between tests with the same configuration, so keep configuration changes to a minimum.

For databases, an embedded database such as H2 is fast but not identical to production. Testcontainers starts a real database in Docker for the duration of the test, and with `@ServiceConnection` (Spring Boot 3.1 and later) Spring wires the connection automatically. See [Integration Testing](../11-testing/integration-testing.md).

## Common pitfalls

- Creating a new `RestTemplate` or `RestClient` per request. Build the client once and reuse it.
- Default timeouts in libraries that are effectively infinite.
- Retrying on every exception, including validation errors that will never succeed.
- Using `@SpringBootTest` for every test, which makes the suite slow.
- Mocking the repository in a `@DataJpaTest`, which skips the query you need to test.
- Relying on H2 behaviour for SQL that only works in H2.
- Forgetting that `WebClient` is lazy and never subscribing.

!!! tip "Interview tip"
    **Q: How would you test a controller without starting the whole application?**
    Use `@WebMvcTest` with `MockMvc`. It loads only the web layer and the named controller, and you mock its collaborators with `@MockitoBean` (the older `@MockBean` was removed in Spring Boot 4.0). Keep the full `@SpringBootTest` for a small number of end-to-end checks, so the suite stays fast.

## Quick recap

- Choose `RestClient` for synchronous calls, `WebClient` for reactive ones, and know `RestTemplate` is in maintenance mode.
- Always set timeouts; retry only idempotent operations, with backoff and a cap.
- Pick the narrowest test slice that proves the behaviour.
- Use `MockMvc` for controllers and `MockRestServiceServer` for clients.
- Use Testcontainers when you need a real database.

**See also:** [Integration Testing](../11-testing/integration-testing.md) | [Resilience Patterns](../14-microservices/resilience-patterns.md) | [Building REST APIs](rest-apis.md)
