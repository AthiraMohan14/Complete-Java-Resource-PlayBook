# Java-Specific Coding Problems (Part 3 of 3)

Continued from [Part 2](java-coding-problems-part-2.md).

---

## 11. Transfer money between two accounts without deadlock

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A deadlock happens when one transfer locks A then B while another locks B then A. Lock the two accounts in a fixed global order, such as by account ID, so every thread takes them in the same sequence. An alternative is `tryLock` with a timeout, which backs off and retries instead of waiting forever.

### Explanation
**Approach 1: lock ordering.**

```java
import java.util.concurrent.locks.ReentrantLock;

class Account {
    final long id;
    long balance;
    final ReentrantLock lock = new ReentrantLock();

    Account(long id, long balance) {
        this.id = id;
        this.balance = balance;
    }
}

class Bank {
    static void transfer(Account from, Account to, long amount) {
        Account first = from.id < to.id ? from : to;      // always the lower id first
        Account second = first == from ? to : from;
        first.lock.lock();
        try {
            second.lock.lock();
            try {
                if (from.balance < amount) {
                    throw new IllegalStateException("insufficient funds");
                }
                from.balance -= amount;
                to.balance += amount;
            } finally {
                second.lock.unlock();
            }
        } finally {
            first.lock.unlock();
        }
    }
}
```

**Approach 2: `tryLock` with a timeout and back-off.**

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

class Account {
    final ReentrantLock lock = new ReentrantLock();
    long balance;
}

class BankTryLock {
    static boolean transfer(Account from, Account to, long amount) throws InterruptedException {
        while (true) {
            if (from.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                try {
                    if (to.lock.tryLock(50, TimeUnit.MILLISECONDS)) {
                        try {
                            if (from.balance < amount) {
                                return false;
                            }
                            from.balance -= amount;
                            to.balance += amount;
                            return true;
                        } finally {
                            to.lock.unlock();
                        }
                    }
                } finally {
                    from.lock.unlock();
                }
            }
            Thread.sleep(5);                        // back off, then try again
        }
    }
}
```

### When to use / pitfalls
- Approach 2 can livelock if two threads keep backing off in step. Add random jitter to the sleep, and cap the retries.
- A transfer to the same account needs care: with approach 1 the same lock is taken twice, which `ReentrantLock` allows. Decide whether to reject it.
- In a real system, prefer a database transaction with a consistent update order over in-memory locks.

**See also:** [Advanced Java and concurrency](../technical/advanced-java-concurrency-part-1.md), [Data and persistence](../technical/data-and-persistence-part-1.md)

</details>

---

## 12. Parse ISO dates and count the days between them

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `java.time`, not `java.util.Date`. `LocalDate.parse` reads ISO-8601 dates (`yyyy-MM-dd`), and `ChronoUnit.DAYS.between` returns the number of days between two dates. Do not use `Period.getDays()` for this: it returns only the day part of a period, not the total number of days.

### Explanation
**Approach 1: `ChronoUnit.DAYS.between`.** O(1) time.

```java
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

class DaysBetween {
    static long days(String start, String end) {
        LocalDate a = LocalDate.parse(start);      // ISO-8601: 2026-01-31
        LocalDate b = LocalDate.parse(end);
        return ChronoUnit.DAYS.between(a, b);
    }
}
```

**Approach 2: epoch days.** O(1) time. Useful when you already work with epoch-day numbers.

```java
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

class DaysBetweenCustomFormat {
    static long days(String start, String end) {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy");
        LocalDate a = LocalDate.parse(start, fmt);
        LocalDate b = LocalDate.parse(end, fmt);
        return b.toEpochDay() - a.toEpochDay();
    }
}
```

### When to use / pitfalls
- `Period.between(a, b).getDays()` returns the days component after months and years are removed. Use `ChronoUnit.DAYS` for a total.
- Time zones matter for instants and date-times. `LocalDate` has none, which is what you want for calendar dates.
- Patterns such as `dd/MM/yyyy` are not the same as `MM/dd/yyyy`. Use an explicit formatter, never a guess.
- `java.util.Date` and `Calendar` are legacy; mention them only to say you would avoid them.

**See also:** [Core Java](../technical/core-java-part-1.md)

</details>

---

## Quick recap

- LRU: a `LinkedHashMap` in access order is the short answer; a `HashMap` with a doubly linked list shows the mechanics.
- Singletons: holder idiom or enum; double-checked locking needs `volatile`.
- Blocking hand-off: prefer `BlockingQueue`; know the lock-and-condition version.
- Parsing: recursive descent for expressions; split at the first delimiter for simple formats.
- Immutability: final fields, defensive copies, and records.
- Equality: override both `equals` and `hashCode`, using the same fields.
- Concurrency: fixed lock order prevents deadlock; parallel streams need stateless pipelines.
- Dates: `java.time` with `ChronoUnit` for totals.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Stream API problems](stream-api-problems-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md)
