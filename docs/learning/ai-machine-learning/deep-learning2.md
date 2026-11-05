# Deep Learning

Deep neural network architectures: multi-layer perceptrons, CNNs for vision, RNNs for sequences, LSTMs, attention, and training techniques.

---

## Neural Network Basics

### Perceptron (Single Neuron)

```
Inputs        Weights       Activation
  x₁  ─────→ w₁
  x₂  ─────→ w₂  ──→ Σ ──→ σ() ──→ Output
  x₃  ─────→ w₃
  
Output = σ(w₁x₁ + w₂x₂ + w₃x₃ + b)
where σ = activation function
```

**Activation Functions:**
```
Linear:         σ(z) = z                    (no non-linearity)
ReLU:           σ(z) = max(0, z)           (default for hidden)
Sigmoid:        σ(z) = 1/(1+e^-z)          (output for binary)
Tanh:           σ(z) = (e^z - e^-z)/(e^z + e^-z) (hidden layers)
Softmax:        σ(z_i) = e^z_i / Σe^z_j    (output for multi-class)
```

**Why activation?** Without non-linearity, stacking layers = single linear transformation. Activation enables learning complex patterns.

### Multi-Layer Perceptron (MLP)

```
Input Layer    Hidden Layer 1   Hidden Layer 2   Output Layer
   x₁ ─────────┐
   x₂ ──────┐─→[h₁]─────────┐
   x₃ ──┐─→[h₂]──┐      [h₃]─→ y (prediction)
        │    [h₃]─┘    [h₄]─┘
        └─────────────→

Depth: 3 layers (2 hidden + 1 output)
Width: Neurons per layer
Parameters: Weights + biases to learn
```

**Training via Backpropagation:**
```
1. Forward pass: x → predictions
2. Compute loss: Loss = Σ(predicted - actual)²
3. Backward pass: Compute gradients ∂Loss/∂w for each weight
4. Update weights: w = w - α * ∇Loss(w)  [α = learning rate]
5. Repeat on next batch
```

---

## Convolutional Neural Networks (CNNs)

Designed for **image data**; leverage spatial structure.

```
Input Image (32×32×3)
    ↓
Convolution (5×5 filter)  ← Learns edge/texture patterns
    ↓
ReLU Activation
    ↓
MaxPooling (2×2)  ← Downsample, keep important features
    ↓
[Repeat Conv → ReLU → Pool layers]
    ↓
Flatten to 1D
    ↓
Dense layers (classification)
    ↓
Output (probabilities for each class)
```

### Convolution Layer

```
Input (4×4)          Kernel/Filter (3×3)      Output (2×2)
[1 2 3 4]           [1 0]                [1*1+2*0+3*1  ...
[5 6 7 8]       ×   [1 1]        =        ...
[9 10 11 12]        
[13 14 15 16]

Process: Slide filter over input, compute dot product at each position
```

**Why CNN works for images:**
- Convolutional layers capture local patterns (edges, textures)
- Pooling reduces dimensions, captures translation invariance
- Stacking layers: early layers learn simple patterns, later layers combine them into complex objects

### Famous CNN Architectures
- **AlexNet (2012)**: First deep CNN, GPU-trained, ImageNet breakthrough
- **VGGNet (2014)**: Simple stacked 3×3 convolutions
- **ResNet (2015)**: Skip connections, enables very deep networks (152 layers)
- **Inception (2014)**: Multi-scale convolutions in parallel
- **MobileNet**: Efficient CNN for mobile/edge devices

---

## Recurrent Neural Networks (RNNs)

Designed for **sequence data** (text, time series, audio); maintains hidden state.

```
Input sequence: [x₁, x₂, x₃, x₄]

RNN:
h₀ (initial hidden state)
  ↓
[h₁] ← process x₁, output y₁
  ↓
[h₂] ← process x₂ using h₁, output y₂
  ↓
[h₃] ← process x₃ using h₂, output y₃
  ↓
[h₄] ← process x₄ using h₃, output y₄

Key: Hidden state h passes information through time
```

**Equation:**
```
h_t = tanh(W_hh * h_{t-1} + W_xh * x_t + b_h)
y_t = W_hy * h_t + b_y
```

**When to use:** Machine translation, sentiment analysis, speech recognition, time series forecasting

### LSTM (Long Short-Term Memory)

Standard RNNs suffer **vanishing gradient** problem: gradients shrink exponentially in backprop, can't learn long dependencies.

LSTM adds gates to control information flow:

```
         Forget Gate: Drop info from previous state
              ↓
     ╔════════════════╗
     ║  Cell State    ║ ← Information highway through time
     ║  (Memory)      ║
     ╚════════════════╝
              ↑
         Input Gate: Add new info
              
         Output Gate: What to pass to next step
```

