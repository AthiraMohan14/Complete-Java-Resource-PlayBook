# Java Code Review Guidelines

A review checklist for Java code, grouped into ten areas: naming and constants, method design, exceptions, null handling, collections and streams, formatting, performance, Spring usage, miscellaneous hygiene, and enum design. Each rule has a short before and after example. Treat the rules as defaults. A team can override any of them, but should do so on purpose.

---

## 1. Variables and Constants

### Make fields final by default

A field that is never reassigned should be `final`. This documents intent, prevents accidental reassignment, and makes the object easier to reason about when several threads read it.

```java
public class Greeter {
    private final String greeting = "Hello";  // never reassigned
    private String lastName;                  // changed by a setter, so not final

    public void setLastName(String name) {
        this.lastName = name;
    }
}
```

### Keep shared constants in one place

Literal values repeated across classes drift apart over time. Put shared values in a constants class with a private constructor so it cannot be instantiated.

```java
public class StatusChecks {
    // Bad: the same literal in several places
    boolean isFlagged(String flag, String otherFlag) {
        if ("Y".equals(flag)) { return true; }
        return "Y".equals(otherFlag);
    }
}

// Good: one definition
public final class StatusCodes {
    public static final String YES = "Y";
    public static final String NO = "N";

    private StatusCodes() { }
}
```

### Reuse separators and keys

Separators used to build cache keys or log lines should be constants, so that changing one format does not require a search through the code.

```java
public class CacheKeys {
    private static final String SEPARATOR = "---";

    static String key(String tenantId, String userId, String resourceId) {
        String key = String.join(SEPARATOR, tenantId, userId, resourceId);
        return key;
    }
}
```

### Use enums for fixed sets of values

A `String` can hold any value, so typos compile and fail only at runtime. An enum limits the values to the ones that are valid.

```java
public class MessageStatusExample {
    // Bad
    void bad() {
        String status = "PASSED";
    }

    // Good
    enum MessageStatus { PASSED, FAILED, ERROR, WARNING, INFO }

    void good() {
        MessageStatus status = MessageStatus.PASSED;
    }
}
```

### Name things clearly

Avoid single-letter names outside short loops. Prefer names that say what the value means. Very long names are also a problem, because they make lines hard to read. Shorten the name, not the meaning.

```java
// Bad
String y = "Y";
int n = 5;

// Good
String status = "Y";
int maxRetries = 5;
```

### Boolean methods read as questions

Boolean-returning methods should start with `is` or `has`, so that a call reads as a question.

```java
import java.util.EnumSet;
import java.util.Set;

public class Account {
    private boolean valid;
    private final Set<Permission> permissions = EnumSet.of(Permission.READ);

    public boolean isValid() { return valid; }
    public boolean hasPermission() { return permissions.contains(Permission.WRITE); }
}

enum Permission { READ, WRITE }
```

### Getters always return a value

A getter should have a defined result for every state of the object. If `null` is a legal state, decide what the getter returns and document it. Do not let a branch fall through without a return statement.

```java
public class Person {
    private String name;

    public String getName() {
        return name == null ? "" : name;  // the empty-string rule is explicit
    }
}
```

---

## 2. Method Design

### One method, one job

A method that validates, transforms, and saves is three methods. Splitting it makes each part testable on its own and gives each part a name that explains what it does.

```java
public class OrderProcessor {
    record Order(String id) { }

    // Bad
    public void processAndValidateAndLog(Order order) {
        // validation, transformation, and logging all in one body
    }

    // Good
    public void process(Order order) {
        validate(order);
        save(transform(order));
        log(order);
    }

    void validate(Order order) { }
    Order transform(Order order) { return order; }
    void save(Order order) { }
    void log(Order order) { }
}
```

### Keep parameter lists short

Methods with many parameters are hard to call correctly, because arguments of the same type are easy to swap. Group related values into one object when the list grows past about five or six.

