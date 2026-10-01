# Architecture

PythonReviewBot is a LangGraph-based agentic system with a RAG layer.

## Layers
- Interfaces: FastAPI, Typer CLI, Streamlit
- Agents: intake → parse → static → retrieve → diagnose → plan → generate → tests → validate → critique → finalize
- Tools: AST, Ruff, Mypy, subprocess sandbox, unified diff
- RAG: ChromaDB vector store + BM25 with Reciprocal Rank Fusion
- LLM: OpenAI Chat Completions with JSON mode for structured steps

## Diagram

```mermaid
flowchart TD
  U[User code + intent] --> I[Intake]
  I --> P[Parse AST]
  P --> S[Static checks]
  S --> R[Retrieve RAG]
  R --> D[Diagnose]
  D --> PL[Plan]
  PL --> G[Generate fix]
  G --> T[Generate tests]
  T --> V[Validate sandbox]
  V --> C{Critic}
  C -- retry --> G
  C -- ok --> F[Finalize report]
