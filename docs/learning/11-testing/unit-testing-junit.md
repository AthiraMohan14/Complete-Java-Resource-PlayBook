# Unit Testing with JUnit 5

A unit test checks one piece of logic in isolation, runs in milliseconds, and fails for one clear reason. JUnit 5 (Jupiter) is the standard Java framework for this. Interviewers ask about it to see whether you can structure tests well: descriptive names, one behaviour per test, no hidden ordering between tests, and a sensible rule for what to test directly.

## Core concepts

### The sample class under test

The examples on this page use one small class so the snippets stay self-contained.

```java
package com.example.pricing;

public class PriceCalculator {

    // Totals above 100 get a 10% discount; everything else is charged in full.
    public int discounted(int total) {
        return total > 100 ? total - total / 10 : total;
    }
}
```

### The basic test and lifecycle

A test is a method annotated with `@Test`. JUnit creates a new instance of the test class for each test method, so fields set in one test do not leak into another. Lifecycle annotations run setup and cleanup around the tests.

| Annotation | When it runs |
|---|---|
| `@BeforeAll` | Once before all tests in the class (method must be `static` with the default per-method lifecycle) |
| `@BeforeEach` | Before each test |
| `@AfterEach` | After each test |
| `@AfterAll` | Once after all tests (method must be `static` with the default lifecycle) |

```java
package com.example.pricing;

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

### Parameterised tests

`@ParameterizedTest` runs one test body against many inputs. It needs the `junit-jupiter-params` artifact on the test classpath.

```java
package com.example.pricing;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class DiscountRuleTest {

    @ParameterizedTest(name = "total {0} is charged {1}")
    @CsvSource({"50, 50", "100, 100", "101, 91", "150, 135"})
    void discountRule(int total, int expected) {
        assertEquals(expected, new PriceCalculator().discounted(total));
    }
}
```

Other argument sources include `@ValueSource` for single values, `@EnumSource` for enum constants, and `@MethodSource` for objects that are awkward to write inline.

### Dynamic tests

`@TestFactory` builds tests at runtime. The method returns a `Stream` (or collection) of `DynamicTest` objects. This suits cases that are only known when the test runs, such as data read from a file.

```java
package com.example.pricing;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

class DynamicDiscountTest {

    @TestFactory
    Stream<DynamicTest> discountNeverIncreasesTotal() {
        return Stream.of(50, 100, 150, 400)
                .map(total -> DynamicTest.dynamicTest("total " + total, () -> {
                    int charged = new PriceCalculator().discounted(total);
                    assertTrue(charged <= total);
                }));
    }
}
```

Prefer `@ParameterizedTest` when the inputs are fixed in the source code. Reach for dynamic tests only when the cases come from somewhere the test cannot know in advance.

### Assertions

The `Assertions` class covers most needs.

- `assertAll` runs several checks and reports every failure, not just the first.
- `assertThrows` checks that a block throws a given exception and returns it for further checks.
- `assertTimeout` fails if a block takes longer than a given `Duration`.

```java
package com.example.orders;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class AssertionExamples {

    @Test
    void groupedChecks() {
        String reference = "order-42";
        assertAll(
                () -> assertTrue(reference.startsWith("order")),
                () -> assertEquals(8, reference.length()),
                () -> assertNotNull(reference)
        );
    }

    @Test
    void exceptionIsThrownWithMessage() {
        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> { throw new IllegalArgumentException("quantity must be positive"); });
        assertEquals("quantity must be positive", ex.getMessage());
    }
}
```

AssertJ is a popular alternative. Its fluent style reads like a sentence and gives clearer failure messages for collections and objects. It needs the `assertj-core` artifact.

```java
package com.example.orders;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;

class AssertJExamples {

    @Test
    void fluentCollectionChecks() {
        List<String> items = List.of("book", "pen");
        assertThat(items).hasSize(2).contains("pen").doesNotContain("cup");
    }
}
```

### Nested tests and injected parameters

`@Nested` groups related tests in an inner class, which makes reports read like a specification. JUnit can also inject `TestInfo` (name and tags of the current test) and `TestReporter` (publishes extra key-value data into the report) as method parameters.

```java
package com.example.cart;

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
            reporter.publishEntry("test", info.getDisplayName());
            assertEquals(0, new Cart().total());
        }
    }
}

