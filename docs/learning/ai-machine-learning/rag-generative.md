# RAG & Generative AI

Retrieval-Augmented Generation (RAG) and generative AI patterns: embedding-based retrieval, vector databases, and LLM integration.

---

## The Hallucination Problem

Large language models generate confident but false information.

```
Question: "What was the main topic of Alice's speech in Q3 2024?"
LLM (without external info):
  "Alice focused on cloud migration strategies and 
   emphasized the importance of microservices architecture."

Reality: This is completely made up (hallucination)

Problem: Model can't distinguish between training knowledge 
         and new information; generates plausible-sounding answers
```

**Impact:**
- Medical AI giving wrong diagnoses
- Financial advice based on false data
- Legal analysis citing non-existent cases
- Customer support with invented policies

---

## Retrieval-Augmented Generation (RAG)

Combine LLM with **external retrieval** to ground responses in facts.

```
User Query: "What was the main topic of Alice's speech in Q3 2024?"

Step 1: RETRIEVE relevant documents
  Search knowledge base (company documents, PDFs, wiki)
  Find: [Speech_Q3_2024.pdf, Alice_Biography.txt, ...]
  
Step 2: CONTEXT
  Extract relevant passages from retrieved docs
  Context: "In her Q3 2024 speech, Alice discussed..."
  
Step 3: GENERATE with context
  Prompt = Context + Query + LLM instruction
  LLM: "Based on this context, answer the question..."
  Output: Answer grounded in actual documents

Result: Factual answer, cites sources, reduced hallucination
```

### RAG vs Fine-tuning

| Approach | Data Update | Training | Latency | Cost | Use Case |
|----------|------------|----------|---------|------|----------|
| **Fine-tune** | Retrain model | Hours-days | Fast | High | Permanent knowledge, frequent updates |
| **RAG** | Update retrieval DB | Minutes | Slower (retrieve+generate) | Lower | Dynamic knowledge, real-time data |

**Recommendation**: Start with RAG for speed and cost; fine-tune if latency-critical.

---

## Vector Embeddings

Convert text to dense vectors for similarity search.

### Word/Sentence Embeddings

```
Traditional: One-hot encoding
  "cat" = [0, 0, 1, 0, 0, ...]  (size = vocabulary)
  Issues: Sparse, no semantic similarity

Modern: Dense embeddings
  "cat" = [0.2, -0.5, 0.1, 0.9, 0.3]  (size = 384-4096)
  
Semantics: Similar words → similar vectors
  "cat" ≈ "kitten" (high cosine similarity)
  "cat" ≈ "dog" (moderate similarity)
  "cat" ≈ "mathematics" (low similarity)
```

### Embedding Models

```
OpenAI text-embedding-3-small:  1536 dimensions
OpenAI text-embedding-3-large:  3072 dimensions
Sentence-Transformers (BERT):   384 dimensions
Cohere Embed-English:           4096 dimensions

Trade-off: More dimensions = more expressive but slower, larger storage
```

### Computing Similarity

```
Cosine Similarity = (A · B) / (||A|| * ||B||)
Range: [-1, 1]
- 1.0: Identical direction (same meaning)
- 0.5: Somewhat similar
- 0.0: Orthogonal (different)
- -1.0: Opposite directions

Example:
  "Autonomous vehicle safety" embedding A
  "Self-driving car security" embedding B
  similarity(A, B) = 0.85  ← High similarity

  "Autonomous vehicle safety" embedding A
  "Breakfast recipes" embedding C
  similarity(A, C) = 0.02  ← Low similarity
```

---

## Vector Databases

Specialized databases optimized for similarity search.

### How Vector DB Works

```
Input text: "How do I reset my password?"

Step 1: Embed
  Embedding model: "How do..." → [0.1, -0.2, 0.5, ...]

Step 2: Store in vector DB
  DB indexed for fast similarity search
  
Step 3: Query
  New question: "Can't log in, forgot password"
  Embed: "Can't log..." → [0.09, -0.21, 0.51, ...]
  Search: Find vectors most similar to query
  
Step 4: Retrieve
  Top-K results (e.g., K=3)
  [FAQ_1: 0.92 similarity, FAQ_2: 0.88, FAQ_3: 0.85]
```

### Popular Vector Databases

| Database | Features | Pros | Cons |
|----------|----------|------|------|
| **Pinecone** | Cloud, fully managed | Easy setup, scalable | Vendor lock-in, cost |
| **Weaviate** | Open-source, self-hosted | Control, modular | Needs infrastructure |
| **Milvus** | Open-source, scalable | High performance, free | Complex deployment |
| **Chroma** | Lightweight, embedded | Simple for prototypes | Limited scale |
| **Qdrant** | Vector-native, fast | High throughput | Newer ecosystem |

### Vector Indexing Strategies

**Exact Search:** Compare query against all vectors
```
Time: O(n * d)  [n = num docs, d = embedding dim]
Accuracy: 100%
Suitable for: Small datasets (<1M docs)
```

**Approximate Nearest Neighbor (ANN):** Fast approximation
```
Algorithms: HNSW, IVF, LSH
Time: O(log n)
Accuracy: 95-99%
Suitable for: Large-scale (<100M+ docs)
```

---

## RAG Pipeline (End-to-End)