```java
public class UserService {
    // Bad: eight strings in a row
    void createUser(String id, String name, String email, String phone,
                    String address, String city, String state, String zip) { }

    // Good
    record UserRequest(String id, String name, String email, String phone,
                       String address, String city, String state, String zip) { }

    void createUser(UserRequest request) { }
}
```

Put heavy or large parameters, such as a big map, a large collection, or a bulky configuration object, last in the list. The short identifying arguments then come first and read as the main subject of the call, and the bulky argument is easy to spot at the end. This is a readability convention. Java passes object references, so the position of an argument does not change its runtime cost.

```java
import java.util.Map;

public class Dispatcher {
    // Good: the identifiers come first, the payload last
    void process(String id, int priority, Map<String, Object> payload) { }
}
```

### Keep methods short

A method that runs to hundreds of lines usually mixes several steps. A common limit is 50 to 70 statements. When a method goes past that, extract the steps into named private methods. The top-level method then reads like a list of steps.

### Prefer guard clauses to nested branches

Guard clauses return early for invalid input, so the main logic is not buried in nested `if` blocks. This is usually clearer than one long boolean expression.

```java
static boolean isUsable(String value) {
    if (value == null) return false;
    if (value.isBlank()) return false;
    return value.length() <= 255;
}
```

A single return statement is not a rule. Use it when it makes the method easier to read.

### Keep the return expression simple

A `return` line that contains a long stream pipeline is hard to debug. Assign intermediate results to named variables, then return the final one.

```java
import java.util.List;
import java.util.Objects;

public class NameFilter {
    List<String> activeNames(List<String> names) {
        List<String> active = names.stream()
                .filter(Objects::nonNull)
                .map(String::trim)
                .sorted()
                .toList();
        return active;
    }
}
```

---

## 3. Exception Handling

### Declare exceptions instead of swallowing them

If a method cannot handle a failure, let it propagate with a `throws` clause. Catching `Exception` and logging it inside a low-level method hides the failure from the caller, who may be able to recover.

```java
// Bad: the caller never learns the call failed
public void processRequest() {
    try {
        loadRecords();
    } catch (Exception e) {
        LOGGER.error("failed", e);
    }
}

// Good: the caller decides
public void processRequest() throws IOException {
    loadRecords();
}
```

### Throw specific exceptions

A generic `Exception` tells the caller nothing. Define or use an exception type that names the problem, and include a message that says what was wrong.

```java
public class CustomerValidationException extends RuntimeException {
    public CustomerValidationException(String message) {
        super(message);
    }
}

class CustomerValidator {
    void reject() {
        throw new CustomerValidationException("Customer ID must not be blank");
    }
}
```

### Name exception-throwing helpers clearly

If a helper method's only job is to throw, its name should say so. A team convention such as `throwValidationException()` makes that obvious at the call site. Apply the convention only if the team agrees on it.

### Log with context, not just the exception

A stack trace without context is hard to act on. Include the identifiers involved and the message, and pass the exception as the last argument so the stack trace is still logged. SLF4J treats a trailing `Throwable` argument as the exception.

The block below is pseudo-code: `LOGGER.error(exception)` has no SLF4J overload that takes a single `Throwable`.

```text
// Bad: no context, or the whole object printed as text
LOGGER.error("Error");
LOGGER.error(exception);

// Good
LOGGER.error("Failed to process customer {}", customerId, exception);
```

### Suppress unchecked warnings narrowly

`@SuppressWarnings("unchecked")` hides warnings for every line in the scope it covers. Put it on the smallest declaration that needs it, and add a comment that explains why the cast is safe.

```java
import java.util.List;

public class CacheReader {
    void readItems(Object cachedValue) {
        @SuppressWarnings("unchecked")
        List<String> items = (List<String>) cachedValue;  // written only by this class as a List<String>
    }
}
```

### Handle the default case in a switch

