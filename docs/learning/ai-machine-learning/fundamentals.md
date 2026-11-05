# ML Fundamentals

Core machine learning concepts: learning paradigms, data splits, model evaluation, hyperparameter tuning, and feature engineering.

---

## Supervised vs Unsupervised Learning

### Supervised Learning
Learning from **labeled data**: input (X) → output (Y).

```
Task: Predict house price given square footage, bedrooms, location
Input: [2000 sqft, 3 bed, downtown] → Output: $350,000
```

**Types:**
- **Regression**: Predict continuous value (house price, temperature)
- **Classification**: Predict category (spam/not spam, cat/dog/bird)

**Common algorithms**: Linear Regression, Logistic Regression, Decision Trees, SVM, Neural Networks

**Pros**: Accurate when labeled data available  
**Cons**: Expensive to label data, slow to gather; can't learn from unlabeled data

### Unsupervised Learning
Learning from **unlabeled data**: find hidden patterns, structure, relationships.

```
Task: Group similar customers without predefined categories
Input: [Age, Income, Purchase History] → Output: Clusters of similar customers
```

**Types:**
- **Clustering**: Group similar data points (KMeans, DBSCAN, Hierarchical)
- **Dimensionality Reduction**: Compress data (PCA, t-SNE, Autoencoders)
- **Anomaly Detection**: Find outliers (Isolation Forest, One-Class SVM)

**Pros**: Leverage unlimited unlabeled data  
**Cons**: Hard to evaluate; may find meaningless patterns

### Reinforcement Learning
Learning through **reward/penalty feedback**: agent interacts with environment, learns policy.

```
Task: Train agent to play Atari games
Action: Move right/left, jump
Reward: +1 for collecting coin, -1 for dying
Agent learns: Optimal policy = sequence of actions to maximize reward
```

**Key concepts:**
- **State**: Current situation
- **Action**: What agent can do
- **Reward**: Feedback signal
- **Policy**: Strategy (how to act in each state)
- **Value**: Expected future reward

**Applications**: Game AI, robotics, autonomous driving, resource optimization

---

## Regression vs Classification

| Task | Output | Examples | Metric |
|------|--------|----------|--------|
| **Regression** | Continuous value | House price, temperature, stock price | MSE, RMSE, MAE, R² |
| **Classification** | Discrete category | Spam/not spam, tumor/not tumor, digit recognition | Accuracy, Precision, Recall, F1, AUC |

### Regression Example
```
Problem: Predict house price (continuous)
Model: y = mx + b (Linear Regression)
Input: square_footage → Output: $price
Metric: MSE = mean((predicted - actual)²)
```

### Classification Example
```
Problem: Predict if email is spam (binary)
Model: Logistic Regression, SVM, or Neural Network
Input: [word_freq, sender, links] → Output: P(spam) 
Metric: Accuracy, Precision (TP/TP+FP), Recall (TP/TP+FN), F1
```

---

## Train / Validation / Test Split

Prevent **data leakage** and overfitting:

```
Total Data
├── Train (70%)     → Fit model, adjust weights
├── Validation (15%) → Tune hyperparameters, model selection
└── Test (15%)      → Final evaluation, report performance
```

### Why Not Just Train/Test?
❌ Bad: Train on 70%, test on 30%
- You can tune hyperparameters based on test results → overfitting to test data
- Reported accuracy is inflated

