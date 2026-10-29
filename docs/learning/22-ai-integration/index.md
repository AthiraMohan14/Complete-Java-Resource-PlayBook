# AI Integration

Backend services increasingly call large language models (LLMs), search their own documents by meaning, and expose the results through APIs. This section covers the concepts behind those integrations: calling a model safely, grounding answers in your data with retrieval, storing embeddings, and using Spring AI in a Spring Boot service.

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

**See also:** [Part 4 roadmap, section 22](../../resources/full-stack-java-roadmap/part-4-design-interview-projects.md)
