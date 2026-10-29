# Spring Security: Filter Chain, Authorisation, and Method Security

Spring Security protects an application by running every request through a chain of servlet filters before it reaches your controllers. Authentication establishes who the caller is, and authorisation decides what that caller may do. Interviewers ask about this because most security bugs in Spring apps come from misunderstanding the filter chain, the rule order, or where method security applies.

## Core concepts

### Authentication versus authorisation

Authentication answers "who are you?", usually by checking a password, token, or certificate. Authorisation answers "are you allowed to do this?", by checking roles, authorities, or ownership. A request can be authenticated and still be forbidden: the server returns `401` when authentication is missing or invalid, and `403` when the caller is known but not permitted.

### The filter chain

When a request arrives, the servlet container calls a `DelegatingFilterProxy` registered as a servlet filter. It hands the request to Spring's `FilterChainProxy`, which selects the first `SecurityFilterChain` whose request matcher fits and runs its filters in order. Those filters include CSRF protection, the authentication filters (basic, form, bearer token), and the authorisation check. Only then does the request reach your `DispatcherServlet` and controllers.

The roadmap calls this a "DispatcherFilter pattern"; the Spring classes to know are `DelegatingFilterProxy` and `FilterChainProxy`. The idea is the same: one front door of filters that decides before your code runs.

### Declaring a SecurityFilterChain

Spring Security 6 removed `WebSecurityConfigurerAdapter`. You declare a `SecurityFilterChain` bean instead.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableMethodSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**", "/actuator/health").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }
}
```

Rules are evaluated top to bottom, and the first match wins. Put the most specific rules first and end with a catch-all such as `anyRequest().authenticated()`, so new endpoints are protected by default.

### SecurityContext, Authentication, and GrantedAuthority

After successful authentication, Spring stores an `Authentication` object in the `SecurityContext`, held per thread (or per reactive context). The `Authentication` holds the principal (who), credentials (usually cleared after login), and a collection of `GrantedAuthority` values. Authorities are plain strings such as `ROLE_ADMIN` or `INVOICE_READ`. `hasRole("ADMIN")` checks for `ROLE_ADMIN`, because the `ROLE_` prefix is added for you.

### UserDetailsService and UserDetails

`UserDetailsService.loadUserByUsername` loads a user by name, and `UserDetails` describes the password hash, authorities, and account status. The `DaoAuthenticationProvider` uses this service and a `PasswordEncoder` to verify credentials.

```java
import java.util.List;
import java.util.Optional;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

record AppUser(String email, String passwordHash, List<String> roles) {}

interface AppUserRepository {
    Optional<AppUser> findByEmail(String email);
}

@Service
class DbUserDetailsService implements UserDetailsService {

    private final AppUserRepository users;

    DbUserDetailsService(AppUserRepository users) {
        this.users = users;
    }

    @Override
    public UserDetails loadUserByUsername(String username) {
        AppUser user = users.findByEmail(username)
                .orElseThrow(() -> new UsernameNotFoundException("unknown user"));
        return User.withUsername(user.email())
                .password(user.passwordHash())
                .authorities(user.roles().toArray(String[]::new))   // e.g. "ROLE_ADMIN"
                .build();
    }
}
```

Use the stored hash in `password(...)`, never the raw password. The `authorities(...)` method takes full authority names, while `roles(...)` adds the `ROLE_` prefix for you.

### Role-based access control and fine-grained rules

RBAC grants permissions through roles. It works well when roles map to clear responsibilities. Attribute-based rules (for example, "only the owner of this invoice") need the value of the resource, so they belong at method level, where you have the arguments.

### Method security

`@EnableMethodSecurity` (the replacement for the older `@EnableGlobalMethodSecurity`) turns on annotations on Spring beans:

- `@PreAuthorize` checks before the method runs; it can use SpEL and method parameters.
- `@PostAuthorize` checks after the method runs and can inspect `returnObject`.
- `@Secured` checks role names only.
- `@RolesAllowed` (JSR-250) requires enabling JSR-250 support.

```java
import org.springframework.security.access.prepost.PostAuthorize;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;

record Invoice(String id, String ownerId, long amountCents) {}

@Service
class InvoiceService {

    @PreAuthorize("hasAuthority('INVOICE_READ') or #ownerId == authentication.name")
    Invoice find(String ownerId, String invoiceId) {
        return new Invoice(invoiceId, ownerId, 1200L); // load from storage here
    }

