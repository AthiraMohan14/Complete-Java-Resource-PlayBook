# AI and Machine Learning

Machine learning fundamentals and algorithms, deep learning, transformers and LLMs, retrieval-augmented generation, and using AI from Java.

---

## AI/ML Evolution & Milestones

### **Phase 1: Foundations (1956–1980s)**
- **1956**: Dartmouth Summer Research Project — "AI" term coined; optimism about solving intelligence
- **1966–1974**: First AI Winter — unrealistic expectations, limited computing power
- **1980s**: Expert Systems boom — knowledge-based AI for specific domains (medical diagnosis, financial)
- **Key tech**: Symbolic AI, rule-based systems, logic programming

### **Phase 2: ML Emergence (1990s–2000s)**
- **1990s**: Shift from symbolic AI to statistical ML — learning from data vs. handcoded rules
- **Key algorithms**: Decision trees, SVM (Support Vector Machines), Naive Bayes, ensemble methods (Random Forest)
- **1997**: Deep Blue defeats Kasparov at chess — symbolic AI milestone
- **2000s**: Probabilistic graphical models, Bayesian networks
- **Key datasets**: ImageNet starts (2009) — catalyst for deep learning

### **Phase 3: Deep Learning Revolution (2010s)**
- **2012**: AlexNet wins ImageNet competition — CNN breakthrough with GPU acceleration
- **2011–2015**: ResNets, VGGNets, Inception — deep convolutional architectures
- **2014**: GAN (Generative Adversarial Networks) — adversarial training paradigm
- **2015**: LSTM/GRU maturity — RNNs for sequences (NLP, time series)
- **2016**: AlphaGo defeats Lee Sedol — reinforcement learning milestone
- **Key enablers**: GPUs (NVIDIA), large datasets, open frameworks (TensorFlow 2015, PyTorch 2016)

### **Phase 4: Attention & Transformers (2017–2019)**
- **2017**: "Attention is All You Need" paper — Transformer architecture
  - Self-attention mechanism replaces RNNs
  - Enables parallel processing, better for long sequences
  - Foundation for all modern LLMs
- **2018**: BERT (Bidirectional Encoder Representations from Transformers)
  - Pre-training on massive unlabeled text
  - Fine-tuning for downstream NLP tasks
  - Paradigm shift: pre-train then fine-tune (vs. training from scratch)
- **2019**: GPT-2 (OpenAI) — large language model, remarkable text generation
  - 1.5B parameters
  - "Few-shot learning" ability without fine-tuning
- **Key insight**: Scale matters — bigger models + more data = emergent capabilities

### **Phase 5: Large Language Models (LLMs) Era (2020–2023)**
- **2020**: GPT-3 (OpenAI)
  - 175B parameters
  - In-context learning: prompt → immediate answer (no fine-tuning)
  - Enables: code generation, reasoning, question-answering, translation
  - API-first model (not open-sourced)
- **2022**: ChatGPT (OpenAI)
  - Conversational interface to GPT-3.5
  - RLHF (Reinforcement Learning from Human Feedback) — align model with user intent
  - 100M users in 2 months — AI enters mainstream
- **2022**: BLOOM (BigScience)
  - 176B parameters
  - Open-source alternative to GPT-3
- **2023**: GPT-4 (OpenAI)
  - Multimodal (text + images)
  - Better reasoning, reduced hallucinations
  - System prompts for behavior control
- **2023**: Open-source explosion
  - LLaMA (Meta) — 7B–65B models, high-quality
  - Mistral (8x7B MoE) — mixture of experts
  - Vicuña, Alpaca — fine-tuned variants
  - Enabled: local inference, customization, privacy-preserving deployments

### **Phase 6: RAG & Grounding (2023–Present)**
- **Problem**: LLMs hallucinate (confidently generate false information)
- **Solution**: Retrieval-Augmented Generation (RAG)
  - Query → Retrieve relevant documents → Feed to LLM with context → Answer
  - Grounds LLM in external knowledge, reduces hallucinations
