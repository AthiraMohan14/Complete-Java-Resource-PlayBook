# Date & Time (java.time)

The `java.time` package, added in Java 8, is the standard API for dates, times, durations, and time zones. Interviewers ask about it to check whether you know why the older `java.util.Date` and `Calendar` classes cause bugs and which type to use for each kind of value.

## Core concepts

### Choosing the right type
Each `java.time` type models one concept. Picking the wrong one is the most common mistake.

| Type | Models | Example value |
|---|---|---|
| `LocalDate` | A date with no time or zone | `2026-10-29` |
| `LocalTime` | A time of day with no date or zone | `14:30` |
| `LocalDateTime` | A date and time with no zone | `2026-10-29T14:30` |
| `ZonedDateTime` | A date and time in a specific zone | `2026-10-29T14:30+05:30[Asia/Kolkata]` |
| `Instant` | A point on the UTC timeline | `2026-10-29T09:00:00Z` |
| `Duration` | A time-based amount (hours, minutes, seconds) | `PT2H30M` |
| `Period` | A date-based amount (years, months, days) | `P1Y2M3D` |
| `ZoneId` | A time zone rule set | `Europe/London` |

All of these types are immutable. Every "change" method returns a new object, so a value can be shared between threads without locks.

### LocalDate, LocalTime, LocalDateTime
```java
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

public class LocalExample {
    public static void main(String[] args) {
        LocalDate due = LocalDate.of(2026, 11, 15);   // months are 1-based: 11 is November
        LocalTime noon = LocalTime.NOON;
        LocalDateTime meeting = LocalDateTime.of(due, noon);

        System.out.println(due.plusDays(10));          // 2026-11-25
        System.out.println(meeting);                    // 2026-11-15T12:00
        System.out.println(due.getDayOfWeek());         // SUNDAY
    }
}
```

`LocalDate.of` takes a 1-based month, unlike the legacy API, which used 0-based months. This is one of the easiest things to get wrong when migrating code.

### Instant and ZonedDateTime
`Instant` is the right type for machine timestamps: logs, database `created_at` values, and events. `ZonedDateTime` is for showing a time to a person in their zone.

```java
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;

public class TimestampExample {
    public static void main(String[] args) {
        Instant now = Instant.now();                                  // always UTC
        ZonedDateTime local = now.atZone(ZoneId.of("Asia/Kolkata"));  // same moment, local view
        System.out.println(now);
        System.out.println(local);
    }
}
```

Zone IDs are region names such as `Europe/Paris`, not offsets such as `+01:00`. Region names follow daylight-saving rules; fixed offsets do not.

### Duration and Period
`Duration` measures elapsed time in seconds and nanoseconds. `Period` measures calendar amounts, which stay correct across month lengths and daylight-saving changes.

```java
import java.time.Duration;
import java.time.LocalDate;
import java.time.Period;

public class AmountExample {
    public static void main(String[] args) {
        Duration d = Duration.ofMinutes(150);
        System.out.println(d);                    // PT2H30M
        System.out.println(d.toHours());          // 2

        Period p = Period.between(LocalDate.of(2024, 1, 31), LocalDate.of(2026, 3, 1));
        System.out.println(p);                    // P2Y1M1D
    }
}
```

Use `Duration` to time code: `Duration.between(start, end)` with two `Instant` values. Do not use `Period` for elapsed time; `Period.ofDays(1)` is not always 24 hours.

### DateTimeFormatter
`DateTimeFormatter` parses and formats values. Built-in constants cover ISO formats; a pattern covers the rest.

```java
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class FormatExample {
    public static void main(String[] args) {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd MMM yyyy");
        LocalDate d = LocalDate.parse("2026-10-29");          // ISO format by default
        System.out.println(d.format(fmt));                    // 29 Oct 2026
        System.out.println(LocalDate.parse("01 Jan 2027", fmt));
    }
}
```

`DateTimeFormatter` is immutable and thread-safe, so a single constant can be shared across the application. Use `yyyy` for the year and `uuuu` if you need a proleptic year that works with negative values; `yyyy` is the common choice in application code.

### Legacy types: Date, Calendar, SimpleDateFormat
`java.util.Date`, `java.util.Calendar`, and `java.text.SimpleDateFormat` are mutable and were designed before `java.time`. Known problems:

- `Date` mixes a timestamp with a default time zone, so a `Date` printed on one server can show a different wall-clock time on another.
- `Date.getMonth()` and `Calendar.MONTH` are 0-based (January is 0). `Date.getYear()` is years since 1900. These are easy to misread.
- `Calendar` objects are mutable; passing one to another method can change it unexpectedly.
- `SimpleDateFormat` is not thread-safe. Sharing one instance between threads can corrupt parsed results.

Convert between the two worlds only at the boundary: `date.toInstant()` and `Date.from(instant)`.

```java
import java.util.Date;

public class LegacyBridge {
    public static void main(String[] args) {
        Date legacy = new Date();
        java.time.Instant instant = legacy.toInstant();   // legacy -> java.time
        Date back = Date.from(instant);                    // java.time -> legacy
        System.out.println(instant + " " + back);
    }
}
```

## How it works / Step by step

1. Decide what the value means: a calendar date, a clock time, a moment on the timeline, or a length of time.
2. Store machine timestamps as `Instant` (UTC) or as a database type that maps to it.
3. Convert to `ZonedDateTime` or `LocalDateTime` only when you show or read values for a user in a known zone.
4. Use `Duration` for elapsed time and `Period` for calendar offsets.
5. Format and parse with a shared `DateTimeFormatter` constant, and always name the zone or offset when data crosses a system boundary.

## Common pitfalls

- Using `LocalDateTime` for a moment in time. It has no zone, so the same value means different instants on different servers.
- Calling `LocalDate.of(2026, 0, 1)` expecting January. `java.time` months start at 1.
- Using `ZoneOffset` or a fixed `+05:30` where a region such as `Asia/Kolkata` is needed. Offsets do not follow daylight-saving changes.
- Adding `Period.ofDays(1)` to a `ZonedDateTime` and expecting exactly 24 hours. Days are calendar days; use `Duration` for exact time.
- Sharing a `SimpleDateFormat` between threads. Use `DateTimeFormatter` instead.
- Parsing with `yy` (two-digit year) without checking the century rule.

!!! tip "Interview tip"
    **Q: Why is `java.time` better than `java.util.Date`?**
    `java.time` types are immutable, cover the different kinds of time (local date, zoned time, instant, duration) as separate types, use 1-based months, and separate time zone rules from the value. `Date` is mutable, mixes a moment with a default zone, uses 0-based months, and is paired with the non-thread-safe `SimpleDateFormat`. Store instants in UTC and convert to zones only for display.

## Quick recap

- Use `LocalDate` and `LocalDateTime` for values without a zone, `Instant` for timestamps, and `ZonedDateTime` for zoned display.
- `Duration` measures exact elapsed time; `Period` measures calendar amounts.
- `java.time` types are immutable and their months are 1-based.
- `DateTimeFormatter` is thread-safe; `SimpleDateFormat` is not.
- `Date` and `Calendar` are legacy: use them only at integration boundaries via `toInstant()` and `Date.from()`.

**See also:** [Java Tools & Utilities](java-tools-utilities.md), [Learning index](../index.md)
