# ML Algorithms

Common machine learning algorithms: regression, decision trees, ensemble methods, clustering, SVMs, and optimization techniques.

---

## Linear & Logistic Regression

### Linear Regression
Predict continuous value using linear relationship: **y = mx + b**

```python
# Simple linear regression
y = w₀ + w₁x₁ + w₂x₂ + ... + wₙxₙ

# Example: Predict house price
Price = 50000 + 100*sqft + 20000*bedrooms + noise

# Training: minimize loss (MSE)
Loss = Σ(predicted - actual)² / n
# Update weights via gradient descent
```

**When to use:**
- Linear relationships between features and target
- Interpretability matters (see coefficients)
- Baseline model before complex algorithms

**Assumptions:**
- Linear relationship
- Independent features
- Constant variance (homoscedasticity)
- Normally distributed errors

### Logistic Regression
Predict probability of class (0 or 1) using sigmoid function.

```python
# Sigmoid: maps any value to [0, 1]
P(y=1) = 1 / (1 + e^-z)
where z = w₀ + w₁x₁ + w₂x₂ + ...

# Decision: if P > 0.5 → class 1, else class 0

# Training: minimize log-loss (cross-entropy)
Loss = -Σ[y*log(P) + (1-y)*log(1-P)] / n
```

**When to use:**
- Binary classification
- Probabilistic output needed (confidence)
- Interpretability important
- Fast, works with many features

**Example:**
```
Email spam detection
Input: [word frequency, sender, links]
Output: P(spam) = 0.85 → likely spam
```

---

## Decision Trees

Tree-based model that recursively splits data on features.

```
        Root: All Emails
         /            \
    [Is_From_Known]    [Is_From_Unknown]
      /        \           /        \
   SPAM      [Has_Links]  SPAM   [Word_Freq>0.8]
              /      \             /        \
           SPAM     NOT_SPAM    SPAM     NOT_SPAM
```

### How It Works
1. At each node, find best feature/threshold to split
2. Minimize impurity (Gini or Entropy)
3. Recursively split until pure or stopping criteria

**Gini Impurity:**
```
Gini = 1 - Σ(p_i)²
where p_i = fraction of class i

Pure (all same class): Gini = 0
Mixed (50/50): Gini = 0.5
```

**When to use:**
- Non-linear relationships
- Categorical and numerical features mix
- Feature importance matters
- Interpretability (rule-based)

**Pros**: Fast, interpretable, handles mixed features  
**Cons**: Prone to overfitting, can be unstable (small data changes = big tree changes)

---

## Ensemble Methods

Combine multiple models for better performance.

### Random Forest
Train many decision trees on random subsets of data/features.

```
Original Dataset
├── Tree 1 (trained on random sample 1) → Prediction 1
├── Tree 2 (trained on random sample 2) → Prediction 2
├── Tree 3 (trained on random sample 3) → Prediction 3
└── Tree 4 (trained on random sample 4) → Prediction 4

Final = Average (regression) or Majority Vote (classification)
```

**Benefits:**
- Reduces variance (individual trees overfit, averaging smooths)
- Feature importance from permutation
- Handles missing values, mixed features
- Parallelizable

**When to use:**
- Baseline for most tabular datasets
- Feature importance needed
- Trade off speed for accuracy

### Gradient Boosting (XGBoost, LightGBM)
Sequentially train trees, each correcting previous errors.

```
Tree 1: Fit to data → Errors: [0.5, -0.3, 0.2, ...]
Tree 2: Fit to errors → Residuals: [0.1, -0.05, 0.04, ...]
Tree 3: Fit to residuals → ...
...

Final = Tree1 + α*Tree2 + α*Tree3 + ...
(α = learning rate, controls step size)
```

**Advantages:**
- Often best performance on tabular data (Kaggle winner)
- Handles non-linear relationships
- Feature importance, partial dependence plots
- Regularization (max_depth, min_samples, learning_rate)

**When to use:**
- Kaggle competitions, production models
- Tabular data with mixed features
- When Random Forest isn't good enough

---

## Support Vector Machines (SVM)

Find **hyperplane** that maximizes margin between classes.

```
Classification Problem:
  Class 1 (o)    Hyperplane      Class 2 (x)
  
  o   o              ─────        x  x
  o    o            /             x  x
  o   o            /   margin     x  x
          ───────────────────
         Support Vectors (closest points)

Maximize: Margin (distance from hyperplane to nearest points)
Subject to: Points on correct side
```

**Linear SVM:**
```
Decision boundary: w·x + b = 0
Prediction: sign(w·x + b)
```

**Kernel Trick:**
Transform data to higher dimensions to handle non-linear cases.

```
Non-linear data in 2D → Linear in higher dimensions
Kernels: Linear, RBF (Radial Basis Function), Polynomial
```

**When to use:**
- Binary classification
- High-dimensional data (text features)
- Robust to outliers (focuses on margin, not individual errors)
- SVM handles many features, small data

