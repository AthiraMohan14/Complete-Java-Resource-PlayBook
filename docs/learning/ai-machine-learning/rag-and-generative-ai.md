# RAG and Generative AI

Retrieval-augmented generation (RAG) fetches relevant passages from your own data and passes them to an LLM together with the question. The model answers from that context instead of relying on memory alone. Interviewers ask why RAG exists, how the pipeline works, how embeddings and vector search behave, and how you would evaluate the result.

!!! note "In simple words"
    RAG means looking up the right paragraphs first, then asking the model to answer using those paragraphs. The answer is grounded in your documents, and you can point to the source.

## Why it matters

An LLM knows only what it learned during training. Ask it about a private contract, last week's policy change, or your product catalogue, and it may invent a confident answer. RAG fixes that gap without retraining the model. You update the index when the documents change, and the system can cite where each claim came from. For most company knowledge problems, this is the first pattern to reach for.

## How it works

### Why RAG

An LLM's knowledge is fixed at training time and blended from many sources. RAG addresses the resulting problems:

- **Grounding**: the answer is based on passages you supply.
- **Freshness**: updating the index updates what the system knows, with no retraining.
- **Citations**: the answer can point to the passages it used.
- **Access control**: retrieval can filter documents by the user's permissions.

### The pipeline

RAG has two phases. The build phase runs offline or on a schedule. The query phase runs for each request.

```mermaid
flowchart TB
    subgraph Build[Build phase]
        D[Documents] --> C[Chunk]
        C --> E1[Embed chunks]
        E1 --> V[Vector index]
    end
    subgraph Query[Query phase]
        Q[User question] --> E2[Embed question]
        E2 --> S[Top k search]
        V --> S
        S --> P[Build prompt with passages]
        P --> L[LLM]
        L --> A[Answer with citations]
    end
```

The question must be embedded with the same model that embedded the chunks. Vectors from different models live in different spaces and cannot be compared.

### Chunking

Documents are split into chunks before embedding. Chunk size is a trade-off:

- Small chunks are specific, but they may lose the context needed to interpret them.
- Large chunks carry context, but they dilute the signal and use more of the prompt budget.

Common approaches are fixed-size windows with some overlap, and structure-aware splits on headings, paragraphs, or code blocks. A few hundred tokens is a common starting point, tuned with evaluation. Store metadata with each chunk, such as the source, section, date, and permissions, so you can filter and cite.

### Embeddings

An embedding model maps text to a dense vector, often a few hundred to a few thousand dimensions. Texts with similar meaning land near each other. Two properties matter in practice:

- Vectors from one model can only be compared with each other.
- Higher dimensions capture more nuance, but they cost more storage and search time.

Check each model's documentation for its dimension and its maximum input length. Domain-specific or multilingual needs may call for a different model than a general-purpose one.

### Similarity measures

- **Cosine similarity** compares direction and ignores length. It is `(a dot b) / (norm a times norm b)`, and it ranges from -1 to 1.
- **Dot product** equals cosine similarity when the vectors are normalised. Without normalisation it also rewards length.
- **Euclidean distance** measures straight-line distance. Smaller means closer.

A minimal top-k retrieval with cosine similarity. The Python example below is not compiled here, and it needs NumPy installed:

```python
import numpy as np

def top_k(query_vec: np.ndarray, doc_matrix: np.ndarray, k: int = 3):
    q = query_vec / np.linalg.norm(query_vec)
    d = doc_matrix / np.linalg.norm(doc_matrix, axis=1, keepdims=True)
    scores = d @ q
    best = np.argsort(scores)[::-1][:k]
    return best, scores[best]
```

### Exact versus approximate search

- **Exact search** compares the query with every vector. It is accurate and fine for small collections.
- **Approximate nearest neighbour (ANN)** search trades a little recall for much lower latency at scale. HNSW builds a layered proximity graph. IVF clusters the vectors and searches only the nearest clusters. Product quantisation compresses vectors to save memory.

ANN results can miss some true neighbours. Measure recall against exact search on a sample before you rely on it.

### Vector databases

