# Spring Data JPA

Spring Data JPA removes most of the boilerplate of data access. You declare a repository interface, and Spring generates the implementation at startup, including queries derived from method names. Interviewers ask about it to see whether you know what the framework generates, where its limits are, and how to paginate and filter safely.

## Core concepts

### The repository hierarchy

Spring Data defines a family of repository interfaces:

| Interface | Adds |
|---|---|
| `Repository<T, ID>` | A marker with no methods |
| `CrudRepository<T, ID>` | `save`, `findById`, `findAll`, `delete`, `count` |
| `PagingAndSortingRepository<T, ID>` | `findAll(Sort)` and `findAll(Pageable)` |
| `JpaRepository<T, ID>` | JPA-specific methods such as `flush`, `saveAndFlush`, batch deletes |

Declare an interface and Spring provides the implementation:

```java
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByStatus(String status);

    Optional<Order> findFirstByStatusOrderByIdDesc(String status);

    long countByStatus(String status);

    void deleteByStatus(String status);      // derived delete: runs inside a transaction
}
```

`Order` here is the entity from [JPA and Hibernate](jpa-hibernate.md). The interface has no implementation class; Spring creates a proxy at startup.

### Derived query methods

Spring parses method names into queries. The grammar uses prefixes such as `findBy`, `readBy`, `countBy`, `existsBy`, and `deleteBy`, with property names, operators (`And`, `Or`, `Between`, `LessThan`, `Like`, `IsNull`), and modifiers (`OrderBy`, `First`, `Top`, `Distinct`).

```java
import java.util.List;

class Order { }   // the entity from earlier in this chapter

interface OrderRepository {
    List<Order> findByStatusAndTotalGreaterThan(String status, long total);
    boolean existsByCustomerIdAndStatus(Long customerId, String status);
}
```

Names that get long are a sign to switch to `@Query`. The method name is validated at startup, so a typo in a property name fails the application early.

### Custom queries with @Query

```java
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface OrderQueries extends JpaRepository<Order, Long> {

    @Query("select o from Order o join fetch o.lines where o.status = :status")
    List<Order> findWithLines(@Param("status") String status);

    @Query(value = "select * from orders where created_on < :cutoff", nativeQuery = true)
    List<Order> findOlderThan(@Param("cutoff") java.time.LocalDate cutoff);

    @Modifying
    @Query("update Order o set o.status = :status where o.id = :id")
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
```

`@Modifying` is needed for `UPDATE` and `DELETE` JPQL, and the method runs in a transaction. The return value is the number of affected rows.

### Specifications for dynamic queries

When filters are optional, combining derived methods becomes unmanageable. A `Specification` builds a `WHERE` clause from parts. The repository must extend `JpaSpecificationExecutor`.

```java
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.util.ArrayList;
import java.util.List;

public interface OrderSearch extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {

    static Specification<Order> hasStatus(String status) {
        return (root, query, cb) -> status == null ? null : cb.equal(root.get("status"), status);
    }
}
```

Combine with `Specification.where(...)`, `.and(...)`, and `.or(...)`. A `null` predicate is ignored by Spring Data when combined this way, which keeps optional filters simple. Pass the result to `findAll(Specification, Pageable)`.

### Named queries

`@NamedQuery` on an entity defines a JPQL query by name, which the repository finds by convention (`Order.findByStatus` style names). They are validated at startup. Most teams prefer `@Query` on the repository because the query sits next to the method that uses it.

### Pagination and sorting

Use `Pageable` for pages and `Sort` for ordering. `Page<T>` includes the total count, which costs an extra `COUNT` query; `Slice<T>` avoids it when you only need "has next".

```java
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;

public class OrderPaging {
    static Pageable firstTen() {
        return PageRequest.of(0, 10, Sort.by(Sort.Direction.DESC, "id"));
    }
}
```

```java
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

// In the repository interface
Page<Order> findByStatus(String status, Pageable pageable);
```

Sorting on a property that is not indexed in a large table is slow. Deep pages with large offsets are slow for the same reason described in [Query Optimisation](../06-databases-sql/query-optimisation.md).

### Projections

A projection returns only the fields you need, avoiding full entity loading.

```java
// Interface projection: Spring implements it from the getters
public interface OrderSummary {
    Long getId();
    String getStatus();
}
```

```java
import java.util.List;

interface OrderSummary {
    String getStatus();
}

interface OrderSummaryRepository {
    List<OrderSummary> findByStatus(String status);
}
```

Class-based (DTO) projections and dynamic projections are also supported. See [DTO Mapping](dto-mapping.md).

## How it works / Step by step

At application startup:

1. Spring scans for repository interfaces and creates a proxy for each.
2. Derived methods are parsed into JPQL or criteria queries; `@Query` strings are validated.
3. At call time, the proxy runs the query inside a transaction (read-only for query methods by default in Spring Data, and read-write for save and delete).
4. Results are converted to entities or projections.

## Common pitfalls

- Assuming a derived method name is always clear. Long names are hard to read and review.
- Forgetting `@Modifying` on an update query, which causes an error at runtime.
- Using `Page` where `Slice` would avoid an extra count query.
- Returning entities from a controller, which exposes lazy associations and internal fields (see [DTO Mapping](dto-mapping.md)).
- Calling `deleteBy...` without a transaction, or expecting it to load and delete efficiently in bulk. Derived deletes load each entity first.
- Building JPQL strings by concatenation with user input.

!!! tip "Interview tip"
    **Q: How does Spring Data create a repository implementation without you writing one?**
    At startup, Spring creates a dynamic proxy for each repository interface. The proxy routes calls to a generic implementation for CRUD methods, and parses derived method names and `@Query` annotations into queries. You write the interface; the framework provides the class.

## Quick recap

- `JpaRepository` provides CRUD and paging; you declare the interface only.
- Derived methods are parsed from names; `@Query` handles complex queries.
- `@Modifying` marks update and delete queries.
- `Specification` builds optional filters without a combinatorial explosion of methods.
- `Page` costs an extra count; `Slice` does not. Projections load only the fields you need.

**See also:** [JPA and Hibernate](jpa-hibernate.md), [DTO Mapping](dto-mapping.md), [JDBC](jdbc.md)
