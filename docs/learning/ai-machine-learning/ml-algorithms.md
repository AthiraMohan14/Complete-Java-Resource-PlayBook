# Machine Learning Algorithms

Classical algorithms remain the first tool for tabular data: linear models, decision trees, ensembles of trees, support vector machines, and clustering. Interviewers ask how each one works, when it fails, and how to choose between them.

## Core concepts

### Linear regression

Linear regression predicts a continuous value as a weighted sum of features:

```
y = w0 + w1·x1 + w2·x2 + ... + wn·xn
```

Training chooses the weights that minimise mean squared error. It is fast, interpretable (each weight shows a feature's effect with other features held fixed), and a good baseline.

Its assumptions matter when you interpret coefficients: the relationship is roughly linear, the features are not strongly correlated with each other, residuals have constant variance, and residuals are roughly normally distributed for inference.

### Gradient descent in one example

Most models are trained by gradient descent: compute the gradient of the loss and move the weights a small step against it. The learning rate sets the step size. Too large and training diverges; too small and it crawls.

```python
def fit_line(xs, ys, lr=0.05, steps=1000):
    """Fit y = w*x + b by gradient descent on mean squared error."""
    w, b = 0.0, 0.0
    n = len(xs)
    for _ in range(steps):
        dw = sum(2 * (w * x + b - y) * x for x, y in zip(xs, ys)) / n
        db = sum(2 * (w * x + b - y) for x, y in zip(xs, ys)) / n
        w -= lr * dw
        b -= lr * db
    return w, b

w, b = fit_line([1, 2, 3, 4], [3, 5, 7, 9])
print(round(w, 2), round(b, 2))  # close to 2 and 1
```

### Logistic regression

Logistic regression is a classifier. It computes a linear score `z` and passes it through the sigmoid function:

```
P(y = 1) = 1 / (1 + e^(-z))
```

The model is trained by minimising log loss (cross-entropy). The output is a probability, and a threshold (0.5 by default) turns it into a class. The threshold can be moved to trade precision for recall. Like linear regression, it is fast and interpretable, and it is a strong baseline for binary problems.

### Decision trees

A decision tree splits the data recursively. At each node it chooses the feature and threshold that best separate the classes, measured by impurity:

```
Gini = 1 - Σ p_i²
```

A pure node has Gini 0. A 50/50 binary node has Gini 0.5. Entropy (information gain) is the other common criterion.

Trees handle non-linear relationships and mixed feature types, and they need no scaling. A single deep tree memorises training data and changes a lot with small data changes. Control this with `max_depth`, `min_samples_leaf`, or pruning.

### Random forests (bagging)

A random forest trains many trees, each on a bootstrap sample of the rows and a random subset of features at each split. Predictions are averaged (regression) or voted (classification).

Averaging decorrelated trees reduces variance without much added bias. Trees train in parallel, and the out-of-bag samples give a built-in validation estimate. Forests are a strong default for tabular data, though their predictions are harder to explain than one tree.

### Gradient boosting

Boosting trains trees one after another. Each new tree fits the errors (more precisely, the negative gradient of the loss) left by the ensemble so far. The learning rate scales each tree's contribution.

Gradient-boosted tree libraries such as XGBoost, LightGBM, and CatBoost are often the strongest choice on tabular data. They are slower to tune than a forest and less transparent. Regularise with tree depth, learning rate, minimum leaf size, and subsampling.

### Support vector machines

An SVM finds the hyperplane that separates classes with the widest margin. The points closest to the boundary are the *support vectors*. A soft margin parameter `C` trades margin width against misclassified training points. Kernels such as RBF let the boundary bend by implicitly mapping data into a higher-dimensional space; `gamma` controls how local that bend is.

SVMs need scaled features, perform well on high-dimensional, sparse inputs such as text, and can be slow on very large datasets. They produce no native probabilities, and they are hard to interpret.

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

svm = make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1.0, gamma="scale"))
svm.fit(X_train, y_train)
print(round(svm.score(X_test, y_test), 3))
```

### Clustering

**k-means** assigns points to the nearest of K centroids, recomputes the centroids as the means of their members, and repeats until assignments stop changing. It needs K in advance, works best with roughly spherical clusters of similar size, and is sensitive to initialisation (k-means++ helps). Use the elbow method or silhouette scores to compare values of K.

```python
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=3, n_init=10, random_state=0)
labels = kmeans.fit_predict(X_train)  # scale features first
```

**DBSCAN** groups points that have at least `min_samples` neighbours within radius `eps`, grows clusters from these core points, and labels everything else as noise. It finds clusters of arbitrary shape and needs no K. It struggles when clusters have very different densities, because one `eps` cannot suit them all.

### Gradient descent variants

| Variant | Each update uses | Trade-off |
|---------|------------------|-----------|
| Batch | All samples | Stable, slow, memory-heavy on big data |
| Stochastic (SGD) | One sample | Fast, noisy |
| Mini-batch | A small batch | The usual compromise on GPUs and CPUs |
| Adam | Mini-batch plus adaptive per-parameter steps | Robust defaults, a few more hyperparameters |

## How it works / Step by step

Choosing an algorithm for a tabular problem:

1. Fit a baseline: logistic or linear regression, with scaling where needed.
2. Try a random forest with default-ish settings and check cross-validated scores.
3. If accuracy is not enough, try gradient boosting and tune its learning rate, depth, and number of trees.
4. Weigh the result against interpretability, latency, and training cost.
5. For unlabelled data, start with k-means, check the cluster quality, and try DBSCAN if the shapes look irregular.

| Algorithm | Task | Training speed | Interpretability | Typical use |
|-----------|------|----------------|------------------|-------------|
| Linear regression | Regression | Fast | High | Baseline, linear trends |
| Logistic regression | Classification | Fast | High | Binary probabilities |
| Decision tree | Both | Fast | High | Rules, mixed features |
| Random forest | Both | Medium | Medium | Strong tabular baseline |
| Gradient boosting | Both | Slower | Low to medium | Top accuracy on tabular data |
| SVM | Both | Slow on big data | Low | High-dimensional, small to medium data |
| k-means | Clustering | Fast | Medium | Segments, compression |
| DBSCAN | Clustering | Medium | Medium | Irregular shapes, outliers |

## Common pitfalls

- Forgetting to scale features for SVMs, k-means, or k-nearest neighbours. Tree models do not need scaling.
- Reading a single deep tree as reliable. Its structure depends heavily on the sample.
- Treating forest or boosting feature importances as causal. They measure predictive use, and correlated features share credit.
- Choosing k-means K by intuition alone, without a validation criterion.
- Using DBSCAN with one `eps` on data whose clusters differ widely in density.

!!! tip "Interview tip"
    **Random forest or gradient boosting?** Forests build independent trees in parallel and reduce variance by averaging. Boosting builds trees in sequence, each correcting the last, which lowers bias and often gives higher accuracy. Boosting is more sensitive to tuning and more prone to overfitting if the learning rate and depth are not controlled.

## Quick recap

- Linear and logistic regression are fast, interpretable baselines.
- Decision trees split on impurity; single trees overfit, so limit depth or use ensembles.
- Forests average decorrelated trees; boosting fits trees to residual errors.
- SVMs maximise the margin, need scaled inputs, and use kernels for non-linear boundaries.
- k-means needs K and suits round clusters; DBSCAN finds arbitrary shapes and marks noise.

**See also:** [ML Fundamentals](ml-fundamentals.md), [Deep Learning](deep-learning.md), [LLMs and Transformers](llms-and-transformers.md)