An unexpected value should be visible. Either log it at an error level or throw. For an enum, a switch expression with an exhaustive set of cases makes the compiler check the coverage.

```java
public class OrderRouter {
    enum Type { ORDER, REFUND }

    void route(Type type) {
        switch (type) {
            case ORDER -> handleOrder();
            case REFUND -> handleRefund();
            default -> throw new IllegalArgumentException("Unexpected type: " + type);
        }
    }

    void handleOrder() { }
    void handleRefund() { }
}
```

---

## 4. Null and Empty Checks

### Use `Objects.nonNull` for clarity

`Objects.nonNull(x)` reads more clearly than `x != null` in a filter or a condition, and it can be passed as a method reference.

```java
import java.util.Objects;

public class OrderHandler {
    record Order(String id) { }

    void handle(Order order) {
        if (Objects.nonNull(order)) {
            process(order);
        }
    }

    void process(Order order) { }
}
```

### Avoid double negatives

Negating a method whose name is already negative is hard to read. Call the positive form instead.

```java
// Bad
if (!StringUtils.isNotBlank(value)) { ... }

// Good
if (StringUtils.isBlank(value)) { ... }
```

### Do not repeat null checks a helper already performs

Many utility methods are null-safe. Calling a null check first adds noise. `NumberUtils.isParsable` from Apache Commons Lang returns `false` for `null`, so an extra check is redundant.

```java
// Bad
if (value != null && NumberUtils.isParsable(value)) { ... }

// Good
if (NumberUtils.isParsable(value)) { ... }
```

### Trust non-null guarantees, but verify them

If the database schema or the framework guarantees a value is present, a check on it is noise. If the guarantee does not exist, the check stays. Write a short comment where the contract is not obvious.

### Use the null-safe collection helpers

`org.springframework.util.CollectionUtils.isEmpty` handles `null` and empty collections in one call. It does not have an `isNotEmpty` counterpart, so negate the call with `!`.

```java
// Bad
if (list != null && !list.isEmpty()) { ... }

// Good
if (!CollectionUtils.isEmpty(list)) { ... }
```

### Check several strings at once

`StringUtils.isAllEmpty` from Apache Commons Lang checks a group of values in one expression, which is clearer than chaining `isEmpty` checks with `&&`.

```java
if (StringUtils.isAllEmpty(state, abbrev, code)) { ... }
```

### Trim safely

Calling `trim()` on `null` throws `NullPointerException`. `StringUtils.trimToEmpty` returns an empty string for `null` and trims otherwise.

```java
String trimmed = StringUtils.trimToEmpty(value);
```

---

## 5. Collections and Streams

### Prefer streams for transformations

A loop that builds a new list from another list is often clearer as a stream. Use a loop when the body has side effects or needs early exit that a stream does not express well.

```java
import java.util.ArrayList;
import java.util.List;

public class UpperCaser {
    // Bad
    List<String> upperBad(List<String> words) {
        List<String> upper = new ArrayList<>();
        for (String word : words) {
            upper.add(word.toUpperCase());
        }
        return upper;
    }

    // Good
    List<String> upperGood(List<String> words) {
        List<String> upper = words.stream()
                .map(String::toUpperCase)
                .toList();
        return upper;
    }
}
```

`Stream.toList()` returns an unmodifiable list and is available from Java 16. Before Java 16, use `Collectors.toList()`.

### Name complex predicates

A long filter condition is easier to read and test when it is a named `Predicate`.

```java
import java.time.LocalDate;
import java.util.List;
import java.util.function.Predicate;

public class OrderFilter {
    record Order(String type, String status, LocalDate date) { }

    static final Predicate<Order> IS_ACTIVE_TYPE_A =
            o -> "A".equals(o.type()) && "ACTIVE".equals(o.status());

    List<Order> activeOrders(List<Order> orders) {
        List<Order> result = orders.stream()
                .filter(IS_ACTIVE_TYPE_A)
                .toList();
        return result;
    }
}
```

