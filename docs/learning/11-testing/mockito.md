# Mocking with Mockito

Mockito creates test doubles: objects that stand in for collaborators so you can test one class at a time. You stub what a dependency returns, then verify how your code used it. Interviewers ask about Mockito to see whether you know when a mock helps and when it hides a problem, such as an over-mocked test that passes while the real integration is broken.

## Core concepts

### The example under test

The snippets on this page share one small service. The production types are shown once here so every example compiles against them.

```java
package com.example.orders;

interface PaymentGateway {
    boolean charge(String customerId, int amount);
}

interface OrderRepository {
    void save(Order order);
}

record Order(String customerId, int amount, String status) {}

class OrderService {

    private final PaymentGateway gateway;
    private final OrderRepository repository;

    OrderService(PaymentGateway gateway, OrderRepository repository) {
        this.gateway = gateway;
        this.repository = repository;
    }

    void place(String customerId, int amount) {
        String status = gateway.charge(customerId, amount) ? "PAID" : "DECLINED";
        repository.save(new Order(customerId, amount, status));
    }
}
```

### Setting up Mockito with JUnit 5

Annotate the test class with `@ExtendWith(MockitoExtension.class)`. The extension initialises `@Mock`, `@Spy`, `@InjectMocks`, and `@Captor` fields before each test. It also turns on strict stubbing, so a stub that a test never uses fails the test. This needs the `mockito-junit-jupiter` artifact.

`@InjectMocks` builds the class under test and passes in the mocks through its constructor.

```java
package com.example.orders;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    PaymentGateway gateway;

    @Mock
    OrderRepository repository;

    @InjectMocks
    OrderService service;

    @Test
    void savesPaidOrderWhenChargeSucceeds() {
        when(gateway.charge("customer-1", 500)).thenReturn(true);

        service.place("customer-1", 500);

        ArgumentCaptor<Order> captor = ArgumentCaptor.forClass(Order.class);
        verify(repository).save(captor.capture());
        assertEquals("PAID", captor.getValue().status());
    }

    @Test
    void savesDeclinedOrderWhenChargeFails() {
        when(gateway.charge(anyString(), anyInt())).thenReturn(false);

        service.place("customer-2", 80);

        verify(repository).save(new Order("customer-2", 80, "DECLINED"));
    }

    @Test
    void gatewayFailureSavesNothing() {
        when(gateway.charge(anyString(), anyInt()))
                .thenThrow(new IllegalStateException("gateway down"));

        assertThrows(IllegalStateException.class, () -> service.place("customer-3", 10));

        verify(repository, never()).save(any());
    }
}
```

### Stubbing

`when(...).thenReturn(...)` sets what a call returns. Related options:

- `thenThrow(...)` makes the call throw.
- `thenAnswer(...)` computes the result from the call's arguments.
- For `void` methods, use `doThrow(...).when(mock).method(...)`, because `when(...)` cannot wrap a `void` call.

```java
package com.example.orders;

import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class StubbingExamples {

    void demo() {
        PaymentGateway gateway = mock(PaymentGateway.class);
        OrderRepository repository = mock(OrderRepository.class);

        when(gateway.charge("customer-1", 500)).thenReturn(true);
        when(gateway.charge("customer-2", 500)).thenAnswer(
                invocation -> invocation.<String>getArgument(0).startsWith("vip"));
        doThrow(new IllegalStateException("disk full")).when(repository).save(org.mockito.ArgumentMatchers.any());
    }
}
```

### Argument matchers

When you do not know the exact argument in advance, use a matcher such as `any()`, `anyString()`, `anyInt()`, `eq(...)`, or `argThat(...)`. There is one rule to remember: if any argument in a call uses a matcher, every argument in that call must use a matcher. Mix them and Mockito throws an `InvalidUseOfMatchersException`. Wrap a literal with `eq(...)` to fix this.

```java
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

class GatewayStubbing {

    interface PaymentGateway {
        boolean charge(String account, int cents);
    }

    PaymentGateway gateway;   // a mock in a real test

    void stub() {
        // Correct: every argument is a matcher.
        when(gateway.charge(anyString(), eq(500))).thenReturn(true);

        // Wrong: mixes a matcher with a raw value and will fail at runtime.
        // when(gateway.charge(anyString(), 500)).thenReturn(true);
    }
}
```

### Verification

