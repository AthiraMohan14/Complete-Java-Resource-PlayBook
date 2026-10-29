# Linked Lists, Stacks, and Trees Coding Questions (Part 2 of 2)

Continued from [Part 1](linked-lists-trees-part-1.md).

---

## 8. Traverse a binary tree in order, with and without recursion

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
In-order traversal visits left, node, right. The recursive version is O(n) time and O(h) stack space, where h is the height. The iterative version uses an explicit stack and has the same complexity, which avoids stack overflow on deep trees. Pre-order and post-order differ only in when the node is visited.

### Explanation
The examples use this node class:

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}
```

**Approach 1: recursive.** O(n) time, O(h) space.

```java
import java.util.ArrayList;
import java.util.List;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class InorderRecursive {
    static List<Integer> inorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        walk(root, out);
        return out;
    }

    private static void walk(TreeNode node, List<Integer> out) {
        if (node == null) {
            return;
        }
        walk(node.left, out);
        out.add(node.val);
        walk(node.right, out);
    }
}
```

**Approach 2: iterative with a stack.** O(n) time, O(h) space.

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class InorderIterative {
    static List<Integer> inorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {          // go as far left as possible
                stack.push(cur);
                cur = cur.left;
            }
            cur = stack.pop();
            out.add(cur.val);
            cur = cur.right;
        }
        return out;
    }
}
```

### When to use / pitfalls
- `ArrayDeque` does not accept `null` elements; push only non-null nodes, as above.
- Morris traversal does in-order traversal in O(1) extra space by threading the tree temporarily. Mention it if the interviewer asks for constant space.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 9. Level-order traversal and maximum depth

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Breadth-first search with a queue visits the tree one level at a time; the queue size at the start of each pass is the number of nodes on that level. Maximum depth can be found recursively in O(n) time and O(h) space, or by counting BFS levels in O(n) time and O(w) space, where w is the widest level.

### Explanation
**Approach 1: level-order traversal with a queue.** O(n) time, O(w) space.

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Queue;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class LevelOrder {
    static List<List<Integer>> levels(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) {
            return result;
        }
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) {
                    queue.add(node.left);
                }
                if (node.right != null) {
                    queue.add(node.right);
                }
            }
            result.add(level);
        }
        return result;
    }
}
```

**Approach 2: recursive maximum depth.** O(n) time, O(h) space.

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class MaxDepth {
    static int maxDepth(TreeNode root) {
        if (root == null) {
            return 0;
        }
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }
}
```

The BFS version of maximum depth is simply `LevelOrder.levels(root).size()`.

### When to use / pitfalls
- Read `queue.size()` before the inner loop; the queue grows during the loop.
- Use `poll()` rather than `remove()` to get `null` on an empty queue instead of an exception.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 10. Validate a binary search tree

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Every node must lie strictly between bounds set by its ancestors. Pass a lower and an upper bound down the recursion; this is O(n) time and O(h) space. Alternatively, an in-order traversal of a valid BST is strictly increasing, which gives the same complexity.

