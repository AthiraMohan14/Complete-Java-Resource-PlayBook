# Testing

Testing gives you confidence to change code. In a Java backend, that means fast unit tests for logic, mocks for collaborators you control, integration tests against real infrastructure, and API tests that exercise the contract clients depend on. These notes cover JUnit 5, Mockito, Spring Boot integration testing, API testing, and coverage, with the trade-offs interviewers ask about.

---

## Topics

### [Unit Testing with JUnit 5](unit-testing-junit.md)
**@Test - lifecycle - @ParameterizedTest - @Nested - assertions - AssertJ**
Writing fast, focused tests with the JUnit 5 lifecycle, parameterised and dynamic tests, and readable assertions.

### [Mocking with Mockito](mockito.md)
**@Mock - @InjectMocks - @Spy - when/thenReturn - verify - ArgumentCaptor**
Isolating a unit from its collaborators, verifying interactions, and knowing when a mock is the wrong tool.

### [Integration Testing](integration-testing.md)
**@SpringBootTest - context caching - @DirtiesContext - Testcontainers - @ServiceConnection**
Testing wiring, persistence, and messaging against real or near-real dependencies, and keeping the suite fast.

### [API Testing and Code Coverage](api-testing-and-coverage.md)
**MockMvc - REST Assured - Postman and Newman - Spring Cloud Contract - JaCoCo - SonarQube**
Testing HTTP contracts end to end, and measuring coverage in a way that reflects real test quality.

---

**See also:** [HTTP Clients and Testing](../09-spring-boot/http-clients-and-testing.md) | [Spring Security Authorisation](../10-security/spring-security-authorisation.md) | [Caching and Performance](../12-caching-performance/index.md)
