# LLMs & Transformers

Large language models built on Transformer architecture: attention mechanisms, pre-training, fine-tuning, and prompt engineering.

---

## Transformer Architecture

Foundation of all modern LLMs (GPT, BERT, Claude, etc.).

```
Input: "The cat sat on the mat"
  ↓
Tokenization: ["The", "cat", "sat", "on", "the", "mat"]
  ↓
Embedding: Convert tokens to vectors (d_model dimensions)
  ↓
┌─────────────────────────────────┐
│   Encoder/Decoder Stack         │  ← Multiple layers (6-96)
│  ┌──────────────────────────┐   │
│  │ Multi-Head Attention     │   │
│  │ (attends to all positions)   │
│  ├──────────────────────────┤   │
│  │ Feed-Forward Network     │   │
│  │ (Dense layers)           │   │
│  ├──────────────────────────┤   │
│  │ Add & Norm (residuals)   │   │
│  └──────────────────────────┘   │
│  [Repeated N times]             │
└─────────────────────────────────┘
  ↓
Output: Prediction for next token
```

### Self-Attention Mechanism

Compute relevance between all positions.

```
Sentence: "The cat sat on the mat"
           1    2   3   4   5   6

Attention for "sat" (position 3):
- How relevant is "The"? Low
- How relevant is "cat"? High (subject)
- How relevant is "sat"? Very high (itself)
- How relevant is "on"? High (preposition)
- How relevant is "the"? Low
- How relevant is "mat"? High (object)

Weighted output: Combination of all words, weighted by relevance
```

**Scaled Dot-Product Attention:**
```
Query (Q): "What am I looking for?"
Key (K):   "What does each word represent?"
Value (V): "Actual content of each word"

Attention(Q, K, V) = softmax(Q*K^T / √d_k) * V

Steps:
1. Compute Q*K^T (similarity between all pairs)
2. Scale by √d_k (stabilize gradients)
3. Apply softmax (convert to probabilities)
4. Weight values by attention weights
5. Output: Context-aware representation
```

### Multi-Head Attention

Multiple attention mechanisms in parallel.

```
Input: [d_model dimensions]
  ↓
├→ Head 1: Attention(Linear(x))  → [d_k dimensions]
├→ Head 2: Attention(Linear(x))  → [d_k dimensions]
├→ Head 3: Attention(Linear(x))  → [d_k dimensions]
└→ Head N: Attention(Linear(x))  → [d_k dimensions]
  ↓
Concatenate: [d_model dimensions]

Benefit: Attend to different representation subspaces simultaneously
Example: Head 1 attends to syntax, Head 2 to semantics, etc.
```

### Positional Encoding

Transformers process tokens in parallel (unlike RNNs). Need to encode position.

```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

Effect: Each position gets unique encoding
"The cat" ≠ "cat The" (order matters)
```

---

## BERT (Pre-training Paradigm)

**Bidirectional Encoder Representations from Transformers**

```
Traditional training: Train model from scratch on specific task
  Input data → Model → Loss → Gradient → Update
  [Limited by task-specific data]

BERT approach:
Step 1: PRE-TRAIN on massive unlabeled corpus
  - Masked Language Model (MLM): Hide 15% of words, predict them
  - Next Sentence Prediction (NSP): Predict if two sentences consecutive
  Result: Learn language patterns, grammar, semantics

Step 2: FINE-TUNE on specific downstream task
  - Add task-specific layers on top
  - Train on labeled data (much smaller)
  Result: Transfer knowledge, faster convergence, better performance
```

**Key Innovation: Bidirectional**
```
Previous models (like GPT-1): Left-to-right only
  "The cat sat on the ___"  (can only look back)

BERT: Bidirectional
  "The ____ sat on the mat"  (look at both sides)
  Context from both directions → better understanding
```

**Performance Impact:**
```
Training from scratch (on 1M labeled examples):
  Accuracy: 85%

BERT fine-tuning (on same 1M):
  Accuracy: 92%

Reason: Transfer learning from billions of tokens
```

---

## GPT (Generative Pre-trained Transformer)

**Autoregressive Language Model** (generate text token-by-token)

```
Prompt: "Paris is the capital of"

GPT:
Step 1: "Paris is the capital of" → Predict next: "France"
Step 2: "Paris is the capital of France" → Predict: "."
Step 3: "Paris is the capital of France." → Predict: [END]

Output: "Paris is the capital of France."
```

### GPT Evolution

| Model | Year | Params | Training Data | Key Features |
|-------|------|--------|---------------|--------------|
| **GPT-1** | 2018 | 117M | BookCorpus (1.2B tokens) | Decoder-only, left-to-right |
| **GPT-2** | 2019 | 1.5B | Web (40GB) | Few-shot learning, text generation |
| **GPT-3** | 2020 | 175B | Web + books (570B tokens) | In-context learning, API-first |
| **GPT-3.5** | 2022 | ~175B | Filtered web + books | RLHF training, ChatGPT backbone |
| **GPT-4** | 2023 | ?200-300B? | Not disclosed | Multimodal, improved reasoning |

**Scaling Laws:**
```
Larger model + More data = Better performance
(Emergent abilities appear at certain scales)

GPT-1 → GPT-2: More data, better text generation
GPT-2 → GPT-3: 100x scale → In-context learning emerges
GPT-3 → GPT-4: Multimodal + better reasoning
```

---

## Pre-training vs Fine-tuning

### Pre-training
Unsupervised learning on massive unlabeled corpus.

```
Objective: Predict masked tokens
Input: "The [MASK] sat on the mat"
Model learns: Language patterns, world knowledge, reasoning
Time: Weeks/months on massive compute (100s of GPUs)
Cost: Millions of dollars
```