### Use `collect` for accumulation, not `reduce` with strings

Concatenating strings with `reduce` creates a new string at every step, which is quadratic in the total length. `Collectors.joining` uses a builder internally.

```java
import java.util.List;
import java.util.stream.Collectors;

public class WordJoiner {
    // Bad
    String joinBad(List<String> words) {
        String result = words.stream().reduce("", (a, b) -> a + b);
        return result;
    }

    // Good
    String joinGood(List<String> words) {
        String result = words.stream().collect(Collectors.joining());
        return result;
    }
}
```

### Use `IntStream` for numeric ranges

`IntStream.rangeClosed` states the bounds directly, so there is no hand-written list of numbers to keep in sync.

```java
import java.util.List;
import java.util.stream.IntStream;

public class Months {
    List<Integer> months() {
        List<Integer> months = IntStream.rangeClosed(1, 12)
                .boxed()
                .toList();
        return months;
    }
}
```

### Use `List.of` for fixed lists

`List.of` creates an immutable list and rejects `null` elements. If the caller needs to add items later, wrap the result in a new `ArrayList`.

```java
import java.util.ArrayList;
import java.util.List;

public class FixedLists {
    void demo() {
        List<String> fixed = List.of("a", "b", "c");
        List<String> mutable = new ArrayList<>(List.of("a", "b", "c"));
    }
}
```

### Use pattern matching for `instanceof` (Java 16+)

Pattern matching removes the separate cast and the variable that duplicates the type.

```java
public class ResponseHandler {
    record OrderResponse(String id) { }

    void process(OrderResponse orderResponse) { }

    // Bad
    void handleBad(Object response) {
        if (response instanceof OrderResponse) {
            OrderResponse orderResponse = (OrderResponse) response;
            process(orderResponse);
        }
    }

    // Good
    void handleGood(Object response) {
        if (response instanceof OrderResponse orderResponse) {
            process(orderResponse);
        }
    }
}
```

---

## 6. Code Formatting and Style

### Brace placement

Put the opening brace on the same line as the statement and the closing brace on its own line. This is the common style in the Google Java Style Guide and most IDE defaults.

```java
public class BraceStyle {
    void doSomething() { }

    void run(boolean condition) {
        if (condition) {
            doSomething();
        }
    }
}
```

### Always use braces

A single-statement `if` without braces is one edit away from a bug. A later edit adds a line that looks like it belongs to the `if` but does not.

```java
public class BracesExample {
    void doSomething() { }

    // Bad
    void runBad(boolean condition) {
        if (condition) doSomething();
    }

    // Good
    void runGood(boolean condition) {
        if (condition) {
            doSomething();
        }
    }
}
```

### Limit nesting to three levels

Deep nesting makes the flow of a method hard to follow. Invert a condition and return early to flatten it.

```java
public class NestingExample {
    void action() { }

    // Bad: five levels deep
    void runBad(boolean a, boolean b, boolean c, boolean d, boolean e) {
        if (a) {
            if (b) {
                if (c) {
                    if (d) {
                        if (e) {
                            action();
                        }
                    }
                }
            }
        }
    }

    // Good: guard clause
    void runGood(boolean a, boolean b, boolean c, boolean d, boolean e) {
        if (!(a && b && c && d && e)) {
            return;
        }
        action();
    }
}
```

### Prefer early returns to else blocks

When one branch is a short exit, return from it and keep the main path unindented.

```java
public class EarlyReturn {
    void doA() { }
    void doB() { }

    void run(boolean condition) {
        if (!condition) {
            doB();
            return;
        }
        doA();
    }
}
```

### Separate logical groups with blank lines

A blank line between groups of related statements tells the reader where one step ends and the next begins.

```java
public class RequestSteps {
    static class Request {
        String getName() { return ""; }
        int getAge() { return 0; }
    }

    void validate(String name, int age) { }
    void save(Request request) { }

    void handle(Request request) {
        String name = request.getName();
        int age = request.getAge();

        validate(name, age);
        save(request);
    }
}
```

