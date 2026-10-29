# Collections

The Java Collections Framework holds groups of objects: lists, sets, maps, queues, and deques, plus the ordering and utility classes that go with them. Almost every Java program depends on it, and interviewers use it heavily to test your knowledge of complexity, equality rules, iteration safety, and thread safety.

---

## Topics

### [Collections Overview](collections-overview.md)
**Iterable - Collection - Map - equals - hashCode - immutable factories**
The framework hierarchy, the contracts behind hash-based collections, and the choice of implementation for common tasks.

### [Lists](lists.md)
**ArrayList - LinkedList - Vector - CopyOnWriteArrayList - List.of**
Ordered, index-based collections: how `ArrayList` and `LinkedList` differ, the legacy `Vector`, and the copy-on-write list.

### [Sets and Maps](sets-and-maps.md)
**HashSet - LinkedHashSet - TreeSet - HashMap - LinkedHashMap - TreeMap - ConcurrentHashMap**
Unique elements and key-value mappings, the hash and tree variants, insertion order, and the special-purpose maps.

### [Queues and Deques](queues-and-deques.md)
**PriorityQueue - ArrayDeque - LinkedList - offer and poll - stack and queue use**
First-in-first-out and priority ordering, double-ended queues, and why `ArrayDeque` replaces `Stack` and `LinkedList` for most stacks and queues.

### [Ordering: Comparable and Comparator](ordering-comparable-comparator.md)
**Comparable - Comparator - SortedSet - SortedMap - NavigableMap - consistency with equals**
Natural and custom ordering, building comparators with `Comparator.comparing`, and the sorted and navigable collection interfaces.

### [Iterators and Utilities](iterators-and-utilities.md)
**Iterator - fail-fast - fail-safe - ConcurrentModificationException - Collections**
How iteration works, why modifying a collection during iteration throws, weakly consistent iterators, and the `Collections` helper class.
