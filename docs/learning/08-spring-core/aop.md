# Aspect-Oriented Programming

Aspect-oriented programming (AOP) separates cross-cutting concerns, such as logging, security checks, timing, and transactions, from business logic. Spring AOP applies aspects to beans at runtime using proxies. Interviewers ask about AOP to see whether you understand the proxy mechanism, its limits (especially self-invocation), and how `@Transactional` and similar annotations really work.

## Core concepts

### Vocabulary

| Term | Meaning |
|---|---|
| Aspect | A module that groups advice and pointcuts (a class annotated with `@Aspect`) |
| Join point | A point in program execution. Spring AOP supports only method execution join points |
| Pointcut | An expression that selects join points |
| Advice | Code that runs at a join point (before, after, around) |
| Weaving | Linking aspects into the code. Happens at compile time, load time, or runtime |
| Target | The object being advised |

### Advice types

| Annotation | Runs |
|---|---|
| `@Before` | Before the method |
| `@AfterReturning` | After the method returns normally; can read the return value |
| `@AfterThrowing` | After the method throws; can read the exception |
| `@After` | After the method, whether it returned or threw (like `finally`) |
| `@Around` | Wraps the method; controls whether and how it is called |

`@Around` is the most powerful. It receives a `ProceedingJoinPoint` and must call `proceed()` to run the target.

```java
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class TimingAspect {

    @Around("execution(* com.example.orders..*(..))")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        try {
            return pjp.proceed();                          // run the advised method
        } finally {
            long millis = (System.nanoTime() - start) / 1_000_000;
            System.out.println(pjp.getSignature() + " took " + millis + " ms");
        }
    }
}
```

The `execution(...)` pattern selects methods in the `orders` package and its subpackages. Spring AOP needs `spring-boot-starter-aop` (or the AspectJ libraries) on the classpath to read `@Aspect` annotations.

### Pointcut expressions

The common designators are:

- `execution(...)`: match method signatures. The most common in Spring AOP.
- `within(...)`: match all methods of types in a package or class.
- `@annotation(...)`: match methods that carry an annotation, such as `@Audited`.
- `bean(...)`: match beans by name (a Spring-specific extension).

```java
import org.aspectj.lang.annotation.Before;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class AuditAspect {

    @Before("@annotation(com.example.audit.Audited) && within(com.example.payments..*)")
    public void record() {
        // runs before any @Audited method in the payments package
    }
}
```

Named pointcuts (`@Pointcut`) let you reuse expressions across advice methods.

### Proxy-based AOP

Spring creates a proxy around each advised bean, and callers talk to the proxy. The proxy runs the advice and then delegates to the real target.

- If the bean implements an interface, Spring can use a **JDK dynamic proxy** (the interface is proxied).
- Otherwise, or when configured, Spring uses **CGLIB**, which subclasses the bean.
- Spring Boot defaults to CGLIB proxies (`spring.aop.proxy-target-class=true`), so proxies work for classes without interfaces.

This design has consequences:

- Only public (and, depending on configuration, protected) methods called through the proxy are advised.
- `final` classes and `final` methods cannot be proxied by CGLIB.
- Calls from one method of a bean to another method of the same bean (**self-invocation**) bypass the proxy, so advice does not run.

### Self-invocation

```java
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReportService {

    public void publish() {
        refresh();          // this.refresh(): bypasses the proxy, no transaction starts
    }

    @Transactional
    public void refresh() {
        // runs without a transaction when called from publish()
    }
}
```

Fixes: move the advised method to another bean, inject the bean into itself (less clean), or use `AopContext.currentProxy()` with exposed proxies. Moving the method to a separate bean is the clean answer.

### Weaving types

| Weaving | When | Used by |
|---|---|---|
| Compile-time | Source or bytecode is changed during build | AspectJ compiler (`ajc`) |
| Load-time | Classes are changed as the JVM loads them | AspectJ with a Java agent |
| Runtime | Proxies are created at run time | Spring AOP |

Spring AOP uses runtime proxies, so it can only advise beans managed by Spring, and only method execution. Full AspectJ can advise fields, constructors, and non-Spring objects, at the cost of more setup.

### Typical cross-cutting concerns

- Logging and tracing of method entry and exit.
- Security checks, for example `@PreAuthorize` in Spring Security, which is implemented as an interceptor.
- Transactions (`@Transactional` is implemented with a transaction interceptor, see [Transactions](transactions.md)).
- Caching (`@Cacheable`) and retries.
- Validation of arguments at method boundaries.

## How it works / Step by step

When a bean with matching advice is created:

1. A bean post-processor sees that advice applies and wraps the bean in a proxy.
2. A caller gets the proxy from the container (or via injection).
3. Calling a method on the proxy runs matching advice in order: `@Before`, then the target (through `@Around` if present), then `@AfterReturning` or `@AfterThrowing`, then `@After`.
4. The target's return value or exception goes back to the caller.

## Common pitfalls

- Expecting advice on self-invoked methods. This is the most common AOP bug.
- Advising private methods, which proxies cannot intercept.
- Forgetting to call `proceed()` in `@Around`, which silently skips the method.
- Swallowing exceptions in `@Around`, which changes behaviour.
- Writing pointcuts that match too broadly, which slows every call.
- Putting business logic in aspects, which makes behaviour hard to find.

!!! tip "Interview tip"
    **Q: Why does `@Transactional` not work when I call the method from the same class?**
    The annotation is applied by a proxy. A call from inside the class goes to `this`, which is the raw target, so the proxy never runs and no transaction starts. Move the method to another bean, or restructure so the call goes through the proxy.

## Quick recap

- AOP separates cross-cutting concerns; advice runs at method join points.
- `@Around` wraps the method and must call `proceed()`.
- Spring AOP uses runtime proxies: JDK for interfaces, CGLIB for classes (the Boot default).
- Self-invocation bypasses the proxy, so advice does not apply.
- Only public methods called through the proxy are advised; `final` classes and methods cannot be proxied by CGLIB.

**See also:** [Transactions](transactions.md), [Stereotypes and Configuration](stereotypes-and-configuration.md), [Spring MVC](spring-mvc.md)