A vector database stores vectors with metadata and serves filtered similarity queries. Options include dedicated systems such as Pinecone, Weaviate, Milvus, Qdrant, and Chroma, and extensions to existing databases such as pgvector for PostgreSQL. Choose on operational needs: managed or self-hosted, scale, filtering support, and the team's existing stack.

### Hybrid search and re-ranking

Vector search matches meaning, but it can miss exact tokens such as product codes or error IDs. Keyword ranking such as BM25 matches exact terms, but it misses paraphrases. Hybrid search combines both scores.

A re-ranker, typically a cross-encoder, then re-orders the top candidates by scoring each question and passage pair together. It adds latency, but it often improves precision at the top of the list.

```mermaid
flowchart LR
    Q[Question] --> A[Vector search]
    Q --> B[Keyword search]
    A --> M[Merge scores]
    B --> M
    M --> R[Re-ranker]
    R --> T[Top passages]
```

### Prompt construction

The prompt should separate the instructions, the retrieved passages, and the question. It should also say what to do when the passages do not contain the answer.

```text
You answer questions using only the passages below.
Cite passage IDs in square brackets. If the passages do not contain the
answer, reply exactly: "I could not find this in the documents."

Passages:
[P1] Employees accrue 1.5 days of leave per month worked.
[P2] Unused leave carries over for up to 12 months.

Question: How much leave do I earn each month?
```

Retrieved text is data, not instructions. A document can contain text that tries to override the system prompt. This is called indirect prompt injection. Treat retrieved content as untrusted, and limit which tools the model may invoke based on it.

### RAG versus fine-tuning

| Concern | RAG | Fine-tuning |
|---------|-----|-------------|
| Changing facts | Re-index the documents | Retrain the model |
| Source citations | Natural | Not built in |
| Style, format, or task behaviour | Limited | Strong |
| Per-request cost | Retrieval plus longer prompts | Usually lower per call once trained |
| Set-up effort | Pipeline, chunking, index | Labelled data and training runs |

Start with RAG when the knowledge changes or must be cited. Fine-tune when you need consistent behaviour or format that prompting cannot achieve. The two can be combined.

### Step by step

1. Collect and clean the documents, and record their metadata and access rules.
2. Chunk and embed them, then store the vectors and metadata in the index.
3. At query time, embed the question and apply metadata filters.
4. Retrieve the top k candidates, and optionally hybrid-search and re-rank them.
5. Build the prompt from instructions, passages, and the question.
6. Generate the answer, then check it: are citations present, and is the answer grounded in the passages?
7. Log queries, retrieved IDs, and answers for later evaluation.

### Evaluation

Measure retrieval and generation separately:

- **Retrieval**: recall at k (did the relevant chunk appear in the top k?), precision at k, and mean reciprocal rank.
- **Grounding (faithfulness)**: is every claim in the answer supported by the passages?
- **Answer relevance**: does the answer address the question?
- **Human review**: a sample of real questions, scored by people who know the domain.

Build a small labelled set of questions with known source passages early. It lets you compare chunk sizes, embedding models, and re-rankers with numbers rather than impressions. Lexical metrics such as BLEU and ROUGE are weak proxies for answer quality.

### Other generative AI patterns

- **Document Q&A** runs retrieval over manuals, contracts, or reports.
- **Support assistants** use retrieval over FAQs, tickets, and product documentation, with an escalation path.
- **Summarisation** uses map-reduce over chunks for long documents, or retrieves the relevant sections first.
- **Code assistance** uses retrieval over a repository, with tests as the check on generated code.
- **Content drafting** uses a model with a style guide and approved facts, and an editor reviews the output.

### LLM integration frameworks

Frameworks handle the repetitive parts of an LLM application: calling the model, splitting and embedding documents, talking to vector stores, and chaining steps together. You can build all of this by hand with an HTTP client and a vector library. A framework saves that plumbing, at the cost of an extra abstraction to learn and debug.

### LangChain

LangChain is a general framework for LLM applications. Its core idea is composition: small components, such as prompts, models, retrievers, output parsers, and tools, are joined into chains or agent loops. It covers many providers and vector stores behind shared interfaces, so swapping one model or store changes less code.

