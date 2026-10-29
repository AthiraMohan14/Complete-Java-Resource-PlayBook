# Spring MVC

Spring MVC is the web framework built on the Servlet API. A single front controller, the `DispatcherServlet`, receives every request and delegates it to your controller methods, then turns the result into a response. Interviewers ask about Spring MVC to check that you understand the request pipeline, where filters and interceptors fit, and how a request becomes a method call.

## Core concepts

### The DispatcherServlet and the request pipeline

`DispatcherServlet` is the front controller. For each request, it:

1. Finds the handler (usually a controller method) with a **HandlerMapping**.
2. Finds an adapter that knows how to call that handler (a **HandlerAdapter**).
3. Runs the handler, which returns data or a view name.
4. Resolves the view with a **ViewResolver** (for HTML pages) or writes the body directly (for REST responses using `@ResponseBody` or `ResponseEntity`).

```text
Client -> Servlet Filters -> DispatcherServlet
            -> HandlerInterceptors (preHandle)
            -> Controller method
            -> HandlerInterceptors (postHandle, afterCompletion)
            -> ViewResolver (view pages) or message converter (REST)
          -> Response
```

Spring Boot registers `DispatcherServlet` automatically on the embedded server.

### Controllers and request mapping

```java
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.servlet.ModelAndView;

@Controller
@RequestMapping("/orders")
public class OrderPageController {

    @GetMapping("/{id}")
    public ModelAndView show(@PathVariable long id) {
        ModelAndView mav = new ModelAndView("order-detail");   // view name
        mav.addObject("orderId", id);                          // model attribute
        return mav;
    }
}
```

`@Controller` returns view names resolved by a `ViewResolver`. `@RestController` (for APIs) combines `@Controller` and `@ResponseBody`, so return values are written directly to the response body.

`@RequestMapping` sets the path and HTTP method; the shortcut annotations `@GetMapping`, `@PostMapping`, and similar set the method. Method-level mappings combine with class-level ones.

### Request context

Handlers often need information about the current request, such as the locale, the request path, or a model. Use method parameters (`HttpServletRequest`, `Locale`, `Model`) where possible. When you need the request in a non-web bean, `RequestContextHolder` exposes the current request for the thread, and `RequestContext` (in `org.springframework.web.servlet.support`) gives a view of the request and locale helpers.

### Model and views

`Model` (or `ModelAndView`) carries data from the controller to the view. The view resolver turns the view name into a template (Thymeleaf, JSP, or similar). In REST APIs, skip the model and return data.

### Interceptors vs filters

| | Servlet filter | `HandlerInterceptor` |
|---|---|---|
| Layer | Servlet container, before `DispatcherServlet` | Inside Spring MVC, around the handler |
| Knows the handler? | No | Yes; receives the handler object |
| Hooks | `doFilter` (wraps the whole chain) | `preHandle`, `postHandle`, `afterCompletion` |
| Typical use | Encoding, CORS at the container level, security chain entry | Logging per controller, auth checks, timing |
| Registration | `FilterRegistrationBean` or `@Component` implementing `Filter` | `WebMvcConfigurer.addInterceptors` |

```java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.servlet.HandlerInterceptor;

public class TimingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute("startNanos", System.nanoTime());
        return true;                        // false stops the request here
    }
}
```

Register it in a `WebMvcConfigurer` with `registry.addInterceptor(new TimingInterceptor())`. Use a filter when you need the raw request before Spring MVC runs, such as for security entry points.

### Locale and theme resolution

- **LocaleResolver** decides the request's locale, from a cookie, a session attribute, or the `Accept-Language` header. `LocaleChangeInterceptor` lets a request parameter change it.
- **ThemeResolver** chooses a theme (a set of resource bundles and stylesheets) for views. It is rarely used in modern APIs.

### REST responses and content negotiation

`@ResponseBody` (implied by `@RestController`) passes the return value to an `HttpMessageConverter`, which writes JSON, XML, or another media type. Content negotiation picks the type from the `Accept` header. `ResponseEntity` controls the status code and headers.

```java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class OrderApiController {

    @GetMapping("/api/orders/{id}")
    public ResponseEntity<String> get(@PathVariable long id) {
        return ResponseEntity.ok("order " + id);   // 200 with a text body
    }
}
```

For errors, see the exception handling approach in the Spring Boot section of the roadmap; RFC 9457 (Problem Details) defines a standard error body.

## How it works / Step by step

For a request to `GET /orders/42`:

1. The servlet filter chain runs.
2. `DispatcherServlet` asks the `HandlerMapping` for a handler; it matches `OrderPageController.show`.
3. The `HandlerAdapter` converts the path variable `42` to `long` and calls the method.
4. Interceptors run `preHandle` before the method and `postHandle` after it.
5. The controller returns a view name; the `ViewResolver` produces the page, or a REST return value goes through a message converter.
6. `afterCompletion` runs whether or not an exception happened.

## Common pitfalls

- Returning an entity directly from a controller, which exposes internal fields and can trigger lazy loading.
- Using `@Controller` where `@RestController` was intended, so the return value is treated as a view name.
- Assuming an interceptor runs for requests that a filter rejects. Filters run first and can stop the chain.
- Doing heavy blocking work in a controller on a thread that should be serving requests.
- Relying on `Model` state across requests without a session scope.
- Forgetting that `preHandle` returning `false` must write the response, or the client gets an empty reply.

!!! tip "Interview tip"
    **Q: What is the difference between a filter and an interceptor?**
    A filter is part of the Servlet API and runs before Spring MVC, so it sees raw requests and does not know which controller will handle them. An interceptor is part of Spring MVC and runs around the handler, so it can use handler information. Use filters for container-level concerns and interceptors for per-controller concerns.

## Quick recap

- `DispatcherServlet` is the front controller: handler mapping, handler adapter, then view or message conversion.
- `@Controller` returns views; `@RestController` writes bodies directly.
- Filters run before Spring MVC; interceptors run around handlers.
- `ResponseEntity` controls status and headers; message converters handle JSON.
- Keep request-scoped data in parameters or the request context, not in singletons.

**See also:** [AOP](aop.md), [Transactions](transactions.md), [Dependency Injection](dependency-injection.md)