**LSTM Cell:**
```
Forget:  f_t = σ(W_f * [h_{t-1}, x_t] + b_f)      (0=forget, 1=keep)
Input:   i_t = σ(W_i * [h_{t-1}, x_t] + b_i)      (relevance)
          C̃_t = tanh(W_c * [h_{t-1}, x_t] + b_c)  (candidate values)
Cell:    C_t = f_t * C_{t-1} + i_t * C̃_t          (update memory)
Output:  o_t = σ(W_o * [h_{t-1}, x_t] + b_o)
         h_t = o_t * tanh(C_t)                     (output to next)
```

**Benefits:** Learn long-range dependencies, handles vanishing gradient

### GRU (Gated Recurrent Unit)
Simpler than LSTM, often performs similarly.

---

## Attention Mechanism

Enable models to focus on relevant parts of input.

```
Query: "What's the capital of France?"
Context: "France is a country in Europe. Its capital is Paris. ..."

Attention: Compute similarity between query and each word
           Focus on "capital" and "Paris" (high attention weights)
           Ignore "country", "Europe" (low attention weights)

Output: Weighted combination of context words
```

**Scaled Dot-Product Attention:**
```
Attention(Q, K, V) = softmax(Q * K^T / √d_k) * V

Q (Query): What we're looking for
K (Keys): Database entries
V (Values): Information to return
Output: Weighted sum of values based on query-key similarity
```

**Why attention matters:**
- Transformer architecture built on attention (foundation of modern LLMs)
- Enables parallel processing (vs. sequential RNNs)
- Better handles long-range dependencies

---

## Training Deep Networks

### Backpropagation

Compute gradients efficiently using chain rule.

```
Loss → output layer → hidden layer → hidden layer → input layer

∂Loss/∂w_i = ∂Loss/∂y * ∂y/∂h_{layer3} * ∂h_{layer3}/∂h_{layer2} * ... * ∂h/∂w_i
```

**Efficiency**: Reuse intermediate gradients (dynamic programming style)

### Optimization Algorithms

| Algorithm | Update Rule | Pros | Cons |
|-----------|-------------|------|------|
| **SGD** | w = w - α∇L | Simple, stable | Slow, no adaptive |
| **Momentum** | v = βv + ∇L; w = w - αv | Faster, less noisy | Need tuning |
| **RMSprop** | v = ρv + (1-ρ)∇L²; w = w - α∇L/√v | Adaptive per parameter | Still needs tuning |
| **Adam** | m = β₁m + (1-β₁)∇L; v = β₂v + (1-β₂)∇L²; w = w - α*m/√v | Adaptive, robust, default | More hyperparams |

### Regularization Techniques

Prevent overfitting:

**L1/L2 Regularization:**
```
Loss = MSE + λ * (Σ|w| or Σw²)  [λ = regularization strength]
Effect: Shrink weights toward zero; L1 → sparse (some w=0), L2 → smooth
```

**Dropout:**
```
Training: Randomly drop neurons (probability p)
  [●] → [×] → [●]  (× = dropped)
  
Effect: Forces network to learn redundant representations; ensemble effect

Testing: Use all neurons but scale by (1-p)
  Ensures consistent expectations
```

**Early Stopping:**
```
Monitor validation loss during training
If validation loss increases → stop training
Prevent overfitting before it gets worse
```

**Batch Normalization:**
```
Normalize layer inputs to mean=0, std=1
Benefits: Faster training, allows higher learning rates, regularization effect
```

---

## Popular Architectures Summary

| Architecture | Task | Key Innovation | When to Use |
|--------------|------|-----------------|------------|
| **MLP** | Both | Non-linear layers | Baseline, structured data |
| **CNN** | Vision | Convolution, spatial invariance | Images, computer vision |
| **RNN** | Sequence | Recurrent hidden state | Time series, NLP |
| **LSTM** | Sequence | Gates for long dependencies | Long sequences, machine translation |
| **Transformer** | NLP | Self-attention, parallelizable | Modern NLP, LLMs |
| **ResNet** | Vision | Skip connections, very deep | Image classification, dense tasks |
| **U-Net** | Segmentation | Encoder-decoder with skip | Medical imaging, segmentation |

---

## Interview Talking Points

- **Why activation functions?** Without non-linearity, stacking layers = single linear transformation; ReLU enables complexity
- **CNN vs RNN?** CNN: spatial (images); RNN: temporal (sequences)
- **LSTM benefit over RNN?** Handles vanishing gradient; learns long-range dependencies via gates
- **Backpropagation intuition?** Compute gradients backwards using chain rule; update weights opposite gradient direction
- **Overfitting in deep networks?** More parameters = more capacity to memorize; use dropout, L1/L2, early stopping
- **Attention mechanism?** Compute similarity between query and context; weight values by relevance; foundation of Transformers
- **Optimization: SGD vs Adam?** SGD: simple, stable; Adam: adaptive learning rate per parameter, usually faster, default choice
- **Batch normalization benefit?** Faster training, allows higher learning rates, acts as regularization

---

**See also:** [ML Fundamentals](fundamentals.md), [ML Algorithms](algorithms.md), [LLMs & Transformers](llms-transformers.md)

**Practice questions:** [Machine Learning & AI](../interview-questions/verbal/verbal-ml-ai-questions.md)
