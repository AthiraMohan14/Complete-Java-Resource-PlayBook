# Machine Learning for Backend Engineers

You do not need to train state-of-the-art models to build ML-backed features. Backend engineers are often asked to serve a model behind an API, keep its inputs consistent, measure its behaviour in production, and explain its limits to the rest of the team. This page covers the vocabulary and lifecycle you need, and the Java and JavaScript options for running models.

## Core concepts

### The ML lifecycle in brief

1. **Frame the problem:** what is predicted, for whom, and what decision it drives
2. **Collect and label data:** examples of inputs and the correct outputs
3. **Build features:** turn raw data into numeric inputs the model can use
4. **Train:** fit model parameters to the training data
5. **Evaluate:** measure performance on data the model did not see
6. **Deploy and monitor:** serve predictions and watch for drift and errors

Backend engineers mostly work on steps 3 (features that are available at serving time), 5 and 6 (measurement and monitoring), and the serving layer.

### Training, validation, and test data

Split labelled data into a **training** set (the model learns from it), a **validation** set (you tune settings with it), and a **test** set (you use it once, for an honest final measure). Reusing the test set for tuning inflates results.

**Overfitting** means the model memorises the training data and performs worse on new data. **Underfitting** means it has not learned the pattern. Comparing training and validation performance is the basic check.

### Features and training-serving skew

A **feature** is an input variable, such as "orders in the last 30 days" or "account age in days". The most common production bug is **training-serving skew**: features are computed one way in the training pipeline and another way in the online service. The model then sees values it was never trained on.

Mitigations: share feature definitions in code, use a feature store where the team has one, and log the features used at serving time so you can compare them with training data.

Also watch for **data leakage**, where a feature uses information that would not be available at prediction time (for example, a field set after the outcome happens). Leakage makes offline metrics look excellent and production results poor.

### Evaluation metrics

Choose metrics that match the decision:

- **Accuracy:** share of correct predictions; misleading when classes are imbalanced
- **Precision:** of the items flagged positive, how many were truly positive
- **Recall:** of the truly positive items, how many were flagged
- **Calibration:** whether a predicted 0.7 really happens about 70% of the time
- **Business metrics:** the outcome you actually care about, measured in an experiment where possible

Precision and recall trade off against each other through the decision threshold. The right balance depends on the cost of each kind of error. A fraud check and a product recommendation have very different costs.

### Serving models behind REST or gRPC

A model is usually served as a small service with a prediction endpoint. Concerns for backend engineers:

- **Latency budget:** agree on the maximum time a prediction may take, and measure it at p95 and p99
- **Batching:** group requests when throughput matters more than per-request latency
- **Versioning:** version models like APIs, and record which version answered each request
- **Fallbacks:** if the model is unavailable or times out, return a rule-based default
- **Input validation:** reject malformed or out-of-range features before inference
- **Rollout:** shadow traffic, canary releases, and A/B tests before full switch-over

A prediction endpoint returns a score and the model version, so downstream logs can be joined with outcomes later.

### Prediction APIs

A typical contract includes the model name and version, the features (or a reference to them), the prediction, and a confidence or score. Keep the contract stable even when the model changes. The same discipline as the [API design](../21-api-design/rest-principles-versioning.md) section applies.

### Java options: DJL and ONNX Runtime

Java applications can run models in-process rather than calling a separate service:

- **Deep Java Library (DJL):** a Java deep-learning library with an engine-agnostic API, which can load models from several frameworks through pluggable engines. It suits teams that want to stay in the JVM.
- **ONNX Runtime:** an inference engine for models in the ONNX format, which many training frameworks can export to. It has a Java API and is a common choice for production inference.

A simple, illustrative in-process scorer for a linear model shows what the serving code does. Real models are loaded from a file by the library:

```java
public final class LinearScorer {

    private final double[] weights;
    private final double bias;

    public LinearScorer(double[] weights, double bias) {
        this.weights = weights.clone();
        this.bias = bias;
    }

    public double score(double[] features) {
        if (features.length != weights.length) {
            throw new IllegalArgumentException("feature count mismatch");
        }
        double sum = bias;
        for (int i = 0; i < weights.length; i++) {
            sum += weights[i] * features[i];
        }
        // Logistic function maps the raw sum to a value between 0 and 1
        return 1.0 / (1.0 + Math.exp(-sum));
    }
}
```

The validation of feature count and the separation of model parameters from the service code are the same concerns you would have with a real model library.

### TensorFlow.js

**TensorFlow.js** runs models in JavaScript, in the browser or in Node.js. It is useful when inference should happen on the client (for privacy, latency, or offline use) or when a JavaScript service needs a model. It is not a Java library, so it fits best in a front-end or Node component of a system. Model size and device capability limit what is practical in the browser.

## How it works

1. Training happens offline, from a pipeline that produces a versioned model artifact.
2. The artifact is loaded by a serving component, in Java (DJL, ONNX Runtime), as a separate service, or in the browser (TensorFlow.js).
3. A request arrives with features; the serving layer validates them and runs inference within a time budget.
4. The prediction, model version, and inputs are logged.
5. Monitoring compares input distributions and outcomes with training data, and triggers retraining or rollback.

## Common pitfalls

- Training-serving skew from computing features differently online and offline
- Data leakage that inflates offline metrics
- Evaluating on data reused for tuning, so the test set is no longer honest
- Using accuracy for imbalanced problems
- No fallback when the model is slow or unavailable
- Serving predictions without recording the model version
- Deploying a new model with no shadow or canary period

!!! tip "Interview tip"
    **Q: A model performed well in testing but poorly in production. What do you check?**
    A: First look for training-serving skew: compare the feature values at serving time with the training data. Then check for data leakage in the training features, drift in the input distribution, and whether the production label or outcome is defined the same way as in the training set. Compare the model version actually serving with the one evaluated.

## Quick recap

- Know the lifecycle: frame, data, features, train, evaluate, deploy, monitor
- Keep test data untouched; choose metrics that match the decision
- Training-serving skew and leakage cause most production surprises
- Serve models with latency budgets, versioning, fallbacks, and rollout plans
- Java can run models in-process with DJL or ONNX Runtime; TensorFlow.js runs in JavaScript

**See also:** [Search and Analytics](search-analytics.md), [Advanced Patterns](advanced-patterns.md), [LLM Integration](../22-ai-integration/llm-integration.md)
