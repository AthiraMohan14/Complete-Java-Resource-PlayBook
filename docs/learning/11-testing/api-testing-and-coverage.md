# API Testing and Code Coverage

API tests check the behaviour clients actually depend on: status codes, bodies, headers, and error formats. Contract tests make sure a provider and its consumers agree on that behaviour. Coverage tools tell you which code ran during tests, which is useful but easy to misread. Interviewers ask about these to see whether you can test an HTTP interface, and whether you understand what a coverage number does and does not prove.

## Core concepts

### MockMvc

`MockMvc` sends requests into the Spring MVC stack without starting a server. It is fast, and it exercises routing, serialisation, validation, and exception handling.

```java
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    MockMvc mvc;

    @Test
    void rejectsInvalidEmail() throws Exception {
        mvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Ada\",\"email\":\"not-an-email\",\"age\":30}"))
           .andExpect(status().isBadRequest());
    }

    @Test
    void createsUser() throws Exception {
        mvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Ada\",\"email\":\"ada@example.com\",\"age\":30}"))
           .andExpect(status().isAccepted());
    }
}

@org.springframework.web.bind.annotation.RestController
@org.springframework.web.bind.annotation.RequestMapping("/api/users")
class UserController {
    @org.springframework.web.bind.annotation.PostMapping
    org.springframework.http.ResponseEntity<Void> create(
            @jakarta.validation.Valid @org.springframework.web.bind.annotation.RequestBody UserRequest request) {
        return org.springframework.http.ResponseEntity.accepted().build();
    }
}

record UserRequest(
        @jakarta.validation.constraints.NotBlank String name,
        @jakarta.validation.constraints.Email String email,
        @jakarta.validation.constraints.Min(18) int age) {}
```

The first test sends an invalid email and expects `400`. Once a `@RestControllerAdvice` returns RFC 9457 bodies (see [Exception Handling](../09-spring-boot/exception-handling.md)), add assertions on fields such as `$.status` and `$.title`. In a real suite, use the application's own controller and handler rather than the sketch classes above.

Add `andDo(print())` while debugging to see the request and response.

### REST Assured

REST Assured is a Java DSL for HTTP tests with a `given().when().then()` shape. It runs against a real server (for example, a `RANDOM_PORT` application) and reads well for API-level scenarios.

```java
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

import io.restassured.RestAssured;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OrderApiTest {

    @LocalServerPort
    int port;

    @BeforeEach
    void setUp() {
        RestAssured.port = port;
    }

    @Test
    void createsAndFetchesOrder() {
        given()
            .contentType("application/json")
            .body("{\"item\":\"book\",\"quantity\":1}")
        .when()
            .post("/api/orders")
        .then()
            .statusCode(201);

        given()
        .when()
            .get("/api/orders/42")
        .then()
            .statusCode(200)
            .body("status", equalTo("NEW"));
    }
}
```

The endpoints and response shape are illustrative. Keep the scenario steps realistic and assert on the parts that clients depend on.

### Postman and Newman

Postman collections are useful for exploratory testing and for sharing example requests with other teams. Newman is the command-line runner for those collections, so the same collection can run in CI. Keep collections focused on contract checks, and avoid turning them into the only test layer, because they are harder to version and review than code.

### Contract testing with Spring Cloud Contract

In a contract test, the provider publishes expected interactions and the consumer proves it can handle them. Spring Cloud Contract lets you write contracts (in Groovy or YAML), generate tests for the provider from them, and generate stubs the consumer can run against. This catches breaking changes before deployment, without needing every service running at once.

Use it when several teams depend on one API and you need to avoid integration environments that are always broken. It is a larger investment than MockMvc tests, so start with it where breakage is expensive. Inter-service design is covered in [Inter-Service Communication](../14-microservices/inter-service-communication.md).

### Code coverage with JaCoCo

JaCoCo measures which instructions, branches, lines, methods, and classes run during tests. Common reports show:

- Line coverage: which lines executed
- Branch coverage: which sides of `if` and `switch` decisions ran
- Method and class coverage: which methods and classes were touched

A Maven setup typically uses the `prepare-agent` goal (to instrument tests), the `report` goal (to write HTML and XML), and the `check` goal (to fail the build below a minimum).

```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution><goals><goal>prepare-agent</goal></goals></execution>
    <execution><id>report</id><phase>verify</phase><goals><goal>report</goal></goals></execution>
  </executions>
</plugin>
```

Set minimums carefully. A high number on a critical package is useful; a blanket target for every class can push teams to write tests that only execute code.

### SonarQube and quality gates

SonarQube analyses code for bugs, vulnerabilities, code smells, and coverage (using the JaCoCo report). A quality gate is a set of conditions, such as "no new critical issues" and "coverage on new code at least X", that a branch must meet. Gating on new code is more practical than gating on the whole legacy codebase.

## How it works / Step by step

1. Tests run; JaCoCo's agent records executed instructions.
2. The report is generated and read by SonarQube or the build's `check` goal.
3. API tests start the application (or MockMvc) and send real HTTP requests.
4. Contract tests run against generated stubs or provider verifications.
5. The pipeline fails if a test, contract, or quality gate fails.

## Common pitfalls

- Treating coverage as proof of quality. Coverage shows that code ran; it does not show that the test checked anything. A test with no assertions can give 100% coverage.
- Chasing a coverage number on trivial code such as getters and generated code.
- Testing only the happy path of an API. Error responses (`400`, `404`, `409`) are part of the contract.
- Asserting on whole JSON bodies that include timestamps or generated IDs, which makes tests brittle.
- Relying only on manual Postman runs; they are not regression tests.
- Ignoring branch coverage and checking only line coverage.

!!! tip "Interview tip"
    **Q: Your team has 90% line coverage. Is the test suite good?**
    Not necessarily. Ask how many assertions exist, whether error paths and branches are covered, and whether tests would fail if behaviour changed. Mutation testing (for example, PIT) is one way to check that tests detect real faults. Coverage is a signal of untested code, not a measure of test quality.

## Quick recap

- MockMvc tests the MVC layer quickly; REST Assured tests over HTTP with a readable DSL.
- Test error responses as part of the API contract.
- Spring Cloud Contract checks provider and consumer agreement without full environments.
- JaCoCo reports coverage; SonarQube gates on new code.
- Coverage shows what ran, not whether behaviour was verified.

**See also:** [Integration Testing](integration-testing.md) | [Unit Testing with JUnit 5](unit-testing-junit.md) | [Inter-Service Communication](../14-microservices/inter-service-communication.md)
