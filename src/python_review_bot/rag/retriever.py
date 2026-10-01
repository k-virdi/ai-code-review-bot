"""Hybrid retriever: vector + BM25 + reciprocal rank fusion."""
from __future__ import annotations
from typing import Iterable
import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi

from ..config import get_settings
from ..models import RetrievedDoc


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in text.split() if len(t) > 2]


class HybridRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        chroma = chromadb.PersistentClient(path=self.settings.chroma_dir)
        self.collection = chroma.get_or_create_collection(self.settings.collection)

        data = self.collection.get(include=["documents", "metadatas"])
        self.docs: list[str] = data.get("documents") or []
        self.metas: list[dict] = data.get("metadatas") or []
        self.bm25 = BM25Okapi([_tokenize(d) for d in self.docs]) if self.docs else None

    def _embed(self, text: str) -> list[float]:
        r = self.client.embeddings.create(model=self.settings.embed_model, input=[text])
        return r.data[0].embedding

    def _vector_search(self, query: str, k: int) -> list[tuple[int, float]]:
        if not self.docs:
            return []
        emb = self._embed(query)
        res = self.collection.query(query_embeddings=[emb], n_results=k)
        ids = res.get("ids", [[]])[0]
        idxs: list[tuple[int, float]] = []
        for i, _id in enumerate(ids):
            try:
                idx = int(_id.split("-")[-1])
                idxs.append((idx, 1.0 / (i + 1)))
            except Exception:
                continue
        return idxs

    def _bm25_search(self, query: str, k: int) -> list[tuple[int, float]]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(_tokenize(query))
        top = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        return [(i, float(s)) for i, s in top if s > 0]

    @staticmethod
    def _rrf(rankings: list[list[tuple[int, float]]], k_const: int = 60) -> dict[int, float]:
        fused: dict[int, float] = {}
        for ranking in rankings:
            for rank, (idx, _score) in enumerate(ranking):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (k_const + rank + 1)
        return fused

    def retrieve(self, queries: Iterable[str], k: int | None = None) -> list[RetrievedDoc]:
        k = k or self.settings.top_k
        rankings: list[list[tuple[int, float]]] = []
        for q in queries:
            rankings.append(self._vector_search(q, k))
            rankings.append(self._bm25_search(q, k))
        if not rankings:
            return []
        fused = self._rrf(rankings)
        top = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        out: list[RetrievedDoc] = []
        for idx, score in top:
            if idx >= len(self.docs):
                continue
            meta = self.metas[idx] if idx < len(self.metas) else {}
            out.append(
                RetrievedDoc(
                    source=str(meta.get("source", "unknown")),
                    title=str(meta.get("title", "untitled")),
                    content=self.docs[idx],
                    score=score,
                )
            )
        return out
