# Graphs

Graphs model things that connect: road networks, dependency lists, social links, and task schedules. Interviewers ask about graphs because one model covers many problems, and the choice between BFS, DFS, Dijkstra, and Union-Find shows whether you understand the structure of the input.

## Core concepts

### Representations

A graph has vertices (V) and edges (E). Two common representations:

| Representation | Space | Check if edge `u-v` exists | Best for |
|---|---|---|---|
| Adjacency list | O(V + E) | O(degree of u) | Sparse graphs (most real graphs) |
| Adjacency matrix | O(V²) | O(1) | Dense graphs, Floyd-Warshall |

```java
import java.util.*;

public class GraphBuild {
    public static void main(String[] args) {
        int n = 4;
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            adj.add(new ArrayList<>());
        }
        int[][] edges = {{0, 1}, {1, 2}, {2, 3}};
        for (int[] e : edges) {
            adj.get(e[0]).add(e[1]);
            adj.get(e[1]).add(e[0]);   // undirected: add both directions
        }
        System.out.println(adj);   // [[1], [0, 2], [1, 3], [2]]
    }
}
```

### BFS and DFS

Both visit every reachable vertex in O(V + E). BFS uses a queue and finds shortest paths in unweighted graphs. DFS uses a stack (or recursion) and suits connectivity, cycle detection, and topological ordering.

```java
import java.util.*;

public class Bfs {
    static int[] distances(List<List<Integer>> adj, int src) {
        int[] dist = new int[adj.size()];
        Arrays.fill(dist, -1);          // -1 means "not visited yet"
        Deque<Integer> queue = new ArrayDeque<>();
        dist[src] = 0;
        queue.add(src);
        while (!queue.isEmpty()) {
            int u = queue.poll();
            for (int v : adj.get(u)) {
                if (dist[v] == -1) {
                    dist[v] = dist[u] + 1;
                    queue.add(v);
                }
            }
        }
        return dist;
    }
}
```

Mark a vertex when you enqueue it, not when you dequeue it. Otherwise the same vertex can be queued many times.

### Shortest paths

| Algorithm | Handles negative weights? | Complexity | Typical use |
|---|---|---|---|
| BFS | n/a (unit weights) | O(V + E) | Shortest path, unweighted |
| Dijkstra | No | O((V + E) log V) with a binary heap | Single source, non-negative weights |
| Bellman-Ford | Yes; detects negative cycles | O(V × E) | Single source, negative edges |
| Floyd-Warshall | Yes; detects negative cycles | O(V³) | All pairs, small graphs |

Dijkstra with a `PriorityQueue` (lazy deletion: skip stale entries):

```java
import java.util.*;

public class Dijkstra {
    static final long INF = Long.MAX_VALUE / 4;

    // adj.get(u) holds {v, weight} pairs; weights must be non-negative
    static long[] shortest(List<List<int[]>> adj, int src) {
        long[] dist = new long[adj.size()];
        Arrays.fill(dist, INF);
        dist[src] = 0;
        PriorityQueue<long[]> pq = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));
        pq.add(new long[]{0, src});
        while (!pq.isEmpty()) {
            long[] cur = pq.poll();
            int u = (int) cur[1];
            if (cur[0] > dist[u]) {
                continue;                       // stale entry, a shorter path was already found
            }
            for (int[] edge : adj.get(u)) {
                int v = edge[0];
                long nd = dist[u] + edge[1];
                if (nd < dist[v]) {
                    dist[v] = nd;
                    pq.add(new long[]{nd, v});
                }
            }
        }
        return dist;
    }
}
```

Bellman-Ford relaxes every edge V - 1 times. If a V-th pass still relaxes an edge, a negative cycle is reachable. Floyd-Warshall is a triple loop over k, i, j; it is short enough to write in an interview when V is small:

```java
static void floyd(long[][] d) {          // d[i][i] = 0, d[i][j] = INF when there is no edge
    int n = d.length;
    for (int k = 0; k < n; k++)
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                d[i][j] = Math.min(d[i][j], d[i][k] + d[k][j]);
}
```

With `INF = Long.MAX_VALUE / 4`, the sum never overflows, so the code needs no extra checks.

### Minimum spanning trees

A spanning tree connects all vertices with V - 1 edges. The minimum spanning tree (MST) has the smallest total weight.

- **Kruskal:** sort edges by weight, add each edge that joins two different components (use Union-Find). O(E log E).
- **Prim:** grow one tree from a start vertex, always taking the cheapest edge that leaves the tree (use a priority queue). O(E log V) with a binary heap.

### Union-Find (disjoint set union)

Union-Find answers "are these two vertices in the same component?" in near-constant time. Path compression and union by rank make each operation almost O(1) (inverse Ackermann).

