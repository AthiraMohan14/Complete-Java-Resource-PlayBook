# Unit Testing with JUnit 5

!!! note "In simple words"
    A unit test exercises one small piece of logic by itself. It finishes in milliseconds and, when it fails, points to one specific problem. JUnit 5 is the Java framework most teams use to write them.

## Why it matters

Unit tests are the cheapest bug detector you have. They run on every save, so a mistake surfaces while the code is still fresh in your mind. A well-named test also documents intent, telling a newcomer what the code is supposed to do. Interviewers check unit tests for structure: clear names, one behaviour per test, no ordering between tests, and a sound rule about what deserves a direct test.

## How it works

JUnit follows a fixed sequence for every test. Knowing it explains why tests must not share state.

1. The build tool, Maven Surefire or the Gradle test task, finds test classes and methods on the test classpath.
2. For each `@Test` method, JUnit builds a brand-new instance of the test class, so a field changed in one test cannot leak into the next.
3. The `@BeforeEach` methods run, then the test body, then the `@AfterEach` methods.
4. A failed assertion throws `AssertionFailedError`. Unless the test uses `assertAll`, the first failure ends it.
5. Outcomes are written to the build report, and any failure fails the build and the pipeline.

The flowchart below shows the life of a single test.

```mermaid
flowchart LR
    A[Fresh test instance] --> B[BeforeEach setup]
    B --> C[Test body and assertions]
    C --> D[AfterEach cleanup]
    D --> E[Outcome in build report]
```

### The sample class under test

Every example on this page uses one small class, so each snippet stands alone.

```java
package com.example.pricing;

public class PriceCalculator {

    // Totals above 100 get a 10 percent discount. Everything else is charged in full.
    public int discounted(int total) {
        return total > 100 ? total - total / 10 : total;
    }
}
```

### The basic test and lifecycle

A test is any method annotated with `@Test`. Lifecycle annotations perform setup and teardown around each test or each class.