- **Key tech**: 
  - Vector embeddings (dense representations)
  - Vector databases (Pinecone, Weaviate, Milvus)
  - Similarity search (cosine, dot product)
- **Applications**: 
  - Document Q&A systems
  - Knowledge base integration
  - Up-to-date information (vs. static training data)
- **Frameworks**: LangChain, LlamaIndex (formerly GPT Index)

### **Phase 7: Multimodal & Multi-Agent AI (2024–Present)**
- **Multimodal**: Models handle text + images + audio + video
  - GPT-4V (vision), Gemini (Google), Claude 3 (Anthropic)
- **Multi-Agent Systems**:
  - LLM agents with tools (web search, code execution, APIs)
  - Agent orchestration: planning, reasoning, error recovery
  - Example: AutoGPT, BabyAGI, LLM-powered autonomous systems
- **Fine-tuning at scale**:
  - LoRA (Low-Rank Adaptation) — efficient fine-tuning
  - QLoRA — quantized + LoRA for consumer hardware
- **Emerging**: Mixture of Experts (MoE), Sparse transformers, efficient inference

### **Phase 8: Specialization & Production (2024–2025)**
- **Domain-specific models**: Medical LLMs, legal LLMs, code LLMs (Codex, DeepSeek Coder)
- **Edge & Mobile AI**: On-device inference for privacy and latency
- **Synthetic Data**: Generated data for training when real data is scarce
- **Model Compression**: Distillation, pruning, quantization for faster inference
- **AI Safety & Alignment**: 
  - Constitutional AI
  - Interpretability research
  - Red-teaming and adversarial robustness

### **Key Insights Across Phases**

| Era | Focus | Driver | Bottleneck |
|-----|-------|--------|-----------|
| 1956–1980s | Symbolic AI, reasoning | Logic & rules | Limited computing, no data |
| 1990s–2000s | Statistical ML | Learning from data | Small datasets, handcrafted features |
| 2010s | Deep Learning | GPU acceleration | Need for labeled data, black box |
| 2017–2019 | Transformers & pre-training | Attention mechanism | Compute cost, fine-tuning overhead |
| 2020–2023 | Large scale LLMs | Scale hypothesis | Hallucinations, cost, alignment |
| 2023–Present | RAG & grounding, agents | Retrieval + reasoning | Latency, multi-step reasoning |
| 2024–2025 | Specialization, efficiency | Domain adaptation | Energy, real-time inference |

---

## Topics

### [Machine Learning Fundamentals](ml-fundamentals.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Machine learning fits a model to data so that it can predict outcomes or uncover structure without hand-written rules. Interviewers start here because later topics (algorithms,...

### [ML Fundamentals](fundamentals.md)
**Supervised Learning - Unsupervised Learning - Reinforcement Learning - Overfitting/Underfitting - Cross-Validation - Feature Engineering**  
Core concepts: supervised vs unsupervised learning, regression and classification, training/validation/test splits, hyperparameter tuning, feature scaling and selection.

### [Machine Learning Algorithms](ml-algorithms.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Classical algorithms remain the first tool for tabular data: linear models, decision trees, ensembles of trees, support vector machines, and clustering. Interviewers ask how...

### [ML Algorithms](algorithms.md)
**Linear/Logistic Regression - Decision Trees - Random Forests - SVM - KMeans - Gradient Descent - Loss Functions**  
Common algorithms: decision trees and ensemble methods, clustering algorithms, support vector machines, optimization techniques, when to use each algorithm.

### [Deep Learning](deep-learning1.md)
**Neural Networks - Backpropagation - CNNs - RNNs - LSTMs - Activation Functions - Dropout/Batch Normalization**  
Deep neural network architectures: convolutional networks for vision, recurrent networks for sequences, attention mechanisms, training techniques.

