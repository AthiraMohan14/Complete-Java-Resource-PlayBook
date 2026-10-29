# Trees

A tree is a connected structure with no cycles, and a binary tree gives each node at most two children. Trees appear in interviews because recursion fits them naturally, and because the same few techniques (traversal, passing information up from children, and tracking a best answer) solve a wide range of problems. Knowing the cost in terms of tree height, not just node count, is what separates a good answer from a complete one.

## Core concepts

### Node structure
The examples on this page assume the node class below, nested in a `TreeDemo` class. The examples also use `java.util` collections, so add the imports you need.

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Queue;

public class TreeDemo {

    static final class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;

        TreeNode(int val) {
            this.val = val;
        }
    }
}
```

### Binary search trees
A binary search tree (BST) keeps every value in the left subtree smaller than the node and every value in the right subtree larger. Search, insert, and delete all follow one path from the root, so their cost is O(h), where h is the height. In a balanced tree h is O(log n). In a skewed tree, where each node has one child, h is n and the BST degrades to a linked list.

```java
import java.util.*;

public class BstOps {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static TreeNode insert(TreeNode root, int val) {
        if (root == null) {
            return new TreeNode(val);
        }
        if (val < root.val) {
            root.left = insert(root.left, val);
        } else if (val > root.val) {
            root.right = insert(root.right, val);
        }
        return root;   // duplicates are ignored in this version
    }

    static boolean contains(TreeNode root, int val) {
        TreeNode cur = root;
        while (cur != null) {
            if (val == cur.val) {
                return true;
            }
            cur = (val < cur.val) ? cur.left : cur.right;
        }
        return false;
    }
}
```

Inserting values in sorted order creates a skewed tree, so a plain BST is not safe for sorted input. That is why balanced trees exist.

### Traversals
There are four standard orders. Depth-first traversals are pre-order, in-order, and post-order. Breadth-first traversal is level-order.

| Order | Visit sequence | Typical use |
|---|---|---|
| Pre-order | Node, left, right | Copying a tree, serialisation |
| In-order | Left, node, right | Sorted output of a BST |
| Post-order | Left, right, node | Deleting a tree, computing values from children |
| Level-order | Level by level | Printing layers, finding the shallowest match |

In-order traversal of a BST returns the values in ascending order.

```java
import java.util.*;

public class TreeTraversal {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static void inorder(TreeNode node, List<Integer> out) {
        if (node == null) {
            return;
        }
        inorder(node.left, out);
        out.add(node.val);
        inorder(node.right, out);
    }
}
```

An iterative version uses an explicit stack. It walks left as far as it can, then visits a node and moves to its right child.

```java
import java.util.*;