| Annotation | When it runs |
|---|---|
| `@BeforeAll` | Once, before the class's tests. The method must be `static` under the default lifecycle |
| `@BeforeEach` | Before every test |
| `@AfterEach` | After every test |
| `@AfterAll` | Once, after the class's tests. The method must be `static` under the default lifecycle |

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
    @DisplayName("applies a 10 percent discount to totals over 100")
    void appliesDiscountAboveThreshold() {
        assertEquals(135, calculator.discounted(150));
    }
}
```

### Parameterised tests

`@ParameterizedTest` runs a single test body against a table of inputs. It needs the `junit-jupiter-params` artefact.

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

Other argument sources include `@ValueSource` for lone values, `@EnumSource` for enum constants, and `@MethodSource` for objects that are clumsy to write inline.

### Dynamic tests

`@TestFactory` produces tests while the suite runs. The method returns a stream or collection of `DynamicTest` objects. It suits cases that only become known at run time, such as rows read from a file.

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

When the inputs are fixed in source, `@ParameterizedTest` is the better fit. Save dynamic tests for cases the test code cannot know ahead of time.

### Assertions

`Assertions` covers most needs:

- `assertAll` runs several checks and reports every failure, not just the first.
- `assertThrows` confirms that a block throws the given exception, and returns it for more checks.
- `assertTimeout` fails when a block runs longer than the supplied `Duration`.

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

AssertJ offers a fluent alternative whose failure messages are clearer for collections and objects. It needs the `assertj-core` artefact.

*AssertJ example (library code, not compiled here).*

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

`@Nested` puts related tests inside an inner class, so the report reads like a specification. JUnit can also inject a `TestInfo`, which exposes the current test's name and tags, and a `TestReporter`, which adds key-value details to the report. You receive both as method parameters.

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

For code that writes files, `@TempDir` supplies a clean directory to each test, and JUnit removes it afterwards.

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

A unit test should go through a class's public contract. Private methods are internal. Callers never see them, and a refactor that preserves public behaviour should leave the tests green.

If you catch yourself wanting to test a private method, one of three things is usually true:

- The method is dead code, or its behaviour cannot be reached from the public API.
- The logic is complicated enough to earn its own class, which you can then test directly.
- The method should not be private, for instance package-private, so tests in the same package can reach it.

Improve the design first. If the logic deserves its own tests, extract it into a class with a public method.

When direct access is unavoidable, two options exist:

1. **A test in the same package.** It reaches package-private, protected, and public members, and IDEs place test classes in matching packages by default. It cannot reach `private` members, a frequent misconception.
2. **Reflection, for `private` members.** Fetch the method with `getDeclaredMethod`, call `setAccessible(true)`, and invoke it. The method stays private, but renaming it or changing its parameters breaks the test at run time instead of compile time. Use this rarely.

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

## Where it is used

- Pricing, tax, and discount rules that must return exact figures.
- Parsers and validators that accept many input shapes.
- State machines, where every transition deserves a check.
- Utility classes that much other code relies on.

## Benefits

- A unit test finishes in milliseconds, so it can run on every save.
- A failure names one behaviour, which makes diagnosis fast.
- Parameterised tests cover a large input table with little code.
- Descriptive names turn the suite into readable documentation.

## Cons and limits

- A unit test isolates one class, so it cannot show that the parts cooperate.
- Heavy reflection or same-package testing can make refactoring harder.
- Testing trivial getters and setters adds upkeep without much value.
- Tests written after the code tend to mirror the implementation rather than the requirement.
- A suite without assertions always passes and proves nothing.

### Common pitfalls

- Tests that rely on execution order, or on static state another test changed.
- A single test method checking several behaviours, so a failure does not say which one broke.
- Vague names such as `test1`. Name each test after the behaviour it checks.
- Calling `Thread.sleep` to wait. Use latches, polling with a timeout, or `assertTimeout`.
- Comparing doubles with `assertEquals` and no tolerance. Also note that `new BigDecimal("1.0")` does not equal `new BigDecimal("1.00")`, because the scales differ.
- Reaching for reflection on `private` methods by default. Test the public behaviour first.
- Importing JUnit 4 types such as `org.junit.Assert` or `org.junit.Test` into a JUnit 5 project. The annotations and assertions live in different packages.

## Best practices

- Name each test after the behaviour it verifies, for example "method, condition, expected result".
- Check one behaviour per test, and use `assertAll` when several facts describe one behaviour.
- Build fixtures inside the test or in `@BeforeEach`, and avoid shared mutable static fixtures.
- Use `@ParameterizedTest` for a table of cases, and `@TestFactory` only for cases generated at run time.
- Test through the public interface, and extract any logic that needs its own tests.
- Keep tests deterministic: no real clock, no unseeded randomness, and no network calls.

!!! tip "Interview tip"
    **Q: What makes a good unit test?**
    A good unit test runs quickly, stands alone, gives the same answer every time, and has a name that tells you the behaviour it guards. It calls the public surface, asserts one behaviour, and has only one reason to fail. Build its inputs locally, not in shared static state. Collaborators that need replacing are discussed in [Mockito](mockito.md).

## Quick recap

- `@Test` marks a case; `@BeforeEach` and `@AfterEach` wrap it, and JUnit gives every case a fresh instance.
- `@ParameterizedTest` drives a fixed table, while `@TestFactory` builds cases on the fly.
- `assertAll`, `assertThrows`, and AssertJ make failure output easier to read.
- `@Nested` organises related cases, and `@TempDir` hands out disposable folders.
- Reach private logic through public methods first; use same-package access next, and reflection only as a last resort.

## Official documentation

- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Java 21 API Documentation](https://docs.oracle.com/en/java/javase/21/docs/api/index.html)
- [Java Language Specification, Java SE 21](https://docs.oracle.com/javase/specs/jls/se21/html/index.html)
- [Maven Guides](https://maven.apache.org/guides/)

**See also:** [Mocking with Mockito](mockito.md) | [Integration Testing](integration-testing.md) | [API Testing and Code Coverage](api-testing-and-coverage.md)