```java
public class DisjointSet {
    private final int[] parent;
    private final int[] rank;

    public DisjointSet(int n) {
        parent = new int[n];
        rank = new int[n];
        for (int i = 0; i < n; i++) {
            parent[i] = i;
        }
    }

    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);   // path compression
        }
        return parent[x];
    }

    public boolean union(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra == rb) {
            return false;                  // already connected: adding this edge would make a cycle
        }
        if (rank[ra] < rank[rb]) {
            int t = ra; ra = rb; rb = t;
        }
        parent[rb] = ra;
        if (rank[ra] == rank[rb]) {
            rank[ra]++;
        }
        return true;
    }
}
```

### Topological sort and cycle detection

A topological order exists only for a directed acyclic graph (DAG). Kahn's algorithm removes vertices with in-degree 0 and reports a cycle if some vertices are never removed.

```java
import java.util.*;

public class TopoSort {
    // Returns an order, or an empty list if the graph has a cycle
    static List<Integer> order(int n, int[][] edges) {
        List<List<Integer>> adj = new ArrayList<>();
        int[] indeg = new int[n];
        for (int i = 0; i < n; i++) {
            adj.add(new ArrayList<>());
        }
        for (int[] e : edges) {
            adj.get(e[0]).add(e[1]);
            indeg[e[1]]++;
        }
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            if (indeg[i] == 0) q.add(i);
        }
        List<Integer> result = new ArrayList<>();
        while (!q.isEmpty()) {
            int u = q.poll();
            result.add(u);
            for (int v : adj.get(u)) {
                if (--indeg[v] == 0) q.add(v);
            }
        }
        return result.size() == n ? result : List.of();
    }
}
```

For undirected graphs, cycle detection uses DFS with a parent check (or Union-Find: an edge that joins two vertices already in one set closes a cycle). For directed graphs, DFS with three colours (unvisited, in progress, done) finds back edges.

### Strongly connected components

In a directed graph, a strongly connected component (SCC) is a maximal set of vertices that can all reach each other. Tarjan's and Kosaraju's algorithms find SCCs in O(V + E). Know what they compute; you rarely need to write them from memory in an interview.

### Bipartite graphs and 0/1 BFS

A graph is bipartite if its vertices can be split into two sets with edges only between sets. Colour vertices with BFS or DFS; a conflict means it is not bipartite. Odd-length cycles break bipartiteness.

0/1 BFS handles graphs whose edge weights are only 0 or 1. Push zero-weight neighbours to the front of a deque and weight-one neighbours to the back. It runs in O(V + E) without a heap.

### Articulation points and bridges

An articulation point is a vertex whose removal increases the number of connected components. A bridge is an edge with the same property. Tarjan's DFS-based algorithm finds both in O(V + E) using discovery times and low-link values. Explain the idea (discovery time, lowest reachable ancestor) before you write any code.

## How it works / Step by step

Choosing an algorithm for a graph problem:

1. Is the graph weighted? If not, use BFS for shortest paths.
2. Are weights non-negative? Use Dijkstra. Negative weights: Bellman-Ford. Need all pairs on a small graph: Floyd-Warshall.
3. Is the question "do these two belong together?" as edges arrive? Use Union-Find.
4. Are there ordering constraints (A before B)? Use topological sort.
5. Do you need every vertex covered with minimum cost? Use Kruskal or Prim.

## Common pitfalls

- Using Dijkstra with negative edge weights. It can return wrong answers without any error.
- Forgetting to add both directions for undirected edges.
- Recursive DFS on a large graph causing `StackOverflowError`. Use an explicit stack or raise the thread stack size.
- Marking visited too late in BFS, which enqueues the same vertex many times.
- Using `int` for path sums that can exceed 2³¹. Use `long`.
- Forgetting disconnected components. Loop over all vertices, not just one source.

!!! tip "Interview tip"
    **Q: How do you find the shortest path in a weighted graph with no negative edges?**
    Dijkstra's algorithm with a min-heap, O((V + E) log V). If the weights are unit, plain BFS is O(V + E). If there are negative edges, switch to Bellman-Ford, and say that it also detects negative cycles.

## Quick recap

- Adjacency lists suit most graphs; matrices suit dense graphs and Floyd-Warshall.
- BFS gives shortest paths for unweighted graphs; DFS handles connectivity and cycles.
- Dijkstra needs non-negative weights; Bellman-Ford handles negative weights.
- Kruskal and Prim both build an MST; Union-Find is the core of Kruskal.
- Topological sort (Kahn's algorithm) works only on DAGs; a leftover vertex means a cycle.

**See also:** [Dynamic Programming](dynamic-programming.md), [Backtracking and Recursion](backtracking-recursion.md), [Greedy, Bit Manipulation and Hashing](greedy-bit-manipulation-hashing.md)
