# Graphs, Dynamic Programming, and Backtracking Coding Questions (Part 1 of 3)

Coding questions on graph traversal, shortest paths, union-find, dynamic programming, and backtracking. For each question, give the brute-force idea first, then the approach that meets the expected complexity.

---


This page is split into 3 parts. Continue to [Part 2](graphs-dp-part-2.md).

## 1. Shortest path in a grid with walls (BFS)

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
In an unweighted grid, every move costs the same, so breadth-first search finds the shortest path. Start at the top-left cell, visit neighbours level by level, and stop when you reach the bottom-right cell. This is O(R * C) time and O(R * C) space. Depth-first search does not guarantee the shortest path.

### Explanation
**Approach 1: BFS with a queue.** O(R * C) time, O(R * C) space.

```java
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;

class GridBfs {
    // '.' is open, '#' is a wall. Returns the number of steps, or -1 if unreachable.
    static int shortestPath(char[][] grid) {
        int rows = grid.length;
        int cols = grid[0].length;
        if (grid[0][0] == '#') {
            return -1;
        }
        int[][] dist = new int[rows][cols];
        for (int[] row : dist) {
            Arrays.fill(row, -1);
        }
        int[] dr = {1, -1, 0, 0};
        int[] dc = {0, 0, 1, -1};
        Queue<int[]> queue = new ArrayDeque<>();
        dist[0][0] = 0;
        queue.add(new int[]{0, 0});
        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            int r = cur[0];
            int c = cur[1];
            if (r == rows - 1 && c == cols - 1) {
                return dist[r][c];
            }
            for (int k = 0; k < 4; k++) {
                int nr = r + dr[k];
                int nc = c + dc[k];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols
                        && grid[nr][nc] == '.' && dist[nr][nc] == -1) {
                    dist[nr][nc] = dist[r][c] + 1;
                    queue.add(new int[]{nr, nc});
                }
            }
        }
        return -1;
    }
}
```

**Approach 2: bidirectional BFS.** Searches from both ends and meets in the middle. It can be faster on large open grids, with the same worst-case complexity.

### When to use / pitfalls
- Mark cells as visited when you enqueue them, not when you dequeue them, or the queue can hold duplicates.
- Check the start and end cells for walls before you begin.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 2. Count the islands in a grid

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Scan every cell. Each time you find an unvisited land cell, you have found a new island; flood-fill everything connected to it so you do not count it again. Both DFS and BFS do this in O(R * C) time.

### Explanation
**Approach 1: recursive DFS, which changes the input.** O(R * C) time, O(R * C) worst-case stack.

```java
class IslandsDfs {
    static int count(char[][] grid) {
        int islands = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == '1') {
                    islands++;
                    sink(grid, r, c);
                }
            }
        }
        return islands;
    }

    private static void sink(char[][] grid, int r, int c) {
        if (r < 0 || c < 0 || r >= grid.length || c >= grid[0].length || grid[r][c] != '1') {
            return;
        }
        grid[r][c] = '0';                    // mark as visited by overwriting
        sink(grid, r + 1, c);
        sink(grid, r - 1, c);
        sink(grid, r, c + 1);
        sink(grid, r, c - 1);
    }
}
```

**Approach 2: BFS with a separate visited array.** O(R * C) time and space, and the input is not changed.

```java
import java.util.ArrayDeque;
import java.util.Deque;

class IslandsBfs {
    static int count(char[][] grid) {
        int rows = grid.length;
        int cols = grid[0].length;
        boolean[][] seen = new boolean[rows][cols];
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        int islands = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] != '1' || seen[r][c]) {
                    continue;
                }
                islands++;
                seen[r][c] = true;
                Deque<int[]> queue = new ArrayDeque<>();
                queue.add(new int[]{r, c});
                while (!queue.isEmpty()) {
                    int[] cur = queue.poll();
                    for (int[] d : dirs) {
                        int nr = cur[0] + d[0];
                        int nc = cur[1] + d[1];
                        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols
                                && grid[nr][nc] == '1' && !seen[nr][nc]) {
                            seen[nr][nc] = true;
                            queue.add(new int[]{nr, nc});
                        }
                    }
                }
            }
        }
        return islands;
    }
}
```

### When to use / pitfalls
- The recursive version can overflow the stack on a large all-land grid. Mention the BFS version for big inputs.
- Ask whether diagonal moves count as connected.

**See also:** [Arrays and strings](arrays-strings-part-1.md)

</details>

---

## 3. Order tasks with dependencies, and detect a cycle

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A dependency graph has a valid order (a topological sort) only if it has no cycle. Kahn's algorithm removes nodes with no incoming edges, one at a time; if it cannot remove all nodes, there is a cycle. Depth-first search with three node states also detects cycles. Both run in O(V + E) time.

### Explanation
**Approach 1: Kahn's algorithm (BFS on in-degrees).** O(V + E) time, O(V + E) space.

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

class TopoKahn {
    // An edge {a, b} means task a must finish before task b.
    static List<Integer> order(int n, int[][] edges) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            adj.add(new ArrayList<>());
        }
        int[] indegree = new int[n];
        for (int[] e : edges) {
            adj.get(e[0]).add(e[1]);
            indegree[e[1]]++;
        }
        Deque<Integer> ready = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (indegree[i] == 0) {
                ready.add(i);
            }
        }
        List<Integer> order = new ArrayList<>();
        while (!ready.isEmpty()) {
            int u = ready.poll();
            order.add(u);
            for (int v : adj.get(u)) {
                if (--indegree[v] == 0) {
                    ready.add(v);
                }
            }
        }
        return order.size() == n ? order : new ArrayList<>();   // empty means a cycle exists
    }
}
```

**Approach 2: DFS with three states.** O(V + E) time, O(V) extra space.

```java
import java.util.List;