✅ Good: Train (70%) → Validate (15%) → Test (15%)
- Train: optimize model
- Validate: choose hyperparameters, compare models
- Test: unbiased final evaluation (don't touch during development)

### K-Fold Cross-Validation
Use when data is limited. Split data into K parts:

```
K=5 (5-Fold):
Fold 1: train on [2,3,4,5], validate on [1]
Fold 2: train on [1,3,4,5], validate on [2]
Fold 3: train on [1,2,4,5], validate on [3]
Fold 4: train on [1,2,3,5], validate on [4]
Fold 5: train on [1,2,3,4], validate on [5]

Final score = average of 5 validation scores
Benefit: More stable estimate, uses all data
```

---

## Overfitting vs Underfitting

### Overfitting
Model **memorizes training data**, learns noise instead of patterns.

```
Training Error: 0.5% (very low)
Validation Error: 15% (very high)
Gap: Large → Overfitting

Problem: Doesn't generalize to new data
```

**Causes**: Complex model, too many features, not enough data, high variance

**Solutions:**
- Simplify model (fewer layers, fewer parameters)
- Regularization: L1/L2 penalty, dropout, early stopping
- More training data
- Feature selection (remove irrelevant features)

### Underfitting
Model is **too simple** to capture patterns.

```
Training Error: 20% (high)
Validation Error: 22% (also high)
Gap: Small → Underfitting

Problem: Model can't fit training data, poor generalization
```

**Causes**: Weak model, too few features, wrong algorithm, high bias

**Solutions:**
- Use more complex model (more layers, more parameters)
- Add relevant features
- Train longer
- Better feature engineering

### Bias-Variance Tradeoff

```
Total Error = Bias² + Variance + Irreducible Error

Bias: Underfitting (model too simple)
Variance: Overfitting (model too complex)

Goal: Find sweet spot where both are minimized
```

---

## Hyperparameter Tuning

**Hyperparameters**: Parameters set before training (not learned).

**Examples:**
- Learning rate (α): step size for gradient descent
- Batch size: samples per update
- Epochs: iterations through data
- Number of layers/neurons: model architecture
- Regularization strength (λ): penalty for complex weights

### Grid Search
Try all combinations of hyperparameters.

```python
# Example: Learning rate × Batch size
learning_rates = [0.001, 0.01, 0.1]
batch_sizes = [16, 32, 64]

# Test 3×3 = 9 combinations
best_params = None
best_accuracy = 0

for lr in learning_rates:
    for bs in batch_sizes:
        model = train(lr=lr, batch_size=bs)
        accuracy = validate(model)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_params = (lr, bs)
```

**Pros**: Exhaustive; finds best combination  
**Cons**: Exponentially slow (3 params × 5 values each = 125 combinations)

### Random Search
Sample random hyperparameter combinations.

```python
for iteration in range(100):
    lr = random.uniform(0.001, 0.1)
    bs = random.choice([16, 32, 64])
    model = train(lr=lr, batch_size=bs)
    accuracy = validate(model)
    track(best)
```

**Pros**: Faster than grid search; often finds good hyperparameters  
**Cons**: May miss optimal combination

### Early Stopping
Stop training when validation error increases.

```
Epoch 1: train_loss=0.50, val_loss=0.45 → improving
Epoch 2: train_loss=0.40, val_loss=0.44 → improving
Epoch 3: train_loss=0.30, val_loss=0.50 → getting worse! STOP
Best model: Epoch 2
```

---

## Feature Engineering

Transform raw data into useful features.

### Scaling
Normalize features to same range (especially for distance-based algorithms).

```python
# Example: Age [18-80], Income [20k-500k] on different scales
# Standardization: subtract mean, divide by std
X_scaled = (X - mean) / std

# MinMax: scale to [0,1]
X_minmax = (X - min) / (max - min)

# Why: KMeans, KNN use distance; unscaled features bias toward large ranges
```

### Feature Selection
Remove irrelevant or redundant features.

```
Original features: [Age, Income, Zip_Code, Country, Favorite_Color]
Useful: [Age, Income] → Predict loan approval
Noise: [Zip_Code, Favorite_Color] → Doesn't help
Result: Remove noise, simpler model, faster training
```

**Methods:**
- Correlation analysis: remove highly correlated features
- Mutual information: measure feature-target dependency
- Recursive feature elimination: iteratively remove least important
- L1 regularization: zeros out weights of unimportant features

### Feature Creation
Combine features to capture patterns.

```
Example: Predict house price
Raw: [square_footage, bedrooms]
New: [price_per_sqft = price / sqft, rooms_per_sqft = bedrooms / sqft]
Benefit: Explicitly captures domain knowledge
```

### Encoding Categorical Features
Convert categories to numbers.

```
Color: Red=0, Green=1, Blue=2 (Ordinal)

City: New York → [1,0,0], LA → [0,1,0], Chicago → [0,0,1] (One-Hot)
```

---

## Model Evaluation Metrics

### Regression Metrics
- **MAE (Mean Absolute Error)**: Average |predicted - actual|
- **MSE (Mean Squared Error)**: Average (predicted - actual)²
- **RMSE (Root Mean Squared Error)**: √MSE
- **R² (Coefficient of Determination)**: % variance explained by model [0, 1]

### Classification Metrics
- **Accuracy**: (TP + TN) / Total (overall correctness)
- **Precision**: TP / (TP + FP) (of predicted positive, how many are correct?)
- **Recall**: TP / (TP + FN) (of actual positive, how many did we catch?)
- **F1-Score**: 2 × (Precision × Recall) / (Precision + Recall) (balanced score)
- **AUC-ROC**: Area under curve (probability threshold matters)

**When to use which:**
- Balanced data: Accuracy
- Imbalanced data (fraud detection): Precision, Recall, F1
- Need threshold optimization: AUC-ROC

---

## Interview Talking Points

- **Supervised vs Unsupervised?** Supervised: labeled data, predict output; Unsupervised: unlabeled data, find patterns
- **Regression vs Classification?** Regression: continuous (price, temp); Classification: discrete (spam/not spam)
- **Why train/validation/test split?** Validation tunes hyperparameters without overfitting to test set
- **Overfitting vs Underfitting?** Overfitting: high train accuracy, low test accuracy; Underfitting: both low
- **Bias-Variance tradeoff?** Complex models: high variance, low bias; Simple models: low variance, high bias
- **When to use K-Fold?** Limited data; more stable estimate than single train/test split
- **Feature scaling importance?** Algorithms like KMeans, KNN use distance; unscaled features bias toward large ranges
- **Precision vs Recall?** Precision: accuracy of positive predictions; Recall: coverage of positive cases; trade-off matters by use case

---

**See also:** [ML Algorithms](algorithms.md), [Deep Learning](deep-learning.md), [LLMs & Transformers](llms-transformers.md)

**Practice questions:** [Machine Learning & AI](../interview-questions/verbal/verbal-ml-ai-questions.md)