**Limitations:**
- Slow on very large datasets
- Less interpretable than decision trees
- Hyperparameter tuning matters (C, kernel, gamma)

---

## Clustering Algorithms

### KMeans
Partition data into K clusters, minimize within-cluster distance.

```
Algorithm:
1. Initialize K random centroids
2. Assign each point to nearest centroid
3. Recompute centroids (mean of assigned points)
4. Repeat 2-3 until convergence

Example: K=3 (3 clusters)
  *     **  o oo
  *    * * o   o
  *  *     o o
  (3 clusters formed)
```

**When to use:**
- Unsupervised segmentation (customer groups, image compression)
- Need interpretable clusters (centroid-based)
- Roughly spherical clusters

**Limitations:**
- Must specify K in advance
- Sensitive to initial centroids
- All clusters similar size/density

### DBSCAN
Density-based clustering; finds clusters of arbitrary shape.

```
Concepts:
- Eps: max distance to neighbors
- MinPts: min neighbors to form cluster

Algorithm:
1. For each unvisited point:
   - If has ≥ MinPts neighbors within Eps → Core point (start cluster)
   - Expand cluster to all reachable points
   - Mark noise: points not in any cluster
```

**Advantages:**
- Finds arbitrary-shaped clusters
- Identifies outliers (noise)
- No need to specify K

**When to use:**
- Unknown cluster shapes
- Noise present in data
- Varying cluster densities

---

## Gradient Descent

Optimization algorithm to minimize loss function.

```
Goal: Find weights w that minimize Loss(w)

Gradient Descent:
1. Initialize w randomly
2. Compute gradient: ∂Loss/∂w (direction of steepest increase)
3. Update: w = w - α * ∇Loss(w)  [α = learning rate]
4. Repeat until convergence

Visual:
        Loss
        /\
       /  \
      /    \ ← Gradient points uphill
     /      \____
    /___________
    (Starting w)  (Minimum)
```

### Variants

| Variant | Update | Speed | Memory | Use Case |
|---------|--------|-------|--------|----------|
| **Batch GD** | All samples | Slow | Low | Small datasets, stable |
| **SGD** | 1 sample | Fast, noisy | Low | Large datasets |
| **Mini-batch SGD** | N samples | Fast, stable | Medium | Most common |
| **Adam** | Adaptive learning rate | Fast, adaptive | Medium | Deep learning, default |

**Learning Rate (α):**
- Too high: Overshoot minimum, diverge
- Too low: Very slow convergence
- Adaptive: Adam automatically adjusts

---

## Algorithm Comparison

| Algorithm | Task | Speed | Interpretable | Best For |
|-----------|------|-------|---------------|----------|
| Linear Regression | Regression | Fast | Yes | Linear relationships |
| Logistic Regression | Classification | Fast | Yes | Binary, probability needed |
| Decision Tree | Both | Fast | Yes | Non-linear, rules |
| Random Forest | Both | Medium | Some | Baseline tabular data |
| Gradient Boosting | Both | Slow | Limited | Best tabular accuracy |
| SVM | Classification | Slow | No | High-dimensional, binary |
| KMeans | Clustering | Fast | Yes | Unsupervised segmentation |
| DBSCAN | Clustering | Medium | Yes | Arbitrary shapes, outliers |

---

## When to Use Each Algorithm

**Start with:**
- **Regression**: Linear Regression (baseline)
- **Classification**: Logistic Regression (binary), Random Forest (multi-class)
- **Clustering**: KMeans (simple), DBSCAN (shapes)

**If not good enough:**
- Try ensemble: Gradient Boosting (XGBoost, LightGBM)
- Try neural networks (deep learning)
- Better features, more data

**Production guidelines:**
- Interpretability matters? → Decision Tree, Linear Regression
- Best accuracy? → Gradient Boosting
- Real-time latency critical? → Simple models, SVM
- Lots of data? → Neural Networks, Gradient Boosting

---

## Interview Talking Points

- **Linear vs Logistic Regression?** Linear: continuous output; Logistic: probability [0,1]
- **Decision Tree overfitting?** Pruning, max_depth, min_samples; Random Forest reduces via averaging
- **Random Forest vs Gradient Boosting?** RF: parallel, simpler; GB: sequential, often better, slow
- **SVM pros/cons?** Pros: robust to outliers, high-dimensional; Cons: slow, less interpretable
- **Why ensemble methods?** Combining models reduces variance; individual models overfit, ensemble averages smooths
- **KMeans vs DBSCAN?** KMeans: specify K, spherical clusters; DBSCAN: any shape, finds outliers
- **Gradient Descent variants?** Batch: stable, slow; SGD: fast, noisy; Adam: adaptive, recommended
- **Feature scaling for algorithms?** Need: Distance-based (KMeans, KNN, SVM); Don't need: Tree-based (ignore scaling)

---

**See also:** [ML Fundamentals](fundamentals.md), [Deep Learning](deep-learning.md), [LLMs & Transformers](llms-transformers.md)