Use it when the application is more than retrieval. Typical cases are multi-step workflows, tool-calling agents, and apps that must switch between model providers.

### LlamaIndex

LlamaIndex, formerly called GPT Index, focuses on data. Its core idea is an index over your documents. It loads sources, parses and chunks them, builds indexes, and provides query engines that retrieve and answer. Its retrieval features, such as several index types and query routing, are its main strength.

Use it when the application is mainly question answering over a large body of documents and retrieval quality is the central problem.

### Comparison

| Concern | LangChain | LlamaIndex |
|---------|-----------|------------|
| Main focus | General orchestration of LLM steps and tools | Indexing and querying private data |
| Typical unit | Chain, agent, or graph of components | Index and query engine |
| Strongest fit | Workflows, agents, multi-provider apps | Document Q&A and retrieval-heavy apps |
| Retrieval | Available through retriever components | Central, with many index and query options |

The two overlap. Many teams use LlamaIndex for ingestion and retrieval inside a LangChain workflow, or they pick one and build the rest directly. Whichever you choose, keep the RAG concerns from this page in view. Chunking, metadata, evaluation, and access control remain your responsibility.

!!! note "Verify before you rely on it"
    Both projects change quickly, and their class names and import paths have moved between releases. Check the current documentation for the version you install, rather than copying older examples.

## Where it is used

- Internal knowledge bases, where employees ask questions about policies and procedures.
- Customer support assistants that answer from help articles and past tickets.
- Legal and contract review, where every answer must cite its clause.
- Engineering documentation search that answers from runbooks and API references.
- Product catalogue assistants that ground answers in current specifications.

## Benefits

- Answers stay current, because the index is updated without retraining.
- Citations let users check the source, which builds trust.
- Access control can filter retrieval, so each user sees only permitted content.
- The approach is cheaper to start and easier to reverse than fine-tuning.

## Cons and limits

- Answer quality depends on the quality of chunking and retrieval. Poor retrieval gives poor answers.
- Retrieved text adds tokens to every request, which raises cost and latency.
- The index can go stale if the sync job fails silently.
- Retrieved content can carry prompt injection, so it must be treated as untrusted.
- Evaluation takes effort, and it is easy to skip until quality problems appear.

## Best practices

- Keep chunks coherent: avoid splitting a table or a definition in half.
- Embed queries with the same model that embedded the documents.
- Schedule re-indexing, and monitor it so a stale index is noticed.
- Keep top k modest, so irrelevant passages do not drown the relevant ones.
- Give the model an explicit "not found" answer, so it does not guess.
- Return citations with every answer, so users can check them.
- Filter retrieval by the user's permissions before anything reaches the prompt.

!!! tip "Interview tip"
    **Q: When would you use LangChain instead of calling the model API directly?**
    When the workflow has several steps, tools, or provider swaps, a framework gives shared components and less glue code. For a single prompt with one model call, a direct API call is simpler, easier to debug, and has fewer dependencies. Say that you would adopt a framework only when its abstractions remove real complexity.

!!! tip "Interview tip"
    **Q: Why is RAG cheaper than fine-tuning for most knowledge problems?**
    Adding knowledge through retrieval changes only the index, which is quick and reversible. Fine-tuning needs a new training run for every change, and it can still hallucinate. RAG also gives citations. Fine-tuning is better for behaviour and format, not for facts that change.

## Quick recap

- RAG grounds answers in retrieved passages, which reduces hallucination and keeps knowledge current.
- The build phase chunks and embeds documents. The query phase embeds the question and retrieves the top k.
- Use the same embedding model for indexing and querying, and cosine similarity is the usual measure.
- ANN search trades a little recall for speed. Hybrid search and re-ranking improve precision.
- Evaluate retrieval and grounding separately, and treat retrieved text as untrusted input.

## Official documentation

- [LangChain documentation](https://python.langchain.com/docs/introduction/)
- [LlamaIndex documentation](https://docs.llamaindex.ai/)
- [Spring AI reference documentation](https://docs.spring.io/spring-ai/reference/index.html)

**See also:** [LLMs and Transformers](llms-and-transformers.md), [AI in Java](ai-in-java.md), [AI integration section](../22-ai-integration/index.md)