### Parenthesize mixed conditions

`&&` binds tighter than `||`. Adding parentheses makes the intended grouping visible without reading the precedence table.

```java
if (StringUtils.isNotBlank(time)
        && (EventType.TYPE_975.equals(type) || EventType.TYPE_976.equals(type))) {
    // ...
}
```

### Put the null check first

In `a || b`, the right side runs only when the left side is false. Check for `null` on the left, so a method call on the right never receives a `null` receiver.

```java
public class NullFirst {
    // Bad: NullPointerException when obj is null
    boolean emptyBad(String obj) {
        if (obj.isEmpty() || obj == null) { return true; }
        return false;
    }

    // Good
    boolean emptyGood(String obj) {
        if (obj == null || obj.isEmpty()) { return true; }
        return false;
    }
}
```

### Prefer a set lookup to a chain of equals

A chain of `equals` calls repeats the same variable many times. A `Set` lookup is shorter and checks the value once. Use `Set.of`, which rejects `null` for the lookup argument, so check for `null` first if the input can be null.

```java
import java.util.Set;

public class YesValues {
    private static final Set<String> YES_VALUES = Set.of("Y", "YES", "1");

    boolean isYes(String status) {
        return status != null && YES_VALUES.contains(status);
    }
}
```

A regular expression such as `status.matches("Y|YES|1")` also works. It is harder to read and compiles a pattern on each call unless the pattern is precompiled.

---

## 7. Performance

### Batch calls to remote systems

Each call to a database, a cache, or another service has a fixed cost. Ask the service for several items in one call when its API allows it.

```java
import java.util.List;
import java.util.Map;

public class BatchFetch {
    static class Data { }

    Data fetch(String table, String key) { return new Data(); }
    Map<String, Data> fetchAll(List<String> tables, String key) { return Map.of(); }

    void load(String key) {
        // Bad: three round trips
        Data d1 = fetch("TABLE_A", key);
        Data d2 = fetch("TABLE_B", key);
        Data d3 = fetch("TABLE_C", key);

        // Good: one round trip
        Map<String, Data> all = fetchAll(List.of("TABLE_A", "TABLE_B", "TABLE_C"), key);
    }
}
```

### Filter in the query, not in Java

Loading every row and filtering in memory wastes network time and memory. Put the condition in the `WHERE` clause or the repository query.

```java
import java.util.List;

public class OrderQueries {
    static class Order {
        String getStatus() { return ""; }
    }

    interface OrderRepository {
        List<Order> findAll();
        List<Order> findByStatus(String status);
    }

    // Bad: loads everything, then filters
    List<Order> loadActiveInMemory(OrderRepository repository) {
        List<Order> active = repository.findAll().stream()
                .filter(o -> "ACTIVE".equals(o.getStatus()))
                .toList();
        return active;
    }

    // Good: the database filters
    List<Order> loadActiveInQuery(OrderRepository repository) {
        List<Order> active = repository.findByStatus("ACTIVE");
        return active;
    }
}
```

### Build strings with a builder inside loops

Repeated `+=` on a `String` creates a new object on each pass. Use a `StringBuilder` for the loop, or `String.join` when the parts already exist as a collection.

```java
import java.util.List;

public class ItemBuilder {
    String build(List<String> items, String separator) {
        StringBuilder result = new StringBuilder();
        for (String item : items) {
            result.append(item).append(separator);
        }
        return result.toString();
    }
}
```

### Reuse existing utilities

A hand-written join loop duplicates what `String.join` already does. Reuse the library method so there is one implementation to test.

```java
public class KeyBuilder {
    String key(String param1, String param2, String param3) {
        String key = String.join("|", param1, param2, param3);
        return key;
    }
}
```

### Avoid assigning a value and then overwriting it