class CycleDfs {
    // state: 0 = unvisited, 1 = on the current path, 2 = finished
    static boolean hasCycle(List<List<Integer>> adj) {
        int[] state = new int[adj.size()];
        for (int i = 0; i < adj.size(); i++) {
            if (state[i] == 0 && dfs(i, adj, state)) {
                return true;
            }
        }
        return false;
    }

    private static boolean dfs(int u, List<List<Integer>> adj, int[] state) {
        state[u] = 1;
        for (int v : adj.get(u)) {
            if (state[v] == 1) {
                return true;                // back edge: a cycle
            }
            if (state[v] == 0 && dfs(v, adj, state)) {
                return true;
            }
        }
        state[u] = 2;
        return false;
    }
}
```

### When to use / pitfalls
- A "state 1" node reached again means a back edge, which is a cycle. A "state 2" node is safe to revisit.
- Kahn's algorithm gives the order directly; DFS detects cycles more naturally when you do not need the order.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 4. Shortest paths with non-negative weights (Dijkstra)

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Dijkstra's algorithm repeatedly takes the unvisited node with the smallest known distance from a priority queue and relaxes its outgoing edges. With a binary heap it runs in O((V + E) log V) time. It requires non-negative edge weights. With negative weights, use Bellman-Ford, which is O(V * E).

### Explanation
**Approach 1: priority queue with lazy deletion (Dijkstra).** O((V + E) log V) time.

```java
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;

class Dijkstra {
    // adj.get(u) holds {v, weight} pairs; weights must be non-negative.
    static int[] shortest(List<List<int[]>> adj, int source) {
        int[] dist = new int[adj.size()];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[source] = 0;
        PriorityQueue<int[]> queue = new PriorityQueue<>(Comparator.comparingInt((int[] x) -> x[1]));
        queue.add(new int[]{source, 0});
        while (!queue.isEmpty()) {
            int[] top = queue.poll();
            int u = top[0];
            int d = top[1];
            if (d > dist[u]) {
                continue;                   // stale entry; a shorter path was already found
            }
            for (int[] edge : adj.get(u)) {
                int v = edge[0];
                int candidate = d + edge[1];
                if (candidate < dist[v]) {
                    dist[v] = candidate;
                    queue.add(new int[]{v, candidate});
                }
            }
        }
        return dist;
    }
}
```

**Approach 2: Bellman-Ford.** O(V * E) time, O(V) space. Relax every edge V - 1 times. It handles negative weights and detects negative cycles when one more pass still improves a distance. Describe it in words; implement it if asked.

### When to use / pitfalls
- Java's `PriorityQueue` has no decrease-key operation. Adding duplicates and skipping stale entries is the usual workaround.
- `Integer.MAX_VALUE` as "infinity" overflows if you add to it. Check `dist[u] != MAX` before adding, if you change the code.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---

## 5. Find the edge that creates a cycle (redundant connection)

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Add the edges in order. The first edge whose two endpoints are already connected creates a cycle, and it is the answer. Union-find answers each "are these connected?" check in nearly constant time, so the whole scan is O(E * alpha(V)). A brute-force check with a search per edge is O(E * (V + E)).

### Explanation
**Approach 1: search before each insert.** O(E * (V + E)) time, O(V + E) space.

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

class RedundantBrute {
    // Nodes are numbered 1..n.
    static int[] find(int[][] edges, int n) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i <= n; i++) {
            adj.add(new ArrayList<>());
        }
        for (int[] e : edges) {
            if (reachable(adj, e[0], e[1], n)) {
                return e;                   // already connected: this edge closes a cycle
            }
            adj.get(e[0]).add(e[1]);
            adj.get(e[1]).add(e[0]);
        }
        return new int[0];
    }

    private static boolean reachable(List<List<Integer>> adj, int from, int to, int n) {
        boolean[] seen = new boolean[n + 1];
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(from);
        seen[from] = true;
        while (!stack.isEmpty()) {
            int u = stack.pop();
            if (u == to) {
                return true;
            }
            for (int v : adj.get(u)) {
                if (!seen[v]) {
                    seen[v] = true;
                    stack.push(v);
                }
            }
        }
        return false;
    }
}
```

**Approach 2: union-find.** O(E * alpha(V)) time, O(V) space.

```java
class RedundantUnionFind {
    static int[] find(int[][] edges, int n) {
        int[] parent = new int[n + 1];
        int[] rank = new int[n + 1];
        for (int i = 0; i <= n; i++) {
            parent[i] = i;
        }
        for (int[] e : edges) {
            if (!union(parent, rank, e[0], e[1])) {
                return e;                   // the endpoints were already in one set
            }
        }
        return new int[0];
    }

    private static int root(int[] parent, int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];  // path halving
            x = parent[x];
        }
        return x;
    }

    private static boolean union(int[] parent, int[] rank, int a, int b) {
        int ra = root(parent, a);
        int rb = root(parent, b);
        if (ra == rb) {
            return false;
        }
        if (rank[ra] < rank[rb]) {
            int tmp = ra;
            ra = rb;
            rb = tmp;
        }
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) {
            rank[ra]++;
        }
        return true;
    }
}
```

### When to use / pitfalls
- Union by rank plus path compression gives the near-constant time. Using only one of them still works but is slower.
- Union-find answers connectivity questions, not shortest paths. Do not reach for it when the problem asks for distances.

**See also:** [Graphs and dynamic programming](graphs-dp-part-1.md)

</details>

---


**Next:** [Part 2](graphs-dp-part-2.md)