public class IterativeInorder {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static List<Integer> inorderIterative(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {
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

Level-order uses a queue. Read the queue size at the start of each pass to keep the levels separate.

```java
import java.util.*;

public class LevelOrder {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        if (root == null) {
            return levels;
        }
        Queue<TreeNode> queue = new ArrayDeque<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int size = queue.size();          // nodes in the current level
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) {
                    queue.offer(node.left);
                }
                if (node.right != null) {
                    queue.offer(node.right);
                }
            }
            levels.add(level);
        }
        return levels;
    }
}
```

Every traversal visits each node once, so it is O(n) time. Recursive depth-first traversal uses O(h) stack space. Level-order uses O(w) queue space, where w is the widest level.

### Morris traversal
Morris traversal does an in-order walk with O(1) extra space. It borrows the unused `right` pointer of each node's in-order predecessor as a temporary thread back to the node, then removes that thread when it returns. The tree is restored when the traversal ends.

```java
import java.util.*;

public class MorrisInorder {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static List<Integer> morrisInorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        TreeNode cur = root;
        while (cur != null) {
            if (cur.left == null) {
                out.add(cur.val);
                cur = cur.right;
            } else {
                TreeNode pred = cur.left;                 // in-order predecessor
                while (pred.right != null && pred.right != cur) {
                    pred = pred.right;
                }
                if (pred.right == null) {
                    pred.right = cur;                     // create the thread
                    cur = cur.left;
                } else {
                    pred.right = null;                    // remove the thread
                    out.add(cur.val);
                    cur = cur.right;
                }
            }
        }
        return out;
    }
}
```

Time is O(n), because each edge is walked a constant number of times. Extra space is O(1). Use it when the interviewer asks you to avoid recursion or extra stack space, and be ready to say that it temporarily modifies the tree.

### Tree dynamic programming
Many tree questions compute a value for each subtree from its children, then use it at the parent. The trick is to return one value to the parent and record a second, possibly larger, answer in a side variable. The diameter (the longest path measured in edges between any two nodes) is the standard example.

```java
import java.util.*;

public class TreeDiameter {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static int diameter(TreeNode root) {
        int[] best = new int[1];        // side answer, updated while recursing
        height(root, best);
        return best[0];
    }

    // Returns the number of nodes on the longest downward path from node.
    private static int height(TreeNode node, int[] best) {
        if (node == null) {
            return 0;
        }
        int left = height(node.left, best);
        int right = height(node.right, best);
        best[0] = Math.max(best[0], left + right);  // edges through this node
        return 1 + Math.max(left, right);
    }
}
```

Each node is visited once, so the time is O(n) and the stack space is O(h).

### Path sum
For root-to-leaf path sums, subtract the node value from the target as you descend, and check the target at a leaf.

```java
import java.util.*;

public class PathSum {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static boolean hasPathSum(TreeNode node, int target) {
        if (node == null) {
            return false;
        }
        if (node.left == null && node.right == null) {
            return node.val == target;
        }
        int rest = target - node.val;
        return hasPathSum(node.left, rest) || hasPathSum(node.right, rest);
    }
}
```

The check must happen at a leaf. A node with only one child is not the end of a path.

### Lowest common ancestor
In a BST, the lowest common ancestor (LCA) of two values is the first node where they split onto different sides, or the node equal to one of them. You do not need to search the whole tree.

```java
import java.util.*;

public class BstLca {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static TreeNode lcaBst(TreeNode root, int p, int q) {
        TreeNode cur = root;
        while (cur != null) {
            if (p < cur.val && q < cur.val) {
                cur = cur.left;
            } else if (p > cur.val && q > cur.val) {
                cur = cur.right;
            } else {
                return cur;      // split point, or one value equals cur.val
            }
        }
        return null;
    }
}
```

For a general binary tree, return the node when you find one target, and join the results from the two subtrees. This is O(n) time, O(h) stack space.

```java
import java.util.*;

public class TreeLca {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static TreeNode lca(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) {
            return root;
        }
        TreeNode left = lca(root.left, p, q);
        TreeNode right = lca(root.right, p, q);
        if (left != null && right != null) {
            return root;        // targets found on different sides
        }
        return (left != null) ? left : right;
    }
}
```

### Serialisation
Serialisation turns a tree into a string so that it can be stored or sent, then rebuilt. Pre-order with a marker for `null` is enough to rebuild a unique tree, because the marker records where each subtree ends.

```java
import java.util.*;

public class TreeSerialize {
    static class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }


    static String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        serializeHelper(root, sb);
        return sb.toString();
    }

    private static void serializeHelper(TreeNode node, StringBuilder sb) {
        if (node == null) {
            sb.append("#,");
            return;
        }
        sb.append(node.val).append(',');
        serializeHelper(node.left, sb);
        serializeHelper(node.right, sb);
    }

    static TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>(List.of(data.split(",")));
        return build(tokens);
    }

    private static TreeNode build(Deque<String> tokens) {
        String t = tokens.poll();
        if (t == null || t.equals("#")) {
            return null;
        }
        TreeNode node = new TreeNode(Integer.parseInt(t));
        node.left = build(tokens);
        node.right = build(tokens);
        return node;
    }
}
```

Both directions are O(n) time. Note that `List.of` requires Java 9 or later and rejects `null` elements, which `split` never produces.

### Balanced trees and other tree types
A plain BST has no guarantee on height, so production code uses self-balancing trees.

- **AVL trees** keep the heights of the two subtrees of every node within one of each other. Lookups are O(log n).
- **Red-black trees** use node colours and rotations to keep the tree balanced. Java's `TreeMap` and `TreeSet` are backed by a red-black tree, so their operations are O(log n).
- **B-trees** store many keys per node to reduce disk reads. Database indexes commonly use this design.
- **Tries** store strings by character, one level per character. Lookups cost O(L) for a string of length L, independent of how many strings are stored.
- **Segment trees** answer range queries and point updates in O(log n).

You will rarely implement these in an interview. Know what problem each one solves and what its operations cost.

## How it works / Step by step

1. Decide whether the tree is a BST. If it is, use the ordering to skip subtrees.
2. Ask what the parent needs from each child. If the answer is a single number, return it. If the question asks for a global best, record it in a side variable.
3. Write the base case first: `null` is the usual leaf boundary.
4. Use recursion for clear code and an explicit stack or queue when the depth may be large.
5. Test with an empty tree, one node, a skewed tree, and a balanced tree. The skewed case often exposes wrong complexity claims.

| Operation | Balanced tree | Skewed tree |
|---|---|---|
| BST search, insert, delete | O(log n) | O(n) |
| Full traversal | O(n) | O(n) |
| Recursive stack depth | O(log n) | O(n) |

## Common pitfalls

- Stating BST operations as O(log n) without saying the tree is balanced. The correct bound is O(h).
- Checking for a path sum at a node with one child, which is not a leaf.
- Calling `root.left.val` without a `null` check.
- Mixing up height and depth. Height is measured from a node down to its deepest leaf. Depth is measured from the root down to the node.
- Using recursion on a very deep, skewed tree and causing a `StackOverflowError`. Switch to an explicit stack when the depth can be large.
- Comparing `TreeNode` values with `==` when the problem asks for equal values. Compare `val` fields instead.
- Forgetting that Morris traversal changes `right` pointers while it runs.

!!! tip "Interview tip"
    **Q: How would you find the lowest common ancestor of two nodes in a binary search tree and in a general binary tree?**
    A: In a BST, walk from the root. If both values are smaller than the current node, go left. If both are larger, go right. Otherwise the current node is the answer, in O(h) time and O(1) extra space. In a general tree, there is no ordering, so recurse into both subtrees and return the node where the two results meet, in O(n) time.

## Quick recap

- A BST operation costs O(h). Only a balanced tree gives O(log n).
- Pre-order, in-order, post-order, and level-order cover all standard traversals, each in O(n) time.
- Morris traversal does an in-order walk in O(1) extra space by temporarily threading the tree.
- For tree DP, return one value to the parent and keep the global answer in a side variable.
- Serialise with pre-order and `#` markers to rebuild a unique tree.

**See also:** [Arrays & Strings](arrays-strings.md), [Linked Lists](linked-lists.md), [Stacks & Queues](stacks-queues.md), [DSA Foundations](index.md)
