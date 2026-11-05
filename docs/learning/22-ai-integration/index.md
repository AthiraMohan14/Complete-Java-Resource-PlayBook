# AI Integration

Backend services increasingly call large language models (LLMs), search their own documents by meaning, and expose the results through APIs. This section covers the concepts behind those integrations: calling a model safely, grounding answers in your data with retrieval, storing embeddings, and using Spring AI in a Spring Boot service.

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

### [LLM Integration](llm-integration.md)
**prompts - context window - tokens - sampling - streaming - tool calling**
Call a text-generation model through a provider-neutral interface, control cost and output, and handle failure.

### [Retrieval-Augmented Generation and Vector Databases](rag-and-vector-databases.md)
**chunking - embeddings - similarity search - hybrid search - HNSW - pgvector**
Give a model the right passages from your own documents, and store and search embeddings efficiently.

### [Spring AI and Use Cases](spring-ai-use-cases.md)
**ChatClient - embeddings - tool-using agents - conversation memory - structured output**
Build chatbots, grounded question answering, and content tools with Spring AI, and know which use cases need the most care.

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

**See also:** [Part 4 roadmap, section 22](../../resources/full-stack-java-roadmap/part-4-design-interview-projects.md)