    @PostAuthorize("returnObject.ownerId() == authentication.name")
    Invoice byIdForAnyone(String invoiceId) {
        return new Invoice(invoiceId, "someone", 500L);
    }
}
```

Method security applies only when the call crosses the Spring proxy. A method calling another method on the same class (`this.find(...)`) skips the check. That is one of the most common mistakes.

### Authentication providers

An `AuthenticationManager` delegates to one or more `AuthenticationProvider` beans. Each provider knows how to authenticate one kind of credential, such as username and password, a JWT, or a certificate. Custom providers are the extension point when your login does not fit the defaults.

## Login, ownership, and error handling

### A login endpoint with AuthenticationManager

A login endpoint hands the submitted credentials to the `AuthenticationManager`. The manager is exposed as a bean, typically from `AuthenticationConfiguration.getAuthenticationManager()`.

```java
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

record LoginRequest(String username, String password) {}

@RestController
@RequestMapping("/auth")
class LoginController {

    private final AuthenticationManager authenticationManager;

    LoginController(AuthenticationManager authenticationManager) {
        this.authenticationManager = authenticationManager;
    }

    @PostMapping("/login")
    ResponseEntity<Map<String, String>> login(@RequestBody LoginRequest request) {
        try {
            Authentication auth = authenticationManager.authenticate(
                    UsernamePasswordAuthenticationToken.unauthenticated(
                            request.username(), request.password()));
            // A real API issues a token here (see the authentication page)
            return ResponseEntity.ok(Map.of("user", auth.getName()));
        } catch (BadCredentialsException ex) {
            // The same message for unknown users and wrong passwords
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "invalid username or password"));
        }
    }
}
```

Throw `BadCredentialsException`, not a generic `RuntimeException`, so the status code is correct. By default the DAO authentication provider reports an unknown user as bad credentials too, which keeps account names from leaking through the response.

### Ownership rules with a custom principal

An expression such as `authentication.principal.id` needs the principal to have an `id` property. Spring's default `User` has none. Create a `UserDetails` implementation that exposes `getId()`, and load it in your `UserDetailsService`. Then the SpEL expression works.

### Custom permission checks

A `PermissionEvaluator` answers `hasPermission(...)` expressions. It is useful when the rule depends on the object's owner or state. Register it in a `MethodSecurityExpressionHandler`, or the expression fails at runtime.

```java
import java.io.Serializable;
import org.springframework.security.access.PermissionEvaluator;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

record Post(Long id, String authorName) {}

@Component
class PostPermissionEvaluator implements PermissionEvaluator {

    @Override
    public boolean hasPermission(Authentication authentication, Object target, Object permission) {
        if (target instanceof Post post && "EDIT".equals(permission)) {
            return post.authorName().equals(authentication.getName()) || hasRole(authentication, "ADMIN");
        }
        return false;
    }

    @Override
    public boolean hasPermission(Authentication authentication, Serializable targetId,
                                 String targetType, Object permission) {
        return false;   // an ID-based check would load the object here
    }

    private boolean hasRole(Authentication authentication, String role) {
        return authentication.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_" + role));
    }
}
```

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.PermissionEvaluator;
import org.springframework.security.access.expression.method.DefaultMethodSecurityExpressionHandler;
import org.springframework.security.access.expression.method.MethodSecurityExpressionHandler;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;

@Configuration
@EnableMethodSecurity
class MethodSecurityConfig {

    @Bean
    static MethodSecurityExpressionHandler methodSecurityExpressionHandler(PermissionEvaluator evaluator) {
        DefaultMethodSecurityExpressionHandler handler = new DefaultMethodSecurityExpressionHandler();
        handler.setPermissionEvaluator(evaluator);
        return handler;
    }
}
```

```java
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;

@Service
class PostService {

    @PreAuthorize("hasPermission(#post, 'EDIT')")
    Post update(Post post) {
        return post;   // persist the change here
    }
}
```

The parameter name `post` in the expression is resolved from the method signature. Spring Boot's parent POM compiles with `-parameters`, so the names are available; without it, annotate the parameter with `@P("post")`.

### Shaping responses by role

Prefer separate response types for each audience over setting fields to `null` for non-admins. With separate types, a new sensitive field cannot reach the wrong audience by accident. Choose the endpoint or the response type from the caller's authorities, and keep the admin-only fields out of the public record.