### Explanation
**Approach 1: pass bounds down.** O(n) time, O(h) space.

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class ValidBstBounds {
    static boolean isValid(TreeNode root) {
        return check(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private static boolean check(TreeNode node, long low, long high) {
        if (node == null) {
            return true;
        }
        if (node.val <= low || node.val >= high) {
            return false;
        }
        return check(node.left, low, node.val) && check(node.right, node.val, high);
    }
}
```

**Approach 2: in-order values must increase.** O(n) time, O(h) space. Uses `InorderIterative.inorder` from question 8.

```java
import java.util.ArrayList;
import java.util.List;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class ValidBstInorder {
    static boolean isValid(TreeNode root) {
        List<Integer> values = new ArrayList<>();
        collect(root, values);   // in-order walk
        for (int i = 1; i < values.size(); i++) {
            if (values.get(i - 1) >= values.get(i)) {
                return false;
            }
        }
        return true;
    }

    private static void collect(TreeNode node, List<Integer> out) {
        if (node == null) {
            return;
        }
        collect(node.left, out);
        out.add(node.val);
        collect(node.right, out);
    }
}
```

### When to use / pitfalls
- Checking only each node against its direct children is a common wrong answer. A value deep in the left subtree can still be larger than the root.
- Use `long` bounds so that `Integer.MIN_VALUE` and `Integer.MAX_VALUE` values are handled.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 11. Lowest common ancestor of two nodes

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
For a general binary tree, recurse into both subtrees; if the two targets are found on different sides, the current node is the lowest common ancestor. This is O(n) time and O(h) space. For a binary search tree, walk down from the root using the values: the first node that splits the two values is the answer, in O(h) time and O(1) space.

### Explanation
**Approach 1: recursive search.** O(n) time, O(h) space.

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class LcaGeneral {
    static TreeNode lca(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) {
            return root;
        }
        TreeNode left = lca(root.left, p, q);
        TreeNode right = lca(root.right, p, q);
        if (left != null && right != null) {
            return root;                    // p and q are on different sides
        }
        return left != null ? left : right;
    }
}
```

**Approach 2: use the BST ordering.** O(h) time, O(1) space.

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class LcaBst {
    static TreeNode lca(TreeNode root, TreeNode p, TreeNode q) {
        TreeNode cur = root;
        while (cur != null) {
            if (p.val < cur.val && q.val < cur.val) {
                cur = cur.left;
            } else if (p.val > cur.val && q.val > cur.val) {
                cur = cur.right;
            } else {
                return cur;                 // the values split here, or one equals cur
            }
        }
        return null;
    }
}
```

### When to use / pitfalls
- The general version must search the whole tree when the nodes are far apart; it cannot stop early.
- Clarify whether both nodes are guaranteed to exist. If not, the answer can be null.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md)

</details>

---

## 12. Serialise and deserialise a binary tree

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Write the tree in pre-order, and write a marker such as `#` for each missing child. Reading the tokens back in the same order rebuilds the tree exactly. Both directions are O(n) time, and the recursive parser uses O(h) stack space. A level-order encoding works too, if you mark missing children at each level.

### Explanation
**Approach 1: pre-order with null markers (recursive).** O(n) time, O(n) space for the string.

```java
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode(int val) {
        this.val = val;
    }
}

class TreeCodec {
    static String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        writeNode(root, sb);
        return sb.toString();
    }

    private static void writeNode(TreeNode node, StringBuilder sb) {
        if (node == null) {
            sb.append("#,");
            return;
        }
        sb.append(node.val).append(',');
        writeNode(node.left, sb);
        writeNode(node.right, sb);
    }

    static TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>(Arrays.asList(data.split(",")));
        return readNode(tokens);
    }

    private static TreeNode readNode(Deque<String> tokens) {
        String token = tokens.poll();
        if (token == null || token.equals("#")) {
            return null;
        }
        TreeNode node = new TreeNode(Integer.parseInt(token));
        node.left = readNode(tokens);
        node.right = readNode(tokens);
        return node;
    }
}
```

**Approach 2: level-order with a queue.** O(n) time, O(n) space. Write each node from a BFS queue and a `#` for each missing child; rebuild by reading the tokens in the same order with a second queue. The code is longer, but the output is easier to read by eye.

### When to use / pitfalls
- Integer values with commas or sign characters need an escape scheme if the values are not plain integers.
- A deep, skewed tree makes the recursive parser use O(n) stack space; mention the iterative option.

**See also:** [Linked lists and trees](linked-lists-trees-part-1.md), [Coding: Java problems](java-coding-problems-part-1.md)

</details>

---

## Quick recap

- Use a dummy node to avoid special cases at the head of a list.
- Floyd's two-pointer method finds cycles and the cycle start in O(1) space.
- A stack handles nesting (brackets) and "next greater" problems.
- Level-order traversal uses a queue and the queue size per level.
- BST checks pass bounds down or rely on in-order ordering.
- For tree problems, state the recursion depth: O(h) on a balanced tree, O(n) on a skewed one.

**See also:** [Arrays and strings](arrays-strings-part-1.md), [Graphs and dynamic programming](graphs-dp-part-1.md), [Stream API problems](stream-api-problems-part-1.md)