**Pre-training Tasks:**
- **Masked Language Modeling (BERT)**: Hide tokens, predict them
- **Causal Language Modeling (GPT)**: Predict next token (left-to-right)
- **Contrastive Learning**: Embeddings of similar texts close, dissimilar far

### Fine-tuning
Supervised learning on task-specific labeled data.

```
Task: Sentiment analysis
Labels: [("Great movie!", positive), ("Boring", negative), ...]

Traditional: Train on 10k labeled examples
RLHF Fine-tune (LLMs): 
  1. Supervised fine-tuning: Train on 10k examples
  2. Reinforcement Learning from Human Feedback (RLHF):
     a. Model generates responses
     b. Humans rate quality
     c. Train reward model from ratings
     d. Fine-tune to maximize reward
     
Result: Model aligns with human preferences
```

**Comparison:**

| Task | Pre-train Only | Fine-tune | RLHF |
|------|---|---|---|
| Accuracy on task | ~70% | ~92% | ~95% |
| Time | Weeks | Hours | Days |
| Data needed | Billions tokens | 10k labeled | 10k labels + human feedback |

---

## Prompt Engineering

Guide LLMs to produce better outputs without fine-tuning.

### Few-Shot Prompting
Provide examples in prompt.

```
One-shot example:
Prompt: "Translate English to French:
         Hello → Bonjour
         Goodbye → ?"
Output: "Au revoir"

Few-shot (3 examples):
Prompt: "Classify sentiment:
         Great movie! → Positive
         Terrible → Negative
         It's okay → Neutral
         I loved it → ?"
Output: "Positive"
```

### Chain-of-Thought (CoT)
Ask model to explain reasoning step-by-step.

```
Bad prompt: "What's 3+5?"
Output: "8"
(Could be wrong)

Chain-of-Thought:
Prompt: "Solve step-by-step: 3+5 = ?"
Output: "3+5: First add 3, then add 5 more. 3+5 = 8"
(Better, shows reasoning)
```

### System Prompt
Set model's behavior/role.

```
System: "You are a helpful coding assistant. Answer technically and concisely."

User: "How do I reverse a string in Python?"
Assistant: "Use slicing: s[::-1]"
```

### Role-Playing
Assign role to model.

```
Prompt: "You are a professional financial advisor. 
         Given $10k, what should I invest in?"

Effect: Model responds professionally, considers risk, explains rationale
```

### Temperature & Top-K Sampling
Control randomness.

```
Temperature = 0: Deterministic (always pick highest probability)
Temperature = 1: Balanced randomness
Temperature = 2: Very random (creative but less accurate)

Top-K: Sample from K most likely tokens
Top-K=5: Only consider top 5 predictions, ignore tail
Effect: Prevent absurd predictions while allowing creativity
```

---

## Model Capabilities & Limitations

### Capabilities (Large Models)

✅ **In-Context Learning**: Learn from examples in prompt (no fine-tuning)  
✅ **Reasoning**: Chain-of-thought enables multi-step problem solving  
✅ **Code Generation**: Write, debug, explain code  
✅ **Translation**: Across languages, even low-resource  
✅ **Summarization**: Extract key points  
✅ **Creativity**: Stories, poetry, brainstorming  

### Limitations

❌ **Hallucinations**: Confidently generate false information  
```
Q: "Who won the Superbowl in 2050?"
A: "Tom Brady and the Patriots defeated the Chiefs 35-21"
(Completely made up, sounds plausible)
```

❌ **Knowledge Cutoff**: Only knows data from training date  
```
Q: "What happened in world news today?"
A: "I don't have access to real-time information"
```

❌ **Reasoning Limits**: Struggles with very long chains of logic  
```
Multi-step reasoning (>5 steps) error rate increases
```

❌ **Bias**: Training data reflects historical biases  
```
Gender, racial, cultural biases present in outputs
```

❌ **Context Limits**: Can't process infinitely long inputs  
```
Token limits: GPT-4 = 128k tokens (~100k words)
```

### Mitigation Strategies

- **RAG (Retrieval-Augmented Generation)**: Ground in external documents (reduces hallucination)
- **Chain-of-Thought**: Improve reasoning via step-by-step prompts
- **RLHF**: Align with human values
- **Fine-tuning**: Customize for domain
- **Temperature control**: Balance accuracy vs creativity

---

## Interview Talking Points

- **Transformer advantage over RNN?** Attention enables parallel processing; RNN sequential; Transformers learn long-range dependencies better
- **BERT vs GPT paradigm?** BERT: bidirectional, encoder, understand context; GPT: unidirectional, decoder, generate text
- **Pre-train vs Fine-tune?** Pre-train: learn language from billions tokens; Fine-tune: specialize on task with 10k labels
- **Why attention?** Compute relevance between all token pairs; weights determine which words influence each other
- **Hallucination problem?** LLM generates plausible-sounding but false information; mitigate with RAG, RLHF, temperature control
- **Prompt engineering?** Few-shot examples, chain-of-thought, system prompts guide model without fine-tuning
- **Scaling laws?** Larger models + more data = better performance; emergent abilities at certain scales (e.g., GPT-3)
- **RLHF purpose?** Align model with human preferences; train reward model from human feedback; optimize for alignment

---

**See also:** [ML Fundamentals](fundamentals.md), [Deep Learning](deep-learning.md), [RAG & Generative AI](rag-generative.md)

**Practice questions:** [Machine Learning & AI](../interview-questions/verbal/verbal-ml-ai-questions.md)
