# Spring and Security Questions (Part 4 of 4)

Continued from [Part 3](spring-and-security-part-3.md).

These questions cover form binding with `@ModelAttribute`, entity discovery, the cost of AOP, and server-side templating.

---

## 37. What is the purpose of @ModelAttribute in Spring Boot?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@ModelAttribute` binds request parameters and form fields to a Java object by property name, and it can place an object into the model that a view reads. On a method parameter, it creates the object, fills it from the request, and makes it available to the handler. On a method, it runs before the handler methods in the same controller and adds its return value to the model. It is meant for form-style data, not for JSON bodies, which use `@RequestBody`.

### Explanation
There are three common uses:

- **Request binding.** A parameter annotated with `@ModelAttribute` is built by Spring's data binder, which converts strings to the property types. Pair it with `@Valid` and a `BindingResult` parameter to handle validation errors without throwing.
- **Model population.** A method annotated with `@ModelAttribute` returns data that every handler in the controller can use, such as a list of options for a drop-down. The value is added to the model under the given name, or under a name derived from its type.
- **Method-level use.** The method runs before each `@RequestMapping` method in the same controller, so shared setup happens in one place.

```java
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
class ProfileController {

    @ModelAttribute("countries")                     // added to the model before the handler runs
    java.util.List<String> countries() {
        return java.util.List.of("AU", "NZ", "US");
    }

    @PostMapping("/profile")
    String save(@ModelAttribute ProfileForm form) {  // filled from form fields by name
        return "profile-saved";
    }
}

class ProfileForm {
    private String displayName;
    public String getDisplayName() { return displayName; }
    public void setDisplayName(String displayName) { this.displayName = displayName; }
}
```

### When to use / pitfalls
- A JSON body sent with `application/json` is not bound by `@ModelAttribute`. Use `@RequestBody` for that.
- Binding straight into a JPA entity lets a client set fields it should not control, such as an id or a role. Use a dedicated form or DTO class instead.
- Use `@ModelAttribute` in a `@Controller` that renders views. In a `@RestController`, the binding still works, but the usual reason to use the model is gone.

**See also:** [Building REST APIs with Spring Boot](../../learning/09-spring-boot/rest-apis.md), [Spring MVC](../../learning/08-spring-core/spring-mvc.md)

</details>

---

## 38. What is @EntityScan and when do you need it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
`@EntityScan` tells JPA which packages to search for classes annotated with `@Entity`. Spring Boot searches the package of the `@SpringBootApplication` class and its subpackages by default, so you need `@EntityScan` only when entities live outside that package tree, such as in a sibling module or a shared library. If Hibernate does not know about an entity class, using it fails at runtime, typically with a "Not a managed type" error.

