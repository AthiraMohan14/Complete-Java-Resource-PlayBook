# DTOs and Mapping

A DTO (data transfer object) is a plain object that carries data across a boundary, such as between a web layer and a client or between services. Interviewers ask about DTOs to check that you keep persistence entities out of the API, and to see whether you can explain the trade-offs between compile-time and reflection-based mapping.

## Core concepts

### The DTO pattern and its benefits

An entity describes how data is stored: it may have lazy associations, internal IDs, audit fields, and methods that only make sense inside a transaction. Returning entities directly from an API couples clients to the database schema and can trigger lazy loading during JSON serialisation.

A DTO describes what a caller needs:

- **Stable contract:** the API shape does not change when the table changes.
- **No accidental data exposure:** fields such as password hashes or internal flags are simply not in the DTO.
- **No lazy loading surprises:** the DTO holds plain values, so serialisation cannot touch the database.
- **Shaped for the use case:** one endpoint may need three fields from two tables; a DTO carries exactly those.

Java records make DTOs short and immutable:

```java
public record OrderDto(Long id, String status, int lineCount) {
}
```

Records were finalised in Java 16. Their generated constructor, accessors, `equals`, `hashCode`, and `toString` suit DTOs well.

### Manual mapping

Writing the mapping by hand is explicit and easy to test, and it is the right choice for small projects.

```java
import java.util.List;

// Minimal entity and DTO so the example compiles on its own
class Order {
    long getId() { return 1L; }
    String getStatus() { return "NEW"; }
    List<String> getLines() { return List.of(); }
}

record OrderDto(long id, String status, int lineCount) { }

public class OrderMapping {

    static OrderDto toDto(Order order) {
        return new OrderDto(order.getId(), order.getStatus(), order.getLines().size());
    }

    static List<OrderDto> toDtos(List<Order> orders) {
        return orders.stream().map(OrderMapping::toDto).toList();
    }
}
```

`getLines().size()` touches a lazy collection, so call this inside the transaction or load the data with a fetch join. The mapper is where that decision should be visible.

### MapStruct: compile-time mapping

MapStruct generates mapper implementations at compile time through an annotation processor. The generated code is ordinary Java: fast, debuggable, and checked at build time. A mismatch between source and target properties fails the build (or emits a warning, depending on configuration).

```java
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface OrderMapper {

    @Mapping(target = "lineCount", expression = "java(order.getLines().size())")
    OrderDto toDto(Order order);
}
```

MapStruct needs the annotation processor on the compiler path (Maven `annotationProcessorPaths` or the Gradle `annotationProcessor` configuration). The `componentModel = "spring"` option makes the generated class a Spring bean.

### ModelMapper: reflection-based mapping

ModelMapper maps properties at runtime by inspecting names and types. It needs little configuration for simple cases, which makes it quick to start with. The cost is that mistakes surface at runtime, and reflection adds overhead on each call.

```java
import org.modelmapper.ModelMapper;

public class ModelMapperDemo {
    private static final ModelMapper MODEL_MAPPER = new ModelMapper();

    static OrderDto toDto(Order order) {
        return MODEL_MAPPER.map(order, OrderDto.class);
    }
}
```

`ModelMapper` is thread-safe once configured, so keep one instance rather than creating one per call. Note that its property-matching rules can map the wrong field silently when names are similar; test the mapping.

### Choosing between them

| Concern | MapStruct | ModelMapper |
|---|---|---|
| When mapping is checked | Compile time | Runtime |
| Mechanism | Generated plain Java | Reflection |
| Runtime overhead | Very low | Higher |
| Debugging | Read the generated class | Step through reflection |
| Setup for complex rules | Explicit `@Mapping` annotations | Configuration API |
| Silent mismatches | Reported at build time | Possible at runtime |

For performance-sensitive or large APIs, prefer MapStruct. For a small project where a few fields differ, manual mapping is often clearer than either library.

### Performance considerations

- Mapping cost is usually small compared with the database call that loaded the data. Measure before optimising.
- Reflection-based mapping allocates and does lookups per call; at high request rates this shows up in profiles.
- Mapping collections of thousands of entities allocates many objects; consider projections so the database returns only needed columns.
- Keep mapping out of the database transaction when it does not need the database, so connections are released sooner. The exception is lazy fields, which must be read before the transaction closes.

### Projections as an alternative

A JPA constructor expression or a Spring Data DTO projection lets the database return only the columns you need, already in the DTO's shape. This avoids loading whole entities when only a few fields are used.

```java
import jakarta.persistence.EntityManager;
import java.util.List;

// JPQL constructor expression: the query builds the DTO directly
List<OrderDto> rows = entityManager.createQuery(
        "select new com.example.orders.OrderDto(o.id, o.status, size(o.lines)) from Order o",
        OrderDto.class).getResultList();
```

The package name in the query must be the fully qualified name of the DTO. Be aware that `size(o.lines)` runs a count per row unless the database computes it in a subquery; check the SQL.

## How it works / Step by step

Building a response from an entity:

1. The service loads the entity (or a projection) inside a transaction.
2. The mapper converts it to a DTO, reading any lazy data it needs.
3. The transaction ends; the DTO holds only plain values.
4. The controller serialises the DTO to JSON.

For writes, the reverse happens: the request body is validated and mapped to a command or entity, and only then saved.

## Common pitfalls

- Returning entities from controllers, which exposes internal fields and triggers lazy loading during JSON serialisation.
- Mapping lazy associations after the transaction has closed.
- Using ModelMapper in a hot path without measuring.
- Letting MapStruct or ModelMapper silently map a field with a similar name to the wrong one.
- Creating a new ModelMapper instance per request.
- Putting business rules inside the mapper; keep mappers mechanical.

!!! tip "Interview tip"
    **Q: MapStruct or ModelMapper, and why?**
    MapStruct generates plain Java at compile time, so mismatches fail the build and runtime overhead is low. ModelMapper uses reflection at runtime, which is quicker to start with but costs more and can hide mismatches until a test runs. Say which you would pick for a high-traffic API (MapStruct) and why.

## Quick recap

- DTOs decouple the API from the entity model and prevent lazy loading during serialisation.
- Java records are a concise way to write immutable DTOs.
- MapStruct maps at compile time; ModelMapper maps at runtime through reflection.
- Projections let the database return DTO-shaped results directly.
- Map inside the transaction when lazy fields are involved.

**See also:** [JPA and Hibernate](jpa-hibernate.md), [Spring Data JPA](spring-data-jpa.md), [Database Migrations](database-migrations.md)
