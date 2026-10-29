# Unit Testing with JUnit 5

A unit test checks one piece of logic in isolation, runs in milliseconds, and fails for one clear reason. JUnit 5 (Jupiter) is the standard framework for this in Java. Interviewers ask about it to see whether you can structure tests well: clear names, one behaviour per test, and no hidden dependencies between tests.

## Core concepts

### The basic test and lifecycle

A test is a method annotated with `@Test`. JUnit creates a new test-class instance for each test method by default, which keeps tests independent. Lifecycle annotations run setup and cleanup around the tests.

| Annotation | When it runs |
|---|---|
| `@BeforeAll` | Once before all tests in the class (must be `static`, unless the lifecycle is per-class) |
| `@BeforeEach` | Before each test |
| `@AfterEach` | After each test |
| `@AfterAll` | Once after all tests (must be `static`, unless the lifecycle is per-class) |

```java
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class PriceCalculatorTest {

    private PriceCalculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new PriceCalculator();
    }

    @AfterEach
    void tearDown() {
        calculator = null;
    }

    @Test
    @DisplayName("applies a 10% discount to totals over 100")
    void appliesDiscountAboveThreshold() {
        assertEquals(135, calculator.discounted(150));
    }
}
```

The `PriceCalculator` class under test is assumed to have `int discounted(int total)`, returning the total after a 10% discount when the total is over 100.

### Parameterised tests

`@ParameterizedTest` runs one test with many inputs. Add the `junit-jupiter-params` artefact to use it.

```java
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class DiscountRuleTest {

    @ParameterizedTest(name = "total {0} costs {1}")
    @CsvSource({"50, 50", "100, 100", "101, 90", "150, 135"})
    void discountRule(int total, int expected) {
        assertEquals(expected, new PriceCalculator().discounted(total));
    }
}
```

Other sources include `@ValueSource`, `@EnumSource`, and `@MethodSource` for richer arguments.

### Dynamic tests

`@TestFactory` produces tests at runtime, which suits data-driven cases that are loaded from elsewhere. It returns a stream of `DynamicTest` objects.

```java
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

class DynamicDiscountTest {

    @TestFactory
    Stream<DynamicTest> discountCases() {
        return Stream.of(50, 100, 150).map(total ->
                DynamicTest.dynamicTest("total " + total, () -> {
                    int result = new PriceCalculator().discounted(total);
                    org.junit.jupiter.api.Assertions.assertTrue(result <= total);
                }));
    }
}
```

Prefer `@ParameterizedTest` for fixed inputs. Use dynamic tests when the cases are only known at runtime.

### Assertions

JUnit's `Assertions` class covers most needs. `assertAll` groups several checks so you see every failure, `assertThrows` checks an exception, and `assertTimeout` bounds a duration.

```java
import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

class AssertionExamples {

    @Test
    void groupedChecks() {
        String name = "order-42";
        assertAll(
                () -> assertTrue(name.startsWith("order")),
                () -> assertEquals(8, name.length()),
                () -> assertNotNull(name)
        );
    }

    @Test
    void exceptionCheck() {
        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> { throw new IllegalArgumentException("quantity must be positive"); });
        assertEquals("quantity must be positive", ex.getMessage());
    }
}
```

AssertJ offers fluent assertions that read like sentences and give better failure messages for collections and objects. Many teams prefer it:

```java
import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;

class AssertJExamples {

    @Test
    void fluentAssertions() {
        List<String> items = List.of("book", "pen");
        assertThat(items).hasSize(2).contains("pen").doesNotContain("cup");
    }
}
```

### Nested tests and extra injection

`@Nested` groups related tests inside an outer class, which makes the output readable. `TestInfo` and `TestReporter` are parameters JUnit injects; `TestInfo` gives the test's name and tags, and `TestReporter` publishes extra information to the test report.

```java
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.TestReporter;

class CartTest {

    @Nested
    class WhenEmpty {
        @Test
        void totalIsZero(TestInfo info, TestReporter reporter) {
            reporter.publishEntry("running", info.getDisplayName());
            assertEquals(0, new Cart().total());
        }
    }
}

class Cart {
    int total() { return 0; }
}
```

Temporary files are another common need. `@TempDir` gives each test a fresh directory that JUnit deletes afterwards.

```java
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ExportTest {

    @TempDir
    Path tempDir;

    @Test
    void writesFile() throws Exception {
        Path file = tempDir.resolve("export.csv");
        Files.writeString(file, "id,total\n1,100\n");
        assertTrue(Files.exists(file));
    }
}
```

## How it works / Step by step

1. Surefire (Maven) or Gradle discovers test classes and methods.
2. For each test method, JUnit creates an instance, runs `@BeforeEach` methods, runs the test, then runs `@AfterEach` methods.
3. Assertions throw on failure; the test reports the first failure, unless you used `assertAll`.
4. Results are reported, and a failed build stops the pipeline.

## Common pitfalls

- Tests that depend on each other's order or on shared static state.
- Testing many behaviours in one method, so a failure does not say which one broke.
- Vague names such as `test1`. Name tests for behaviour, for example `appliesDiscountAboveThreshold`.
- Sleeping in tests to wait for something. Use explicit waits, latches, or `assertTimeout`.
- Using `assertEquals` with floating-point numbers without a tolerance, or with `BigDecimal` values that differ only in scale.
- Testing private methods directly. Test through the public behaviour.

!!! tip "Interview tip"
    **Q: What makes a good unit test?**
    It is fast, isolated, deterministic, and has a clear name that states the behaviour. It uses the public interface, checks one behaviour, and fails for one reason. Fixtures are built in the test or in `@BeforeEach`, not shared through static state.

## Quick recap

- JUnit 5 uses `@Test` with `@BeforeEach` and `@AfterEach` for per-test setup.
- `@ParameterizedTest` covers many inputs; `@TestFactory` covers runtime-generated cases.
- `assertAll`, `assertThrows`, and AssertJ make failures clearer.
- `@Nested` organises related behaviour; `@TempDir` handles files safely.
- Keep tests independent, deterministic, and focused on public behaviour.

**See also:** [Mocking with Mockito](mockito.md) | [Integration Testing](integration-testing.md) | [API Testing and Code Coverage](api-testing-and-coverage.md)
