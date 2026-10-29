# Regular Expressions

A regular expression is a compact pattern that describes a set of strings. Developers use them for validation, searching logs, extracting fields, and rewriting text. Interviewers ask about them to check that you know the syntax, can escape correctly in Java string literals, and understand the performance traps.

## Core concepts

### Character classes

A character class matches one character from a set.

| Pattern | Matches |
|---------|---------|
| `.` | any character except a line terminator (unless the DOTALL flag is set) |
| `\w`, `\d`, `\s` | a word character (letters, digits, underscore), a digit, a whitespace character |
| `\W`, `\D`, `\S` | the opposite of the three above |
| `[abc]` | `a`, `b`, or `c` |
| `[^abc]` | any character except `a`, `b`, or `c` |
| `[a-g]` | any character from `a` to `g` |

In Java, `\w` and `\d` match only ASCII characters by default. Use the `UNICODE_CHARACTER_CLASS` flag if you need Unicode-aware classes.

### Anchors and boundaries

Anchors match a position rather than a character.

- `^` matches the start of the input, and `$` the end. With the `MULTILINE` flag they match at line boundaries.
- `\b` matches a word boundary, and `\B` matches a position that is not a boundary.

`^abc$` matches only the complete string `abc`. `\bcat\b` matches `cat` in "a cat sat" but not in "concatenate".

### Escaping

Characters with special meaning, such as `.`, `*`, `+`, `?`, `(`, `)`, `[`, `{`, `\`, `^`, `$`, and `|`, are escaped with a backslash to match them literally. Control characters are written as `\t`, `\n`, and `\r`.

In Java source, each backslash in the pattern must itself be escaped in the string literal. The pattern `\d+` is written `"\\d+"`.

### Groups and backreferences

- `(abc)` is a capturing group; its match is available by number.
- `(?<name>abc)` is a named capturing group; it is available by name in Java.
- `(?:abc)` is a non-capturing group; it groups without storing the match.
- `\1` refers back to the text matched by group 1, so `(\w)\1` finds a doubled letter such as "ll".

### Lookaround

Lookaround checks what comes before or after a position without consuming it.

- `(?=abc)` is a positive lookahead: the text ahead must match `abc`.
- `(?!abc)` is a negative lookahead: the text ahead must not match `abc`.
- `(?<=abc)` and `(?<!abc)` are the lookbehind equivalents. Java supports bounded lookbehind only.

A common use is checking several independent conditions at once. The pattern `(?=.*\d)(?=.*[a-z]).{8,}` requires at least eight characters, one digit, and one lowercase letter.

### Quantifiers

| Pattern | Meaning |
|---------|---------|
| `a*` | zero or more |
| `a+` | one or more |
| `a?` | zero or one |
| `a{5}` | exactly five |
| `a{2,}` | two or more |
| `a{1,3}` | one to three |

Quantifiers are **greedy** by default: they take as much as possible and give back only when needed. Adding `?` makes them **lazy**, matching as little as possible. `<.+>` on `<a><b>` matches the whole string; `<.+?>` matches `<a>` alone.

### Alternation

`|` matches either side. `cat|dog` matches either word. Alternation has the lowest precedence, so `^cat|dog$` means "starts with cat, or ends with dog". Use a group to limit its scope: `^(cat|dog)$`.

## Using regex in Java

The `java.util.regex` package provides two main classes:

- `Pattern` holds a compiled regex. Compile it once and reuse it, because compilation has a cost.
- `Matcher` runs a pattern against a particular input.

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RegexDemo {
    private static final Pattern ORDER_ID = Pattern.compile("ORD-(?<year>\\d{4})-([A-Z]{2})");

    public static void main(String[] args) {
        String text = "Shipped ORD-2024-AB and ORD-1999-CD";

        Matcher matcher = ORDER_ID.matcher(text);
        while (matcher.find()) {
            System.out.println(matcher.group(0) + " year=" + matcher.group("year"));
        }

        System.out.println("2024".matches("\\d{4}"));     // true: whole input must match
        System.out.println("x2024".matches("\\d{4}"));    // false
        System.out.println("a1b2".replaceAll("\\d", "#")); // a#b#
    }
}
```

Key distinctions:

- `matches()` requires the whole input to match. `find()` looks for the pattern anywhere in the input.
- `String.matches`, `replaceAll`, and `split` compile a new `Pattern` on each call. Fine for one-off use; prefer a precompiled `Pattern` in loops.
- `String.split` takes a regex. `"a.b".split(".")` returns an empty array because `.` matches everything; use `split("\\.")`.

## Common patterns

These are starting points for understanding, not production validators.

```java
import java.util.regex.Pattern;

class Patterns {

    // Simple email shape: not a full RFC 5322 check.
    static final Pattern email = Pattern.compile("^[\\w.+-]+@[\\w-]+\\.[\\w.-]+$");

    // Digits only, optionally with a leading plus and spaces or dashes between groups.
    static final Pattern phone = Pattern.compile("^\\+?[\\d][\\d\\- ]{6,14}\\d$");

    // Scheme and host of an http or https URL.
    static final Pattern url = Pattern.compile("^https?://[^\\s/]+(/\\S*)?$");
}
```

For real validation of email addresses or URLs, use the platform's parser (for example `java.net.URI`) or a library, and keep regex for coarse checks.

## How it works / Step by step

When the regex engine runs a pattern against input, it tries each start position and attempts a match from left to right. For a quantified part it tries the greedy option first and backtracks when the rest of the pattern fails. Most patterns finish in linear time. Nested quantifiers can make the number of attempts explode, which is the basis of catastrophic backtracking.

## Common pitfalls

- **Catastrophic backtracking.** A pattern such as `(a+)+$` applied to `"aaaaaaaaaaaaaaaaaaaaaaaa!"` takes exponential time because the engine tries every way to split the `a`s before failing. Avoid nested quantifiers over the same characters, and bound repetition with `{m,n}`.
- **Forgetting double escaping in Java.** `"\d"` does not compile; `"\\d"` is correct.
- **Assuming `.` matches newlines.** It does not, unless DOTALL is set.
- **Using `find()` where `matches()` was meant.** Validation with `find()` accepts input that merely contains a valid part.
- **Greedy matches that swallow too much.** Use a lazy quantifier or a negated class: `"[^\"]*"` is more precise than `".*"` for quoted strings.
- **Using a regex to parse nested structures.** HTML, JSON, and nested brackets need a real parser.
- **Recompiling in a loop.** Store the `Pattern` in a `static final` field.

!!! tip "Interview tip"
    **Q: Why does `"a.b".split(".")` return an empty array?**
    `split` takes a regex, and an unescaped `.` matches any character. Every character is a delimiter, so all the pieces are empty and trailing empty strings are removed. Escape the dot: `split("\\.")`.

## Quick recap

- Character classes match one character; anchors match positions.
- Groups capture; `(?:...)` groups without capturing; lookarounds test context without consuming it.
- Quantifiers are greedy by default; a trailing `?` makes them lazy.
- In Java, escape each backslash in the string literal and compile reusable patterns once.
- `matches()` checks the whole input; `find()` searches for a match inside it.
- Nested quantifiers can cause catastrophic backtracking.

**See also:** [Web Fundamentals](web-fundamentals.md), [Software Design Principles](software-design-principles.md), [Secure Coding and Supply Chain](../10-security/secure-coding-and-supply-chain.md)