Creating an object and reassigning it on the next line means the first object was wasted work, and the reader has to track which value is current.

```java
public class AmountExample {
    static class Amount { }

    static Amount format(Amount amount) { return amount; }

    // Bad
    void bad() {
        Amount amount = new Amount();
        amount = format(amount);
    }

    // Good
    void good() {
        Amount amount = format(new Amount());
    }
}
```

### Use `var` when the type is obvious

`var` removes repeated type names when the right side makes the type clear, such as a constructor call or a well-named factory method. Avoid `var` when a reader must look up the return type to understand the code.

```java
import java.util.List;

public class CustomerTotals {
    interface CustomerRepository { List<String> findAll(); }
    static class Order { }

    static long calculateTotal(Order order) { return 0L; }

    void report(CustomerRepository repository, Order order) {
        var customers = repository.findAll();   // the name and the method make the type clear
        var total = calculateTotal(order);      // hard to tell without reading calculateTotal
    }
}
```

---

## 8. Spring and Framework Usage

### Let Spring create helper classes

A helper class that Spring manages can receive its own dependencies, be replaced in tests, and share a lifecycle with the application. Annotate it with `@Component` and inject it rather than calling `new`.

```java
@Component
public class ComparatorHelper {
    // collaborators are injected, not created here
}

@Service
public class ReportService {
    private final ComparatorHelper comparator;

    public ReportService(ComparatorHelper comparator) {
        this.comparator = comparator;
    }
}
```

Constructor injection, as shown, is preferred over field injection with `@Autowired`. It makes missing dependencies a compile-time or startup error, and it allows the class to be built in a unit test without Spring.

### Use `@PostConstruct` for work that needs injected fields

Work that needs injected dependencies belongs in a `@PostConstruct` method, which runs after injection. In Spring Boot 3 the annotation comes from `jakarta.annotation`, not `javax.annotation`.

```java
import jakarta.annotation.PostConstruct;

@Component
public class SegmentCatalog {
    private final SegmentRepository repository;
    private List<String> segments = List.of();

    public SegmentCatalog(SegmentRepository repository) {
        this.repository = repository;
    }

    @PostConstruct
    void loadSegments() {
        this.segments = repository.loadSegmentNames();
    }
}
```

### Do not set a value that a base method already sets

If a factory method already sets a field, setting it again in the caller is redundant and invites a mismatch if one of the two changes later.

```java
public class RequestFactory {
    static class Request {
        void setId(String id) { }
    }

    static Request createBaseRequest() { return new Request(); }

    // Bad
    Request badBuild(String id) {
        Request request = createBaseRequest();
        request.setId(id);  // createBaseRequest() already sets the id
        return request;
    }

    // Good
    Request goodBuild() {
        Request request = createBaseRequest();
        return request;
    }
}
```

---

## 9. Miscellaneous

### Retire deprecated code

Deprecated code should be removed once no caller uses it. While callers are still migrating, mark the method with `@Deprecated(since = "...", forRemoval = true)` and point to the replacement in the Javadoc. This makes the migration visible to the compiler and to other developers.

```java
public class Legacy {
    /** @deprecated use {@link #newMethod()} instead. */
    @Deprecated(since = "2.0", forRemoval = true)
    public void oldMethod() { }

    public void newMethod() { }
}
```

### Read the user from the security context

Application code should read the authenticated user from Spring Security's context. Do not read identity values from request parameters or headers that a client can change.

```java
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

Authentication auth = SecurityContextHolder.getContext().getAuthentication();
String userId = auth.getName();
```

### Keep build output out of version control

Generated folders such as `bin/` and `target/` should be in `.gitignore`. Committed build output produces noisy diffs and merge conflicts.

### Review the diff before committing

A commit that touches files with no real change adds noise to history. Check the diff before staging, and revert formatting-only changes that were not part of the task.

### Comments explain why, not what

A comment that restates the code is noise. A comment that explains the reason for an unusual choice is valuable, because the code cannot show it.