```
┌─────────────────────────────────────────┐
│  Build Phase (Once, offline)            │
└─────────────────────────────────────────┘

Input Documents
  ├─ PDFs (reports.pdf)
  ├─ Web pages (knowledge.html)
  ├─ Databases (select * from docs)
  └─ APIs (fetch latest data)
        ↓
   Chunking
   (Split into 512-token pieces)
        ↓
   Embedding
   (Convert chunks to vectors)
        ↓
   Store in Vector DB
   (Index for fast search)

┌─────────────────────────────────────────┐
│  Query Phase (Real-time)                │
└─────────────────────────────────────────┘

User Question
        ↓
   Embed Query
   (Same embedding model as docs)
        ↓
   Search Vector DB
   (Find most similar chunks, e.g., top-5)
        ↓
   Construct Prompt
   (System instruction + context chunks + query)
        ↓
   LLM Generation
   (Generate answer based on context)
        ↓
   Post-processing
   (Format, cite sources, validate)
        ↓
   Response to User
```

### Prompt Construction Example

```
System Prompt:
"You are a helpful assistant. Answer questions based on 
 the provided context. If context doesn't contain answer, 
 say 'I don't have this information.'"

Context (retrieved chunks):
"[Document 1] Alice's Q3 2024 speech focused on 
 cloud migration strategies and microservices..."
"[Document 2] The company achieved 40% cost reduction 
 through containerization..."

User Query:
"What was the main topic of Alice's speech?"

Final Prompt Sent to LLM:
"Based on this context:
 [Document 1] Alice's Q3 2024 speech focused on...
 [Document 2] The company achieved...
 
 Answer: What was the main topic of Alice's speech?"

LLM Output:
"Based on the context provided, Alice's Q3 2024 speech 
 focused on cloud migration strategies and microservices architecture."
```

---

## LLM Integration Frameworks

### LangChain
Modular framework for building LLM applications.

```python
from langchain.llms import OpenAI
from langchain.vectorstores import Pinecone
from langchain.chains import RetrievalQA

# Load documents, chunk, embed
documents = load_documents("docs/")
chunks = split_documents(documents, chunk_size=512)
embeddings = embed_documents(chunks)

# Store in vector DB
vectorstore = Pinecone.from_embeddings(embeddings)

# Create RAG chain
llm = OpenAI(model="gpt-3.5-turbo")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # stuff context into prompt
    retriever=vectorstore.as_retriever()
)

# Query
answer = qa_chain.run("What was Alice's speech about?")
```

### LlamaIndex (GPT Index)
Specialized for indexing and querying documents.

```python
from llama_index import GPTVectorStoreIndex, Document

# Load documents
documents = [Document(text="..."), ...]

# Create index
index = GPTVectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("Alice's speech topic?")
print(response)
```

---

## Generative AI Applications

### Document Q&A
Ask questions about documents without reading them all.

```
Use case: "What are the company's main risks according to 
          the 2024 annual report?"
RAG: Retrieve risk sections → Answer from context
```

### Chatbots
Conversational AI grounded in knowledge base.

```
Customer asks: "How do I troubleshoot my account?"
RAG: Retrieve FAQ/docs → Generate personalized response
```

### Summarization
Condense large documents.

```
Input: 50-page research paper
RAG: Extract key sections → LLM summarizes
```

### Code Generation
Generate code from requirements.

```
Prompt: "Write a function to validate email addresses"
LLM generates: Code with explanation
```

### Content Creation
Generate original content (articles, marketing copy).

```
Topic: "AI Safety"
LLM generates: Blog post, multiple angles, cited sources
```

---

## Best Practices

### Retrieval Quality
- **Chunk size**: Balance between specificity (small) and context (large); 256-512 tokens typical
- **Embedding model**: Use domain-specific if available; general models (text-embedding-3) work well for most
- **Indexing**: ANN for scale; exact search for small datasets
- **Top-K**: Retrieve more chunks to increase coverage (e.g., top-10 vs top-3)

### Generation Quality
- **System prompt**: Clear instructions reduce hallucination
- **Context length**: Limit context window to avoid confusion (e.g., top-5 chunks)
- **Temperature**: Lower (0.3-0.5) for factual questions; higher (0.7-0.9) for creative
- **Prompt engineering**: Few-shot examples, chain-of-thought improve output

### Evaluation
- **Retrieval metrics**: Precision, Recall (how many relevant docs retrieved?)
- **Generation metrics**: BLEU, ROUGE, semantic similarity
- **Human evaluation**: Most important; does answer satisfy user?

---

## Interview Talking Points

- **Why RAG?** Grounds LLM responses in facts; reduces hallucinations; adds real-time knowledge without retraining
- **Vector embedding intuition?** Dense representation captures semantic meaning; similar texts → similar vectors
- **Cosine similarity?** Measures angle between vectors; 1.0 = identical direction, 0 = orthogonal
- **RAG vs Fine-tune?** RAG: fast updates, flexible; Fine-tune: permanent knowledge, faster inference
- **Chunking strategy?** Size determines context richness vs specificity; 256-512 tokens common
- **Top-K tradeoff?** More chunks = higher coverage but more noise; typical 3-10 chunks
- **Prompt construction?** Context + system instruction + query; quality matters for good answers
- **Vector DB indexing?** Exact search O(n) for small data; ANN O(log n) for scale

---

**See also:** [LLMs & Transformers](llms-transformers.md), [AI & Java Integration](ai-java.md)

**Practice questions:** [Machine Learning & AI](../interview-questions/verbal/verbal-ml-ai-questions.md)
