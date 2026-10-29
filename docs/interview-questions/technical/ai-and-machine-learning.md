# AI and Machine Learning Questions

Core machine learning, deep learning, LLM, and production questions, with answers you can say out loud. Each answer gives a direct response first, then the reasoning and the usual follow-ups.

---

## 1. What is the difference between supervised and unsupervised learning?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Supervised learning trains on examples that include the correct output, so the model learns a mapping from inputs to labels or numbers. Unsupervised learning works only with inputs and looks for structure, such as groups or lower-dimensional representations, without a known right answer.

### Explanation
In supervised learning the labels make evaluation straightforward: you compare predictions with held-out labels. The two main supervised tasks are regression, which predicts a continuous value such as a price, and classification, which predicts a category such as spam or not spam.

Unsupervised learning covers clustering (grouping similar customers, for example), dimensionality reduction (compressing many features into fewer informative ones), and anomaly detection. Evaluation is harder because there is no ground truth, so you rely on internal measures such as cluster cohesion, or on downstream results.

The practical trade-off is cost. Labels are often expensive to create, while unlabelled data is usually abundant. Teams often use unsupervised methods to explore data, and supervised methods once they have labels for the decision they care about.

### Likely follow-up
**What about semi-supervised learning?** It combines a small labelled set with a large unlabelled one. A common pattern is self-supervised pretraining on the large set, followed by fine-tuning on the labels.

| Situation | Typical approach |
|---|---|
| Plenty of labels for the exact decision | Supervised learning |
| Few labels, lots of raw data | Semi-supervised or self-supervised pretraining |
| No labels, want structure only | Clustering or dimensionality reduction |

### When to use / pitfalls
- Use supervised learning when you can define the target and have enough labelled examples.
- Use clustering when you need segments but have no predefined categories, then check whether the segments mean anything to the business.
- Dimensionality reduction such as PCA creates new combined features; it does not simply select the 50 best of the originals.
- Unsupervised outputs can look convincing and still be meaningless, so validate them against domain knowledge.

**See also:** [ML Fundamentals](../../learning/ai-machine-learning/ml-fundamentals.md), [ML Algorithms](../../learning/ai-machine-learning/ml-algorithms.md)

</details>

---

## 2. What is overfitting, and how do you prevent it?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Overfitting means the model has learned the training data too closely, including its noise, so it performs well on that data but poorly on new data. You spot it by a large gap between training and validation performance. You prevent it with more data, simpler models, regularisation, early stopping, and validation practices that expose the gap early.

### Explanation
Imagine a model that memorises the exact answers from a practice exam. It scores perfectly on that exam and fails a new one, because it never learned the underlying topic. A model with many parameters relative to the amount of data can do the same thing.

Detection is a comparison. Plot or compute training and validation error as training proceeds. If training error keeps falling while validation error rises, the model is overfitting.

Prevention options, in rough order of impact:
- **More representative data**, which makes memorisation harder.
- **Simpler models or fewer features**, which reduce capacity.
- **Regularisation**: L2 weight penalties shrink weights; L1 drives some to zero and selects features.
- **Early stopping** on validation loss, keeping the best checkpoint.
- **Dropout and data augmentation** in neural networks.
- **Cross-validation** to get an honest estimate and to compare settings fairly. It does not reduce overfitting by itself, but it reveals it.

### Diagnostic signs

| Pattern | Likely cause | First action |
|---|---|---|
| Training error low, validation error high | Overfitting | Regularise, add data, or stop earlier |
| Both errors high | Underfitting | Add capacity or better features |
| Both errors low and close | Healthy fit | Check the test set once, at the end |

### Likely follow-up
**How do you know regularisation is working?** Plot validation loss against the penalty strength. It should fall, reach a minimum, and then rise again as the model starts to underfit. Choose the strength at that minimum.

### When to use / pitfalls
- Regularisation strength is a hyperparameter; tune it on validation folds, not on the test set.
- A low training loss is never proof of a good model on its own.
- Adding features without enough data often increases overfitting.
- Do not respond to overfitting by picking the model that happens to score best on the test set; that is another form of overfitting.

**See also:** [ML Fundamentals](../../learning/ai-machine-learning/ml-fundamentals.md), [Deep Learning](../../learning/ai-machine-learning/deep-learning.md)