```java
public class RetryCounter {
    private int counter;
    private int failedRetries;

    void update() {
        // Bad: says what the code already says
        // Increment counter
        counter++;

        // Good: says why
        // Count failed retries so the circuit opens after three failures
        failedRetries++;
    }
}
```

### Do not leave commented-out code

Commented-out code is hard to tell apart from documentation, and nobody dares to delete it. Version control keeps the old code. Delete the block and mention the commit in the pull request description if the history matters.

---

## 10. Enum and Type Safety

### Make enum state private and final

A public field on an enum can be changed by any caller, which breaks the assumption that enum constants are fixed. Make the field `private final`, set it in the constructor, and expose it through a getter.

```java
public class BadStatusExample {
    // Bad
    public enum Status {
        ACTIVE("A"), INACTIVE("I");
        public String code;

        Status(String code) {
            this.code = code;
        }
    }
}

public class GoodStatusExample {
    // Good
    public enum Status {
        ACTIVE("A"), INACTIVE("I");

        private final String code;

        Status(String code) {
            this.code = code;
        }

        public String getCode() {
            return code;
        }
    }
}
```

### Put behaviour on the enum instead of switching on it

When each constant has its own behaviour, store that behaviour in the enum. A new constant then cannot be added without deciding its behaviour, and the switch statement elsewhere disappears.

```java
public class StatusSwitch {
    // Bad: a switch in every caller
    static boolean isActiveBad(String status) {
        switch (status) {
            case "ACTIVE": return true;
            case "INACTIVE": return false;
            default: return false;
        }
    }
}

// Good
public enum Status {
    ACTIVE(true), INACTIVE(false);

    private final boolean active;

    Status(boolean active) {
        this.active = active;
    }

    public boolean isActive() {
        return active;
    }
}
```

---

## Review Checklist

Use this list during a review. Items are grouped by the kind of problem they catch. Not every item applies to every change.

### Before the review

- [ ] The pull request states its intent and the requirement it meets
- [ ] New behaviour has tests, and the tests are in the same change
- [ ] No `TODO` or `FIXME` comments were added without a linked ticket

### Critical issues

- [ ] Failures propagate or are handled. There are no silent catch blocks
- [ ] Exceptions are specific, not a generic `Exception`
- [ ] Input from outside the system is validated and null-checked
- [ ] No SQL built by string concatenation with user input
- [ ] No credentials, tokens, or personal data are hard-coded or logged

### Code quality

- [ ] Each method does one thing
- [ ] No method runs past roughly 50 to 70 statements
- [ ] Names are clear and say what the value means
- [ ] No commented-out code
- [ ] No unused imports, variables, or parameters
- [ ] Log output is useful, and the level matches the severity

### Performance

- [ ] No N+1 query pattern in loops over entities
- [ ] Collections are created with the right size or type
- [ ] Streams are used for transformations, and their results are consumed
- [ ] No string concatenation with `+=` inside loops
- [ ] Remote calls are batched where the API allows

### Style and formatting

- [ ] Braces follow the team style
- [ ] Nesting is at most three levels
- [ ] Blank lines separate logical groups
- [ ] Mixed `&&` and `||` conditions use parentheses
- [ ] The change matches the team style guide

### Testing

- [ ] Edge cases are covered: `null`, empty, and boundary values
- [ ] Existing tests were not changed to make a failing build pass, unless the behaviour changed on purpose
- [ ] Test data is realistic and does not contain real personal data

---

## Sources

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html): formatting and naming conventions
- [Spring Framework reference documentation](https://docs.spring.io/spring-framework/reference/): dependency injection and component lifecycle
- Joshua Bloch, *Effective Java*: null handling, enums, and immutability
- Robert C. Martin, *Clean Code*: method size, naming, and comments
- [Apache Commons Lang](https://commons.apache.org/proper/commons-lang/): `StringUtils`, `NumberUtils`