### [Deep Learning](deep-learning2.md)
**Core concepts - Convolutional neural networks - Recurrent neural networks - Attention - Architecture summary**
Deep learning stacks many layers of learned transformations, so the model builds its own features from raw inputs such as pixels, audio, and text. Interviewers expect you to...

### [LLMs and Transformers](llms-and-transformers.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Large language models (LLMs) are transformer networks trained on very large text corpora to predict tokens. Interviewers ask about the transformer block, why self-attention...

### [LLMs & Transformers](llms-transformers.md)
**Transformers - Attention Mechanism - BERT - GPT - Fine-tuning - Prompt Engineering - LLM Basics**  
Large language models: transformer architecture, self-attention, pre-training and fine-tuning, prompt engineering strategies, model capabilities and limitations.

### [RAG and Generative AI](rag-and-generative-ai.md)
**Core concepts - How it works / Step by step - Evaluation - Other generative AI patterns - Common pitfalls**
Retrieval-augmented generation (RAG) fetches relevant passages from your own data and passes them to an LLM with the question. The model answers from that context instead of...

### [RAG & Generative AI](rag-generative.md)
**Retrieval Augmented Generation - Vector Databases - Embeddings - Semantic Search - LLM Integration - AI Applications**  
Generative AI patterns: combining LLMs with retrieval systems, vector embeddings and similarity search, building AI-powered applications.

### [AI in Java](ai-in-java.md)
**Core concepts - How it works / Step by step - Production considerations - Common pitfalls - Quick recap**
Most Java teams do not train models. They load a trained model for inference, or call a hosted LLM over HTTP, and wrap the call in ordinary service code. Interviewers ask where...

### [AI & Java Integration](ai-java.md)
**TensorFlow Java - DL4J - Spring AI - LLM APIs - Model Serving - Production AI**  
Integrating AI in Java applications: TensorFlow and DL4J for model inference, Spring AI framework, calling LLM APIs, deploying models at scale.

### More in this section

### [AI and Machine Learning: History and Milestones](history-and-milestones.md)
**Core concepts - How it works / Step by step - Common pitfalls - Quick recap**
Artificial intelligence has moved through cycles of high expectations, disappointment, and renewed progress. Each shift had a clear driver: better algorithms, more data, or...

---

## Quick Interview Prep

**ML Fundamentals:**
- **Supervised vs Unsupervised**: Supervised has labeled data (regression, classification); Unsupervised finds patterns (clustering, dimensionality reduction)
- **Overfitting vs Underfitting**: Overfitting: model memorizes data (high train loss, high test loss); Underfitting: model too simple (high both)
- **Train/Validation/Test Split**: Typical 70/15/15 or 80/10/10; validation for hyperparameter tuning, test for final evaluation

**Deep Learning:**
- **CNN vs RNN**: CNN for images (spatial features); RNN for sequences (temporal dependencies)
- **Backpropagation**: Compute gradients via chain rule; update weights to minimize loss
- **Activation Functions**: ReLU (default), Sigmoid (0-1), Tanh (-1 to 1); enable non-linearity

**LLMs & Transformers:**
- **Attention Mechanism**: Query-Key-Value computation; allows model to focus on relevant tokens
- **Tokenization**: Breaking text into tokens; affects input size and processing
- **Prompt Engineering**: Write effective prompts; chain-of-thought, few-shot learning, role-playing

**RAG:**
- **Why RAG?**: Grounds LLM responses in retrieved documents; reduces hallucinations; adds current information
- **Vector Embeddings**: Dense vector representation of text; similarity search via cosine/dot product
- **Workflow**: Query → Retrieval → Context → LLM → Response

**AI in Java:**
- **TensorFlow Java**: Load and run pre-trained models; inference only (training is Python)
- **Spring AI**: Abstraction over LLM APIs (OpenAI, Anthropic, etc.)
- **Model Serving**: TensorFlow Serving, Triton for production model deployment