`verify` asserts that an interaction happened. Add `times`, `never`, `atLeastOnce`, or `atMost` to make the count explicit. `InOrder` checks the sequence across several mocks.

```java
package com.example.orders;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import org.mockito.InOrder;

class VerificationExamples {

    void demo() {
        PaymentGateway gateway = mock(PaymentGateway.class);
        OrderRepository repository = mock(OrderRepository.class);
        OrderService service = new OrderService(gateway, repository);

        service.place("customer-1", 500);

        verify(gateway, times(1)).charge("customer-1", 500);
        verify(repository, atLeastOnce()).save(any());

        InOrder order = inOrder(gateway, repository);
        order.verify(gateway).charge(anyString(), anyInt());
        order.verify(repository).save(any());
    }
}
```

Verify the interactions that define the behaviour, such as charging a card or writing a record. Avoid verifying every internal call. That ties the test to the current implementation and makes refactoring expensive.

### Argument captors

An `ArgumentCaptor` records the object a mock received, so you can inspect its fields. This is useful when the object is built inside the code under test and you cannot easily predict it. The `OrderServiceTest` example above uses one. Outside the extension you create it with `ArgumentCaptor.forClass(...)`. A `@Captor` field is initialised only when `MockitoExtension` is in use.

### Mocks, spies, and real objects

| Kind | Behaviour | Use when |
|---|---|---|
| Mock | Every method returns a default value unless stubbed | You need to replace a dependency completely |
| Spy | Real methods run; you can stub or observe some calls | You need real behaviour but want to watch one call |
| Real object | Your actual code | The logic is simple and has no external effects |

```java
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.verify;

import java.util.ArrayList;
import java.util.List;

class SpyExample {

    void demo() {
        List<String> items = spy(new ArrayList<String>());
        items.add("book");
        verify(items).add("book");
    }
}
```

Spies are useful when wrapping legacy code you cannot change yet. If you reach for them often, the class probably mixes responsibilities that should be separated.

### What to mock

Mock the things you do not control: a payment provider's client, an HTTP client, the system clock. Avoid mocking simple value objects, records, and utility methods. Use the real thing.

Mockito 5 uses the inline mock maker by default, which allows mocking `final` classes. Static methods can be mocked with `Mockito.mockStatic(...)` inside a try-with-resources block. Use this rarely, because static mocks couple tests to global state.

## How it works / Step by step

1. `@Mock` (or `mock(...)`) creates a proxy that records every call and returns configured answers.
2. `when(...).thenReturn(...)` registers a stub for a specific call.
3. The code under test runs and calls the mock.
4. `verify` checks the recorded calls against your expectations. With strict stubs, a stub that was never used fails the test with `UnnecessaryStubbingException`.

## Common pitfalls

- Over-mocking. When every collaborator is mocked, the test passes while the real components would fail together.
- Verifying private details or every internal call, which breaks on each refactor.
- Leaving unused stubs in place. Strict stubs flag them, which is a useful signal to delete them.
- Mixing matchers and raw values in the same call.
- Mocking records or simple value objects, which hides behaviour you actually want to test.
- Using `@InjectMocks` with a constructor argument that has no matching mock. Mockito passes `null` for it, and the code fails later with a `NullPointerException`.
- Relying on mocks to test persistence. A mocked repository cannot reveal bad queries or mapping errors; use a real database in an integration test.

!!! tip "Interview tip"
    **Q: When would you not use a mock?**
    When the collaborator is cheap, deterministic, and free of side effects, use the real object. For persistence, prefer a real database in an integration test, because a mock cannot show that a query or mapping works. Mocks fit best for external services and slow or non-deterministic dependencies. For the test structure around them, see [Unit Testing with JUnit 5](unit-testing-junit.md).

## Quick recap

- Use `@ExtendWith(MockitoExtension.class)` with `@Mock`, `@InjectMocks`, and `@Captor`.
- `when(...).thenReturn(...)` stubs a call; `verify` checks the interactions that matter.
- Matchers must cover every argument in a call; wrap literals with `eq(...)`.
- Argument captors let you inspect objects passed to collaborators.
- Prefer real objects for simple logic. Keep mocks to external dependencies.

**See also:** [Unit Testing with JUnit 5](unit-testing-junit.md) | [Integration Testing](integration-testing.md) | [API Testing and Code Coverage](api-testing-and-coverage.md)