</details>

---

## 3. What is the bias-variance tradeoff?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Bias is error caused by overly strong assumptions, which leads to underfitting. Variance is error caused by sensitivity to the particular training sample, which leads to overfitting. Increasing model complexity usually lowers bias and raises variance. The goal is the complexity where total test error is lowest.

### Explanation
For squared-error loss, expected error splits into three parts: bias squared, variance, and irreducible noise in the data itself. You cannot remove the noise, so you manage the first two.

- A straight line fitted to clearly curved data has high bias. It is consistently wrong in the same way, and it performs poorly on training and test data alike.
- A high-degree polynomial fitted to noisy points has low bias but high variance. It fits training points closely, and its predictions swing if you retrain on a different sample.

The sweet spot is where validation error is lowest. Regularisation, ensembles such as bagging, and more data all reduce variance. More expressive models, richer features, and longer training reduce bias.

### Likely follow-up
**What does the tradeoff imply for ensembles?** Deep decision trees have low bias and high variance. Averaging many of them, as bagging does, cuts variance while keeping bias low, which is why random forests work well. Boosting starts from weak, high-bias learners and reduces bias step by step, so it needs tight control of depth and learning rate to avoid variance growth.

### When to use / pitfalls
- Bagging, as in random forests, mainly reduces variance; boosting mainly reduces bias but needs care to avoid variance growth.
- A model that underfits will not improve from more data alone. Check whether the features and model class can express the pattern at all.
- Diagnose with learning curves: if training and validation error both plateau high, that points to bias; a large gap points to variance.

**See also:** [ML Fundamentals](../../learning/ai-machine-learning/ml-fundamentals.md), [ML Algorithms](../../learning/ai-machine-learning/ml-algorithms.md)

</details>

---

## 4. How do convolutional neural networks work, and when would you use one?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A convolutional neural network applies small learned filters across an image. Each filter responds to a local pattern such as an edge or texture, and the same filter weights are reused at every position. Stacking convolution, non-linearity, and pooling layers lets the network build from edges to parts to objects. Use a CNN when the data has a grid structure, most often images, and also for some signal and spatial data.

### Explanation
A convolution computes a dot product between a filter and each local patch of the input, producing a feature map. Early layers learn simple features, and deeper layers combine them. A ReLU activation adds non-linearity, and pooling reduces spatial size, which makes the response to small shifts more stable.

Two properties make CNNs efficient on images:
- **Local connectivity**: each output depends on a small neighbourhood, because nearby pixels are related.
- **Weight sharing**: one filter scans the whole image, so the parameter count stays small and a feature learned in one place works everywhere.

Shifting the input shifts the feature map by the same amount (equivariance). Pooling then gives approximate invariance to small shifts. A final dense layer or a head for detection or segmentation turns the features into the required output.

Typical uses are image classification, object detection, segmentation, and some medical imaging. Tabular data usually fits better with tree ensembles or MLPs. For time series, recurrent models or 1D convolutions can work, and transformers are common for long sequences.

### Likely follow-up
**Why not use a fully connected network on images?** A 224 by 224 RGB image has about 150,000 input values. One 1,000-unit hidden layer on that input needs roughly 150 million weights, and the network treats a shifted object as entirely new input. Convolutions share weights across positions and exploit local structure, so they need far fewer parameters and generalise better.

### When to use / pitfalls
- Use pretrained backbones and fine-tune them when the labelled dataset is small.
- Input normalisation and augmentation such as flips or crops matter as much as the architecture.
- Do not describe CNNs as fully translation-invariant; pooling only gives approximate tolerance to shifts.
- A CNN on a shuffled, non-grid feature vector gains nothing from the spatial structure.

**See also:** [Deep Learning](../../learning/ai-machine-learning/deep-learning.md)

</details>

---

## 5. Explain the transformer architecture and the attention mechanism.

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
A transformer is a neural network built from attention layers and feed-forward layers, with no recurrence. Self-attention lets every token weigh every other token in the same sequence, so the model captures long-range relationships and processes all positions in parallel. Encoders, decoders, or both are stacked in blocks, and training usually starts from large-scale pretraining followed by fine-tuning.

