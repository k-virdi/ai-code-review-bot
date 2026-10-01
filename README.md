# PythonReviewBot — AI Code Review Copilot

> Paste Python code, tell it what the code should do, get a fixed version with tests, diff, and citations.

PythonReviewBot combines **RAG** over Python best practices with a **LangGraph multi-agent workflow**
(intake → diagnose → plan → generate → validate → critique → finalize) to review and fix Python code.

## Features
- Multi-agent workflow with retry loop and critic
- RAG: ChromaDB + BM25 + Reciprocal Rank Fusion
- Sandboxed validation with Ruff, Mypy, and pytest
- Automatic patch generation + unified diff
- FastAPI, Typer CLI, and Streamlit UI
- Trace of every agent step

## Architecture

```mermaid
flowchart TD
  U[User code + intent] --> I[Intake]
  I --> P[Parse AST] --> S[Static checks] --> R[RAG retrieve] --> D[Diagnose]
  D --> PL[Plan] --> G[Generate fix] --> T[Generate tests] --> V[Validate sandbox]
  V --> C{Critic}
  C -- retry --> G
  C -- ok --> F[Finalize report]
```

## Quickstart

```bash
git clone https://github.com/k-virdi/python-review-bot.git
cd python-review-bot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add OPENAI_API_KEY
make ingest           # build the RAG index
```

### CLI

```bash
prb examples/buggy/example_sort_users.py -i "Return a new list of unique users sorted by signup_date, without mutating input."
```

### API

```bash
make api
curl -X POST localhost:8000/review -H 'content-type: application/json' \
  -d '{"code":"def f(x):\n return x.sort()", "intent":"return sorted copy"}'
```

### UI

```bash
make ui
```

## Tech Stack
FastAPI · LangGraph · OpenAI · ChromaDB · BM25 · Rank-BM25 · tiktoken · Pydantic v2 ·
Ruff · Mypy · Pytest · Docker · Streamlit · Typer · Rich · GitHub Actions

## Roadmap
- [ ] GitHub Action that comments PRs
- [ ] Docker-based sandbox for untrusted code
- [ ] RAGAS eval harness
- [ ] Multi-file repo support
- [ ] Local LLM (Ollama) backend

## License
MIT
