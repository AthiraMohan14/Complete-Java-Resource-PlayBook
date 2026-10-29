# Machine Learning Fundamentals

Machine learning fits a model to data so that it can predict outcomes or uncover structure without hand-written rules. Interviewers start here because later topics (algorithms, deep learning, LLM evaluation) rely on the same ideas: learning paradigms, data splits, bias and variance, tuning, and metrics.

## Core concepts

### Learning paradigms

- **Supervised learning** uses labelled examples, pairs of input and known output. The two main task types are *regression* (predict a continuous number) and *classification* (predict a category).
- **Unsupervised learning** works on unlabelled inputs and looks for structure. Typical tasks are clustering, dimensionality reduction, and anomaly detection.
- **Reinforcement learning** trains an agent that acts in an environment and adjusts its behaviour based on reward signals. Key terms are *state*, *action*, *reward*, *policy* (how to act in each state), and *value* (expected future reward).

### Regression versus classification

| Task | Output | Examples | Common metrics |
|------|--------|----------|----------------|
| Regression | Continuous number | House price, demand forecast | MAE, MSE, RMSE, R² |
| Classification | Discrete label | Spam or not, fraud or not, digit recognition | Accuracy, precision, recall, F1, ROC AUC |

A quick way to pick: ask what the output looks like. A number on a continuous scale means regression. A choice from a fixed set means classification.

### Train, validation, and test splits

Hold data back so that you can measure generalisation honestly.

- **Training set**: fit the model parameters.
- **Validation set**: compare models and choose hyperparameters.
- **Test set**: report the final score once. Do not use it to make decisions.

Typical splits are 70/15/15 or 80/10/10. Without a separate validation set, repeated tuning against the test set inflates the reported score.

### Data leakage

Leakage happens when information from outside the training data reaches the model. Common causes:

- Fitting a scaler or imputer on the full dataset before splitting.
- Selecting features using the target across the whole dataset.
- Random splits on time-ordered data, so the model sees the future.

A scikit-learn `Pipeline` keeps preprocessing inside the cross-validation loop, which prevents the first cause:

```python
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
scores = cross_val_score(model, X_train, y_train, cv=5)  # scaler is refit per fold
print(f"CV accuracy: {scores.mean():.3f}")

model.fit(X_train, y_train)
print(f"Test accuracy: {model.score(X_test, y_test):.3f}")  # touched once
```

### Cross-validation

K-fold cross-validation splits the training data into K parts. Each part serves once as the validation fold while the model trains on the rest. The average of the K scores is a more stable estimate than one split, and every row is used for both training and validation. Use stratified folds for classification so each fold keeps the class balance. Use time-ordered splits for time series.

### Overfitting and underfitting

- **Overfitting**: the model learns noise in the training set. The signature is low training error with much higher validation error.
- **Underfitting**: the model is too simple or under-trained to capture the pattern. Both training and validation errors stay high.

Remedies for overfitting: more data, simpler models, regularisation (L1 or L2 penalties), feature selection, early stopping, and dropout in neural networks. Remedies for underfitting: richer features, a more flexible model, or longer training.

### Bias and variance

For squared-error loss, expected test error decomposes into three parts:

```
Expected error = bias² + variance + irreducible noise
```

- **Bias** is error from wrong assumptions. High bias means underfitting.
- **Variance** is sensitivity to the particular training sample. High variance means overfitting.

Simple models tend toward high bias and low variance. Very flexible models tend toward low bias and high variance. You aim for the complexity where validation error is lowest.

### Hyperparameters and tuning

Hyperparameters are set before training and are not learned from data. Examples are the learning rate, tree depth, the regularisation strength `C`, batch size, and number of epochs.

- **Grid search** tries every combination in a list. It is exhaustive, but the number of combinations multiplies with each parameter.
- **Random search** samples combinations from distributions. It often finds good settings with fewer trials, especially when only a few parameters matter.
- **Early stopping** halts training once validation loss stops improving for a set number of epochs (the patience) and keeps the best checkpoint.

```python
from sklearn.model_selection import GridSearchCV

param_grid = {"logisticregression__C": [0.1, 1.0, 10.0]}
search = GridSearchCV(model, param_grid, cv=5, scoring="f1")
search.fit(X_train, y_train)
print(search.best_params_, round(search.best_score_, 3))
```

### Feature engineering

- **Scaling**: standardisation (subtract mean, divide by standard deviation) or min-max scaling to [0, 1]. Distance-based methods such as k-means, k-nearest neighbours, and SVMs need it. Tree-based models do not.
- **Encoding categories**: use one-hot encoding for nominal categories. Use ordinal codes only when the order is meaningful.
- **Feature selection**: drop features that add noise. Methods include correlation filters, mutual information, recursive feature elimination, and L1 regularisation, which drives some weights to zero.
- **Feature creation**: combine raw fields into signals the model cannot easily form, such as a ratio or a time since last event.

### Evaluation metrics

For classification, start from the confusion matrix:

| | Predicted positive | Predicted negative |
|---|---|---|
| Actual positive | True positive (TP) | False negative (FN) |
| Actual negative | False positive (FP) | True negative (TN) |

- **Precision** = TP / (TP + FP). Of the items flagged positive, how many were right?
- **Recall** = TP / (TP + FN). Of the real positives, how many were found?
- **F1** is the harmonic mean of precision and recall.
- **Accuracy** can mislead on imbalanced data. A model that always predicts the majority class can score well.
- **ROC AUC** measures ranking quality across all thresholds. It does not depend on one cut-off.

For regression, MAE is the mean absolute error, MSE is the mean squared error, RMSE is its square root (same units as the target), and R² is the share of variance explained.

```python
from sklearn.metrics import classification_report, roc_auc_score

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred))
print(f"ROC AUC: {roc_auc_score(y_test, y_prob):.3f}")
```

## How it works / Step by step

1. Frame the problem: what is the output, and what would a good result look like?
2. Split the data before any exploration that could leak information.
3. Build a simple baseline, such as a majority-class predictor or linear model.
4. Engineer features inside a pipeline.
5. Cross-validate candidate models on the training data.
6. Tune hyperparameters with search on validation folds.
7. Evaluate the chosen model once on the test set.
8. Monitor the model after deployment, because data changes over time.

## Common pitfalls

- Tuning repeatedly against the test set, which makes the final score optimistic.
- Preprocessing before the split, which leaks statistics from the test rows.
- Judging an imbalanced problem by accuracy alone.
- Shuffling time-series data and then reporting strong results.
- Comparing two models on a single split when the difference is within noise.

!!! tip "Interview tip"
    **Why keep a test set when you already have validation folds?** Validation folds guide choices, so the model is indirectly fitted to them. The test set is the only untouched estimate of how the chosen model behaves on new data. Use it once, at the end.

## Quick recap

- Supervised learning predicts from labelled data; unsupervised learning finds structure; reinforcement learning optimises rewards.
- Regression predicts numbers; classification predicts labels.
- Keep train, validation, and test data separate, and prevent leakage with pipelines.
- Overfitting shows as a train and validation gap; underfitting shows as high error on both.
- Choose metrics that match the cost of each error type, especially on imbalanced data.

**See also:** [ML Algorithms](ml-algorithms.md), [Deep Learning](deep-learning.md), [LLMs and Transformers](llms-and-transformers.md), [Interview questions on AI and ML](../../interview-questions/technical/ai-and-machine-learning.md)
