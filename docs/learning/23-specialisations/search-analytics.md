# Search and Analytics

Search answers "which documents match these words, ranked by relevance?". Analytics answers "what do the totals and trends look like across a lot of data?". Interviewers ask about both when a system must handle queries that a primary transactional database serves poorly. This page covers Elasticsearch and Solr for search, and the basics of analytical storage.

## Core concepts

### Why not just use SQL LIKE?

A `LIKE '%term%'` query cannot use a normal B-tree index, scans every row, and ignores relevance. It also does not handle stemming ("running" matching "run"), synonyms, typos, or ranking by how well a document matches. A search engine builds a structure designed for those needs.

### The inverted index

The core structure is the **inverted index**: for each term, a sorted list of the documents that contain it (a posting list), along with positions and frequencies. A query looks up each query term, intersects or unions the lists, and scores the matching documents. The index is built at write time, so queries stay fast.

Text goes through an **analyzer** before indexing: a tokeniser splits it into terms, and filters lowercase them, remove stop words, and stem them. The same analyzer must run on the query side, or matching fails in confusing ways.

### Elasticsearch: full-text search and aggregations

**Elasticsearch** is a distributed search and analytics engine built on Lucene. It stores JSON documents in **indices**, and each index has **mappings** that define field types and analyzers. Important concepts:

- **Mapping:** decide whether a field is `text` (analysed, for full-text search) or `keyword` (exact, for filters and aggregations). Mapping mistakes are hard to fix later, because changing a field's type usually means reindexing.
- **Shards and replicas:** an index is split into shards spread across nodes, and replicas provide redundancy and read capacity.
- **Queries:** the query DSL combines full-text clauses (`match`), exact filters (`term`, `range`), and boolean logic.
- **Aggregations:** group and summarise results, such as counting orders by status or averaging price by category.

A query body that searches product names and filters by price and stock:

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "wireless headphones" } }
      ],
      "filter": [
        { "range": { "price": { "lte": 150 } } },
        { "term": { "inStock": true } }
      ]
    }
  },
  "aggs": {
    "by_brand": { "terms": { "field": "brand.keyword" } }
  }
}
```

Putting conditions under `filter` rather than `must` means they do not affect scoring and can be cached. That is a common and useful distinction.

### Relevance tuning

Elasticsearch scores matches with **BM25** by default, which weights terms by how rare they are across the collection and normalises for document length. You tune relevance by:

- Boosting important fields (a match in `title` counts more than in `description`)
- Using `function_score` or similar to add business signals such as popularity or recency
- Adding synonyms for domain terms
- Choosing analyzers that fit the language and the data
- Testing with a labelled set of queries and judged results, not by intuition

### Java access

Use the official Java client for Elasticsearch in your application code. Spring Data Elasticsearch offers repository-style access on top of it. Whichever you choose, keep index mappings under version control, and create indices through a deployment step rather than by hand in production.

### Apache Solr

**Apache Solr** is another search platform built on Lucene. It has similar core features (inverted indices, faceting, relevance scoring) and a different configuration model, using schema files and its own query syntax. Teams choose it for existing investments, specific features, or operational familiarity. The concepts transfer: analysers, fields, faceting, and relevance tuning work the same way in principle.

### Real-time analytics and data warehousing basics

Transactional databases (OLTP) serve many small reads and writes. Analytical systems (OLAP) scan large amounts of data to compute aggregates. Running heavy reports on the production transactional database slows the business, so analytics usually runs on a separate store.

Key ideas:

- **Columnar storage:** data is stored by column, so a query over three columns reads only those three. Common in analytical engines.
- **Star schema:** a central fact table (sales, events) joined to dimension tables (customers, products, dates).
- **Data warehouse:** a curated store for analysis, fed by pipelines (ETL or ELT) from operational systems.
- **Data lake:** raw files in object storage, often with a table format on top.
- **Real-time analytics:** engines that ingest streams and answer queries within seconds, trading some consistency for freshness.

Elasticsearch aggregations cover some analytical needs on search data. For large-scale reporting, a columnar analytical engine is the better tool.

## How it works

1. A document is sent to the search engine and passed through the analyzers for each `text` field.
2. Terms are written to the inverted index on the shards that own the document.
3. A query is analysed the same way, looked up in the index, and scored.
4. Filters narrow the candidates without affecting score.
5. Aggregations compute summaries over the matching set.
6. For analytics, changes flow from the transactional database through a pipeline into a columnar store, where reports run.

## Common pitfalls

- Using `text` fields for exact filters, or `keyword` fields for full-text search
- Changing a mapping in place and expecting old documents to change
- Analysers that differ between indexing and querying
- Putting business conditions in `must` instead of `filter`, which affects scoring and caching
- Running heavy analytical queries on the production OLTP database
- Treating the search index as the source of truth; it is a derived store and must be rebuildable
- Tuning relevance without a labelled evaluation set

!!! tip "Interview tip"
    **Q: How do you keep a search index in sync with the database?**
    A: Treat the index as a derived view. Publish change events from the database (through the outbox pattern, or change data capture), have an indexer consume them and update documents, and make the indexer idempotent. Keep the ability to rebuild the whole index from the source data, and monitor lag between the database and the index.

## Quick recap

- The inverted index maps terms to documents; analysers must match at index and query time
- Elasticsearch uses mappings, shards, and the query DSL; keep exact filters in `filter`
- BM25 is the default scoring; tune relevance with boosts, synonyms, and a labelled set
- Solr offers similar core capabilities with a different configuration model
- Analytics belongs on a separate, columnar store fed from operational systems

**See also:** [Advanced Patterns](advanced-patterns.md), [Machine Learning for Backend Engineers](ml-for-backend-engineers.md)