class Cart {
    int total() {
        return 0;
    }
}
```

For file-based code, `@TempDir` gives each test a fresh directory that JUnit deletes afterwards. You do not have to clean up by hand.

```java
package com.example.io;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ExportTest {

    @TempDir
    Path tempDir;

    @Test
    void writesCsvFile() throws Exception {
        Path file = tempDir.resolve("export.csv");
        Files.writeString(file, "id,total\n1,100\n");
        assertTrue(Files.exists(file));
    }
}
```

### Testing private methods

A useful rule: unit tests should exercise the public contract of a class. Private methods are implementation details. Callers cannot see them, and a refactor that keeps the public behaviour should not break tests.

When you feel the urge to test a private method, it usually signals one of three things:

- The private method is dead code, or its behaviour is not reachable from the public API.
- The private method is complex enough to deserve its own class, which you can then test directly.
- The method should not be private in the first place, for example package-private, so that the package's own tests can reach it.

Fix the design first. If the logic is worth testing on its own, extract it.

When you do need direct access, there are two options.

1. **Same-package test (package-private methods only).** Put the test class in the same package as the class under test. This is the standard approach, and IDEs create test classes in the matching package by default. It works for package-private, protected, and public members. It does not reach `private` members, which is a common misconception.
2. **Reflection (for `private` methods).** Look up the method with `getDeclaredMethod`, call `setAccessible(true)`, and invoke it. This keeps the method `private`, but tests become brittle: renaming the method or changing its parameters breaks the test at runtime, not at compile time. Use it sparingly.

```java
package com.example.pricing;

public class Discounts {

    public int apply(int total) {
        return isEligible(total) ? total - total / 10 : total;
    }

    private boolean isEligible(int total) {
        return total > 100;
    }
}
```

A reflection-based test for the private helper:

```java
package com.example.pricing;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.lang.reflect.Method;
import org.junit.jupiter.api.Test;

class DiscountsReflectionTest {

    @Test
    void isEligibleIsTrueAboveThreshold() throws Exception {
        Discounts discounts = new Discounts();
        Method isEligible = Discounts.class.getDeclaredMethod("isEligible", int.class);
        isEligible.setAccessible(true);

        boolean result = (Boolean) isEligible.invoke(discounts, 150);

        assertTrue(result);
    }
}
```

## How it works / Step by step

1. Maven Surefire or Gradle's test task scans the test classpath for test classes and methods.
2. For each `@Test` method, JUnit creates a fresh instance of the test class, runs the `@BeforeEach` methods, runs the test, then runs the `@AfterEach` methods.
3. An assertion that fails throws an `AssertionFailedError`. Without `assertAll`, the first failure ends that test.
4. Results go to the build report, and a failing test fails the build and the pipeline.

## Common pitfalls

- Tests that depend on execution order or on static state changed by another test.
- One test method checking several behaviours, so a failure does not say which one broke.
- Vague names such as `test1`. Name tests after the behaviour they check.
- Calling `Thread.sleep` to wait for something. Use latches, `Awaitility`-style polling, or `assertTimeout`.
- Comparing doubles with `assertEquals` and no tolerance, or comparing `BigDecimal` values that differ only in scale. `new BigDecimal("1.0")` and `new BigDecimal("1.00")` are not `equals`.
- Writing a test that calls `private` methods through reflection by default. Test through the public behaviour first.
- Using JUnit 4 imports (`org.junit.Assert`, `org.junit.Test`) in a JUnit 5 project. The annotations and assertion class are different packages.

!!! tip "Interview tip"
    **Q: What makes a good unit test?**
    It is fast, isolated, deterministic, and has a name that states the behaviour. It exercises the public interface, checks one behaviour, and fails for one reason. Fixtures are built inside the test or in `@BeforeEach`, never through shared static state. For mocking collaborators, see [Mockito](mockito.md).

## Quick recap

- JUnit 5 uses `@Test` with `@BeforeEach` and `@AfterEach` for per-test setup. Each test gets a new instance.
- `@ParameterizedTest` covers many fixed inputs; `@TestFactory` generates tests at runtime.
- `assertAll`, `assertThrows`, and AssertJ make failures clearer.
- `@Nested` groups related behaviour; `@TempDir` gives safe temporary files.
- Test private logic through the public API. Use same-package tests for package-private members and reflection only as a last resort.

**See also:** [Mocking with Mockito](mockito.md) | [Integration Testing](integration-testing.md) | [API Testing and Code Coverage](api-testing-and-coverage.md)
