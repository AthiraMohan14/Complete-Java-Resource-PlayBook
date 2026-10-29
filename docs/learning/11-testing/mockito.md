# Mocking with Mockito

Mockito creates test doubles: objects that stand in for collaborators so you can test one class at a time. You stub what a dependency returns, then verify how your code used it. Interviewers ask about Mockito to check whether you know when mocking helps and when it hides design problems, such as over-mocked tests that pass while the real integration breaks.

## Core concepts

### Setting up Mockito with JUnit 5

Use `@ExtendWith(MockitoExtension.class)` to initialise `@Mock`, `@Spy`, `@InjectMocks`, and `@Captor` fields for each test. The extension also enables strict stubbing, which fails a test when a stub is never used.

```java
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock PaymentGateway gateway;
    @Mock OrderRepository repository;
    @InjectMocks OrderService service;

    @Test
    void chargesCustomerAndSavesOrder() {
        when(gateway.charge(anyString(), anyInt())).thenReturn(true);

        service.place("customer-1", 500);

        verify(repository).save(any(Order.class));
    }
}
```

The types here are assumed: `OrderService` takes the gateway and repository in its constructor, `OrderRepository.save(Order)` returns `void` in this sketch, and `Order` is a record.

### Stubbing

`when(...).thenReturn(...)` sets what a call returns. `thenThrow` simulates failure, and `thenAnswer` computes a result from the arguments.

```java
import static org.mockito.Mockito.when;

when(gateway.charge("customer-1", 500)).thenReturn(true);
when(gateway.charge("customer-2", 500)).thenThrow(new IllegalStateException("gateway down"));
when(repository.count()).thenAnswer(invocation -> 3L);
```

Use argument matchers (`any()`, `anyString()`, `eq()`, `argThat()`) when arguments are not known in advance. Do not mix raw values and matchers in the same call; if one argument is a matcher, all of them must be.

### Verification

`verify` checks that an interaction happened. Use `times`, `never`, `atLeastOnce`, and `inOrder` to be specific.

```java
import static org.mockito.Mockito.*;

verify(gateway, times(1)).charge("customer-1", 500);
verify(repository, never()).delete(any());

InOrder order = inOrder(gateway, repository);
order.verify(gateway).charge(anyString(), anyInt());
order.verify(repository).save(any());
```

Verify interactions that matter to the behaviour, such as sending a payment or writing a record. Avoid verifying every internal call, because that ties the test to the implementation.

### Argument captors

An `ArgumentCaptor` captures the object passed into a mock, so you can assert on its state.

```java
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

record Order(String customerId, int amount, String status) {}

class CaptorExample {

    @Test
    void savesPaidOrder() {
        OrderRepository repository = mock(OrderRepository.class);
        OrderService service = new OrderService(mock(PaymentGateway.class), repository);
        ArgumentCaptor<Order> orderCaptor = ArgumentCaptor.forClass(Order.class);

        service.place("customer-1", 500);

        verify(repository).save(orderCaptor.capture());
        assertEquals("PAID", orderCaptor.getValue().status());
    }
}
```

With `MockitoExtension`, you can declare the captor as a field with `@Captor` instead. Without the extension, as above, create it with `ArgumentCaptor.forClass(Order.class)`; a `@Captor` field stays `null` in that case.

### Mocks, spies, and real objects

| Kind | Behaviour | Use when |
|---|---|---|
| Mock | All methods stubbed to return defaults unless you stub them | You need to replace a dependency entirely |
| Spy | Real methods run, and you can override some | You need the real behaviour but want to observe or change one call |
| Real object | Your actual code | The logic is simple and has no external effects |

A spy is created with `@Spy` or `Mockito.spy(object)`. Spies are useful for legacy code but usually point to a design that could separate concerns better.

```java
import static org.mockito.Mockito.*;

import java.util.ArrayList;
import java.util.List;

class SpyExample {
    void demo() {
        List<String> list = spy(new ArrayList<String>());
        list.add("book");
        verify(list).add("book");
    }
}
```

### Mock what you do not own

Mock types you do not control: a payment provider's client, a clock, an HTTP library. Do not mock simple value objects, records, or utility classes. If a test needs to mock five collaborators to exercise one method, the class probably has too many responsibilities.

Mockito 5 uses the inline mock maker by default, so `final` classes and static methods can be mocked in some cases with `Mockito.mockStatic`. Use that sparingly; static mocks make tests fragile.

## How it works / Step by step

1. `@Mock` creates a proxy object that records calls and returns configured answers.
2. `when(...).thenReturn(...)` stubs a call. With strict stubs, an unused stub fails the test.
3. The code under test runs and calls the mock.
4. `verify` checks the recorded calls against your expectations.

## Common pitfalls

- Over-mocking: every collaborator mocked, so the test passes while the real components break.
- Verifying private implementation details, which breaks on every refactor.
- Stubbing values the code never uses. Strict stubs flag this as `UnnecessaryStubbingException`, which is a useful signal to remove the stub.
- Mixing matchers and raw values in one call.
- Mocking JPA entities or records, which hides the behaviour you want to test.
- Using `@InjectMocks` on a class with constructor arguments that are not mocked, which leaves them `null`.

!!! tip "Interview tip"
    **Q: When would you not use a mock?**
    When the collaborator is cheap, deterministic, and has no side effects, use the real object. For persistence, use a real database in an integration test, because a mocked repository cannot reveal bad queries or mapping errors. Mocks are best for replacing external or slow dependencies.

## Quick recap

- Use `MockitoExtension` with `@Mock`, `@InjectMocks`, and `@Captor`.
- `when/thenReturn` stubs; `verify` checks important interactions.
- Argument captors inspect objects passed to collaborators.
- Prefer real objects for simple logic; spies are a legacy tool.
- Mock only what you do not own, and keep the number of mocks small.

**See also:** [Unit Testing with JUnit 5](unit-testing-junit.md) | [Integration Testing](integration-testing.md) | [Spring Boot Testing](../09-spring-boot/http-clients-and-testing.md)