### Explanation
`@EntityScan` affects only entity discovery. Spring beans are still found by component scanning, and repositories are still found by `@EnableJpaRepositories`. If your repositories are also outside the default package, you usually add `@EnableJpaRepositories` as well. The annotation accepts `basePackages` for package names or `basePackageClasses` for a type-safe reference to a package.

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication
@EntityScan(basePackages = "com.example.billing.model")
@EnableJpaRepositories(basePackages = "com.example.billing.repository")
public class ShopApplication {
    public static void main(String[] args) {
        SpringApplication.run(ShopApplication.class, args);
    }
}
```

### When to use / pitfalls
- Add `@EntityScan` when entities come from another module or jar, and list every package that holds them.
- Keep the package list narrow. A very broad scan can make startup slower and pick up classes you did not intend to map.
- Do not confuse it with `@ComponentScan`. Adding a package to `@ComponentScan` does not register its entities.

**See also:** [Boot Basics and Configuration](../../learning/09-spring-boot/boot-basics-configuration.md), [JPA and Hibernate](../../learning/07-jdbc-jpa/jpa-hibernate.md)

</details>

---

## 39. What are the performance implications of using AOP in Spring?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Spring AOP adds a proxy and an advice chain to every call on an advised method. For most service methods, that cost is small compared with database or network calls, but it adds up on hot paths. The main levers are how many beans and methods are advised (pointcut breadth), how much work each advice does, and whether `around` advice is needed at all. Self-invocation adds no overhead, but it also skips the advice, so it changes behaviour rather than speed.

### Explanation
- **Proxy overhead.** Each call through the proxy builds an invocation and runs the advice chain in order. Per call this is minor, but a method called millions of times in a tight loop pays for it every time.
- **Pointcut breadth.** Most pointcut expressions are matched when the beans are created, so a broad pointcut mainly means more proxies and more advised methods. Some expressions, such as those that test arguments at runtime, are checked on every call. Narrow the pointcut to an annotation or a specific package where you can.
- **Advice body.** Work in advice runs on every call. String building for logs, reflection, and locks are the usual costs. Check the log level before building messages.
- **Around advice.** `@Around` needs a `ProceedingJoinPoint` and adds a frame. For simple before or after logic, `@Before` or `@AfterReturning` is cheaper and easier to read.
- **Measure, do not guess.** Use a profiler such as Java Flight Recorder, or a micro-benchmark built with JMH, to see whether the advice matters.

### When to use / pitfalls
- Avoid advising getters, tight loops, or per-element methods on hot paths. Use an explicit call instead.
- Do not put I/O or heavy computation inside `@Around` advice.
- Apply tracing or auditing to the service layer, not to every method in the application.
- Remember that Spring AOP only advises public method calls that go through the proxy. Advice that appears to be missing is often a self-invocation problem, not a performance one.

**See also:** [Aspect-Oriented Programming](../../learning/08-spring-core/aop.md), [Transactions](../../learning/08-spring-core/transactions.md)

</details>

---

## 40. What is Thymeleaf or FreeMarker, and when would you use server-side templating instead of REST JSON?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Thymeleaf and FreeMarker are template engines. A controller puts data in the model, and the engine renders an HTML page on the server, which is then sent to the browser. Use server-side templating when the server should own the page: content-heavy pages, forms with server-side validation, internal admin tools, or a small team that wants one deployable unit. Use REST JSON with a separate client, such as a single-page app or a mobile app, when several clients need the same data or the front end needs rich interaction.

### Explanation
**Thymeleaf** uses natural templates, which are valid HTML that a browser can open as a static prototype. Attributes such as `th:text` add the dynamic parts, and output is HTML-escaped by default. Spring Boot configures a Thymeleaf view resolver when `spring-boot-starter-thymeleaf` is on the classpath, and templates are read from `src/main/resources/templates`.

**FreeMarker** uses its own syntax with directives, such as `${name}` and `<#if>`. It is also supported by Spring MVC. It is less tied to HTML structure than Thymeleaf.

**Server-side rendering versus SPA.** Server-side rendering sends a complete page on the first request, works without much client code, keeps authentication in a session cookie, and suits content that search engines should index. An SPA with a JSON API gives a richer client-side experience and lets several clients share one API, but it splits the work into two codebases and adds concerns such as token handling and CORS. Approaches that send HTML fragments from the server sit between the two.

### When to use / pitfalls
- A controller that renders a view returns a view name, so it must be a `@Controller`. Using `@RestController` writes the return value to the response body instead.
- Thymeleaf escapes `th:text` output by default. Using `th:utext` with user input opens the page to cross-site scripting.
- Keep business rules in services, not in templates. Templates should only format what they are given.
- Do not choose server-side rendering only because it is simpler to start. Decide from the clients and the kind of interaction you need.

**See also:** [Spring MVC](../../learning/08-spring-core/spring-mvc.md), [Building REST APIs with Spring Boot](../../learning/09-spring-boot/rest-apis.md)

</details>

---

## Quick recap

- `@ModelAttribute` binds form fields and fills the model; use `@RequestBody` for JSON.
- `@EntityScan` is needed only when entities sit outside the application's package tree.
- AOP costs come from proxy calls, broad pointcuts, and heavy advice; measure before optimising.
- Thymeleaf and FreeMarker render HTML on the server; choose them when the server should own the page.
- Thymeleaf escapes output by default, so avoid `th:utext` with untrusted input.

**See also:** [Spring and Security part 1](spring-and-security-part-1.md), [Spring and Security part 2](spring-and-security-part-2.md), [Spring and Security part 3](spring-and-security-part-3.md)