```java
import java.time.Instant;
import java.util.List;

public record UserView(long id, String username) {}

public record AdminUserView(long id, String username, String email,
                            List<String> roles, Instant createdAt) {}
```

### JSON errors for 401 and 403

By default, Spring Security's error responses are not in your API's format. Replace the access-denied handler, and set an authentication entry point for missing or invalid credentials, so both return a Problem Details body (see [Pagination, Errors, and Idempotency](../21-api-design/pagination-errors-idempotency.md)).

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Component
class JsonAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper mapper;

    JsonAccessDeniedHandler(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       AccessDeniedException ex) throws IOException {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.FORBIDDEN, "You do not have permission for this action.");
        problem.setTitle("Access denied");
        response.setStatus(HttpStatus.FORBIDDEN.value());
        response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);
        mapper.writeValue(response.getOutputStream(), problem);
    }
}
```

Register the handler in the filter chain with `http.exceptionHandling(ex -> ex.accessDeniedHandler(handler))`. Write a matching `AuthenticationEntryPoint` for `401`, using the same pattern.

### Auditing access with AOP

An aspect can record who called a sensitive method. Put the annotation on the method and let the aspect read the caller from the `SecurityContext`.

```java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@interface Audited {
}
```

```java
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

@Aspect
@Component
class AuditAspect {

    private static final Logger log = LoggerFactory.getLogger(AuditAspect.class);

    @Around("@annotation(com.example.security.Audited)")
    public Object audit(ProceedingJoinPoint joinPoint) throws Throwable {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String caller = auth == null ? "anonymous" : auth.getName();
        log.info("audit caller={} operation={}", caller, joinPoint.getSignature().toShortString());
        return joinPoint.proceed();
    }
}
```

The aspect needs `spring-boot-starter-aop`. Log only identifiers, never request bodies or secrets. For compliance, write to a protected audit table rather than an ordinary application log. Also decide whether to record before or after the call; this example records before it, so a failed call is still logged.

## How it works / Step by step

1. The request enters `DelegatingFilterProxy`, then `FilterChainProxy`.
2. The matching `SecurityFilterChain` runs its filters: CSRF check, authentication (for example, basic auth or bearer token), then the authorisation check.
3. If authentication is missing, the entry point returns `401`. If authorisation fails, the access-denied handler returns `403`.
4. On success, the `Authentication` is placed in the `SecurityContext`, and the request reaches the controller.
5. Method-level annotations are checked when a secured bean's method is called through its proxy.

## Common pitfalls

- Relying on the front end to hide buttons. Every endpoint must check on the server.
- Rule order mistakes: a broad `permitAll()` placed before a specific `hasRole` rule makes the specific one unreachable.
- Using `hasRole("ROLE_ADMIN")`, which checks for `ROLE_ROLE_ADMIN`.
- Forgetting `@EnableMethodSecurity`, so `@PreAuthorize` annotations are silently ignored.
- Self-invocation, which bypasses method security (see above).
- Leaking data in `@PostAuthorize`: the method has already run and loaded the data.
- Exposing internal details in `403` or `401` responses.

!!! tip "Interview tip"
    **Q: How does Spring Security decide whether a request is allowed?**
    The request passes through a chain of filters inside `FilterChainProxy`. The first `SecurityFilterChain` whose matcher fits runs its filters: authentication populates the `SecurityContext`, and the authorisation rules check the request's authorities. Rules are ordered, so the first match wins. Method security adds a second check on the proxied bean.

## Quick recap

- Authentication identifies the caller (`401` on failure); authorisation checks permissions (`403` on failure).
- Requests pass through `DelegatingFilterProxy` into `FilterChainProxy` and a `SecurityFilterChain`.
- Declare a `SecurityFilterChain` bean; Spring Security 6 has no `WebSecurityConfigurerAdapter`.
- Use `@EnableMethodSecurity` with `@PreAuthorize` and `@PostAuthorize` for ownership and data rules.
- Protect by default: end with `anyRequest().authenticated()`.

**See also:** [Authentication: JWT, OAuth 2.0, and OpenID Connect](authentication-jwt-oauth.md) | [Password Security and OWASP](password-security-owasp.md) | [Integration Testing](../11-testing/integration-testing.md)
