# Spring Core and Fundamentals

The Spring container and the features built on it: IoC and beans, dependency injection, configuration, AOP, the MVC request pipeline, and declarative transactions. This section covers roadmap section 8.

---

## Topics

### [IoC and Beans](ioc-and-beans.md)
**ApplicationContext - bean scopes - lifecycle - configuration styles**
What the container manages, how beans are scoped, and the order of steps from creation to destruction.

### [Dependency Injection](dependency-injection.md)
**constructor injection - @Autowired - @Qualifier - @Primary - circular dependencies**
Injection styles, why constructor injection is preferred, resolving ambiguous beans, and redesigning cycles.

### [Stereotypes and Configuration](stereotypes-and-configuration.md)
**@Component - @Service - @Repository - @Configuration - @Bean - component scanning**
Marking classes as beans, declaring beans in code, and controlling what scanning picks up.

### [AOP](aop.md)
**@Aspect - advice - pointcuts - proxies - self-invocation**
Cross-cutting concerns, how Spring AOP uses JDK and CGLIB proxies, and where proxies fail.

### [Spring MVC](spring-mvc.md)
**DispatcherServlet - controllers - interceptors vs filters - ResponseEntity**
The request pipeline from the front controller to the response, with controllers, interceptors, and content negotiation.

### [Transactions](transactions.md)
**@Transactional - propagation - rollback rules - isolation - TransactionTemplate**
Declarative and programmatic transactions, propagation choices, and why rollbacks sometimes do not happen.
