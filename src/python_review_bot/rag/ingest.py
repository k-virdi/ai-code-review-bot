"""Chunk and embed the knowledge corpus into ChromaDB."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
import re
import chromadb
from openai import OpenAI

from ..config import get_settings


def _chunk_markdown(text: str, source: str) -> list[dict]:
    """Split on level-2 headings; keep code blocks intact."""
    chunks: list[dict] = []
    parts = re.split(r"\n(?=## )", text)
    for part in parts:
        part = part.strip()
        if len(part) < 40:
            continue
        title_match = re.match(r"#+\s*(.+)", part)
        title = title_match.group(1).strip() if title_match else source
        chunks.append({"text": part, "title": title, "source": source})
    return chunks


def _embed(client: OpenAI, model: str, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def ingest_directory(path: str | Path | None = None) -> int:
    """Ingest all markdown files in the knowledge dir. Returns number of chunks."""
    settings = get_settings()
    root = Path(path or settings.knowledge_dir)
    if not root.exists():
        raise FileNotFoundError(f"Knowledge dir not found: {root}")

    files = list(root.rglob("*.md"))
    all_chunks: list[dict] = []
    for f in files:
        all_chunks.extend(_chunk_markdown(f.read_text(encoding="utf-8"), str(f.relative_to(root))))
    if not all_chunks:
        return 0

    client = OpenAI(api_key=settings.openai_api_key)
    chroma = chromadb.PersistentClient(path=settings.chroma_dir)
    try:
        chroma.delete_collection(settings.collection)
    except Exception:
        pass
    coll = chroma.create_collection(settings.collection, metadata={"hnsw:space": "cosine"})

    batch = 64
    for i in range(0, len(all_chunks), batch):
        window = all_chunks[i : i + batch]
        texts = [c["text"] for c in window]
        embeddings = _embed(client, settings.embed_model, texts)
        coll.add(
            ids=[f"chunk-{i + j}" for j in range(len(window))],
            documents=texts,
            embeddings=embeddings,
            metadatas=[{"title": c["title"], "source": c["source"]} for c in window],
        )
    return len(all_chunks)