### Explanation
Attention computes, for each token, a weighted average over the value vectors of all tokens. The weights come from comparing that token's query with every token's key, scaled by the square root of the key dimension and normalised with softmax. Because every token attends to every other in one matrix operation, the computation parallelises well, unlike a recurrent network that must process tokens in order.

Multi-head attention runs several attention operations in parallel, each with its own learned projections, and concatenates the results. Positional encodings are added because attention alone ignores order.

Each block adds residual connections and layer normalisation around the attention and feed-forward sub-layers. Stacking many blocks gives deep representations.

Common families:
- **Encoder-only (BERT)**: bidirectional context, used for classification, extraction, and embeddings.
- **Decoder-only (GPT-style)**: causal masking, used for generation and chat.
- **Encoder-decoder (T5-style)**: encoder reads the input, decoder generates the output with cross-attention, used for translation and summarisation.

### Likely follow-up
**Why divide by the square root of the key dimension?** Dot products grow in magnitude as the dimension grows. Large scores push softmax into a region where its gradients are tiny, which slows learning. Dividing by the square root keeps the score variance roughly constant as the dimension changes.

### When to use / pitfalls
- Attention cost grows with the square of sequence length, so very long inputs need retrieval, chunking, or efficient attention variants.
- Explain multi-head attention as several learned views of the sequence; do not assign fixed linguistic roles to each head.
- Say that transformers process positions in parallel during training; generation in decoder models is still sequential, one token at a time.

**See also:** [LLMs and Transformers](../../learning/ai-machine-learning/llms-and-transformers.md), [Deep Learning](../../learning/ai-machine-learning/deep-learning.md)

</details>

---

## 6. What is RAG, and why is it useful?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Retrieval-augmented generation (RAG) first retrieves relevant passages from a document store, then gives them to a language model along with the question, so the answer is grounded in those passages. It reduces hallucination, keeps answers current without retraining, and lets the system cite its sources.

### Explanation
Without retrieval, an LLM answers from patterns learned during training. If the question concerns a private document, a recent event, or a policy that changed, the model may produce a plausible but invented answer. RAG changes the input: the prompt contains the relevant text, and the model's job becomes reading and summarising that text.

The pipeline has an offline part and an online part. Offline, documents are split into chunks, each chunk is embedded as a vector, and the vectors go into an index with metadata. Online, the question is embedded with the same model, the index returns the top-k most similar chunks, and the prompt combines instructions, those chunks, and the question. The model's answer can then cite chunk IDs.

Components and their roles:
- **Embedding model**: maps text to vectors where similar meaning means nearby vectors.
- **Vector index**: performs fast similarity search, often approximate at scale.
- **Retriever**: applies filters such as user permissions, and may combine keyword and vector search.
- **Generator**: the LLM that writes the grounded answer.

The benefits are factual grounding, updates by re-indexing rather than retraining, traceable sources, and access control at retrieval time. A smaller model can often suffice because the facts come from the context.

### Likely follow-up
**How does RAG differ from fine-tuning?** RAG changes what the model sees at query time. Fine-tuning changes the model's weights and therefore its behaviour. Use RAG for facts that change and must be cited, and fine-tuning for consistent style, format, or a specialised task. The two can be combined.

### When to use / pitfalls
- RAG is weaker when the needed answer spans many documents that retrieval does not surface together; multi-step retrieval or summaries help.
- Chunking that splits a key table or definition loses meaning. Keep metadata for citations.
- Retrieved text is untrusted input and can contain instructions. Keep the model's tool access limited.
- Evaluate retrieval recall and answer faithfulness separately, or you will not know which part failed.

**See also:** [RAG and Generative AI](../../learning/ai-machine-learning/rag-and-generative-ai.md), [AI in Java](../../learning/ai-machine-learning/ai-in-java.md)

</details>

---

## 7. What is the difference between precision and recall?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Precision is the share of predicted positives that are truly positive: TP / (TP + FP). Recall is the share of actual positives the model finds: TP / (TP + FN). Raising the decision threshold usually increases precision and lowers recall; lowering it does the reverse.

### Explanation
Both come from the confusion matrix. A false positive is a wrong alarm, and a false negative is a missed case. Precision answers "when the model says yes, how often is it right?" Recall answers "of all the real cases, how many did it catch?"

