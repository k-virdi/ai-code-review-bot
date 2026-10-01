# RAG Pipeline

1. Ingest markdown from `data/knowledge/` → chunk by `##` headings.
2. Embed with OpenAI `text-embedding-3-small` → ChromaDB.
3. Retrieve: vector + BM25 → RRF fusion → top-k.
4. Augment: top-k chunks fed to diagnosis/generation prompts.

## Extending
Drop new `.md` files under `data/knowledge/` and run `make ingest`.