Which one to favour depends on the cost of each error:
- **Favour recall** when missing a case is costly: screening for a serious disease, or catching fraud where each missed case has a large loss. Accept more false alarms to catch more true cases.
- **Favour precision** when false alarms are costly: blocking legitimate email, or showing irrelevant results to a user who trusts the list. Accept missing some true cases to keep the output clean.

F1 is the harmonic mean of precision and recall, and it is useful for a single number when both matter and classes are imbalanced. Precision-recall curves and ROC AUC show performance across thresholds. Note that the business sometimes sets a threshold based on capacity, such as how many cases a team can review each day.

Terminology note: precision is not the false positive rate, and recall is not the false negative rate. The false positive rate is FP / (FP + TN), and the false negative rate is FN / (TP + FN), which is one minus recall.

### Worked example
Suppose a fraud model flags 50 transactions. 40 of them are real fraud, and 60 real fraud cases exist in total.

- TP = 40, FP = 10 (50 flagged minus 40 real), FN = 20 (60 real minus 40 caught).
- Precision = 40 / 50 = 0.80. Four in five alerts were fraud.
- Recall = 40 / 60, about 0.67. Two in three fraud cases were caught.

### Likely follow-up
**How would you choose the threshold?** Estimate the cost of each error type with the people who own the decision. Then sweep thresholds on validation data and pick the one that meets a required precision or recall, or minimises expected cost. Show the trade-off curve to stakeholders instead of defaulting to 0.5.

### When to use / pitfalls
- Accuracy hides problems on imbalanced data. Report precision and recall per class.
- Compare models at the same threshold or on a curve; a single threshold can be misleading.
- Pick the threshold on validation data, using the cost of errors, not by default 0.5.

**See also:** [ML Fundamentals](../../learning/ai-machine-learning/ml-fundamentals.md)

</details>

---

## 8. How do you detect and handle model drift?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Model drift is a decline in a deployed model's performance because the data or the relationship it learned has changed. Detect it by monitoring prediction quality against labels when they arrive, and by tracking input and output distributions in the meantime. Handle it by investigating the cause, retraining on recent data, and redeploying only after the new model beats the current one on held-out recent data.

### Explanation
Drift comes in several forms:
- **Data drift (covariate shift)**: the distribution of inputs changes, such as new device types or payment methods, while the input-output relationship stays similar.
- **Concept drift**: the relationship between inputs and the target changes, such as new fraud tactics that make old signals misleading.
- **Label drift**: the distribution of the target changes, such as a shift in the proportion of positive cases.

Detection combines several signals:
- **Performance monitoring** against ground truth, where labels arrive with some delay. Set alerts on drops beyond an agreed threshold.
- **Distribution tests** on features and predictions, such as the Kolmogorov-Smirnov test for numeric features or population-stability measures.
- **Confidence monitoring**, where a drop in prediction confidence can signal unfamiliar inputs.
- **Targeted labelling**, where a sample of recent cases is reviewed by people to measure real error.

Handling drift follows a loop. Confirm the cause, since a broken upstream pipeline can look like drift. Retrain on a window of recent labelled data, possibly weighting recent examples more. Compare the candidate with the current model on recent data, run an A/B test or shadow deployment where feasible, and promote only if it is better. Feature engineering may also be needed when the world has changed in a new way.

### Response checklist
1. Confirm the alert is real: check upstream pipelines, schema changes, and label quality.
2. Identify the drift type and the segments where error grew.
3. Decide on the fix: adjust the threshold, retrain, add features, or roll back.
4. Validate the candidate on recent data and, where possible, in shadow mode.
5. Deploy with a rollback path and keep monitoring after the change.

### Likely follow-up
**How often should you retrain?** No interval fits every system. Use a schedule as a baseline, add a trigger when monitored metrics cross an agreed threshold, and confirm that the labelling pipeline can supply fresh labels fast enough to act on the trigger.

### When to use / pitfalls
- Input drift does not always hurt performance, and performance drops can occur without obvious input drift. Monitor both.
- Retraining on the latest data alone can absorb a labelling error or a temporary anomaly; review samples before retraining.
- Set the retraining policy in advance: a schedule, a performance trigger, or both.
- Keep versioned data, features, and models so you can roll back.

**See also:** [ML Fundamentals](../../learning/ai-machine-learning/ml-fundamentals.md), [AI in Java](../../learning/ai-machine-learning/ai-in-java.md)

</details>

---
