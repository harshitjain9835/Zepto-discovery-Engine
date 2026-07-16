"""Simple pluggable vector store helpers.

Provides:
- `VectorStoreBase` abstract interface
- `InMemoryVectorStore` fast in-memory store for testing
- `SQLiteVectorStore` small file-backed store (embeddings stored as JSON)
- similarity helpers and `embed_and_upsert` convenience helper

This is a lightweight, dependency-free prototype useful for testing
and local development. It's intentionally simple: queries compute
similarity in Python. Replace with a production vector DB (Milvus,
FAISS, Pinecone, Weaviate, etc.) for large datasets.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _normalize_vector(v: Sequence[float]) -> List[float]:
    v = list(v)
    norm = math.sqrt(sum(x * x for x in v))
    if norm == 0:
        return v
    return [x / norm for x in v]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    # Ensure same length
    if len(a) != len(b):
        # Truncate to shortest
        n = min(len(a), len(b))
        a = a[:n]
        b = b[:n]
    # Use normalized vectors for stable cosine
    na = _normalize_vector(a)
    nb = _normalize_vector(b)
    return sum(x * y for x, y in zip(na, nb))


@dataclass
class VectorRecord:
    id: str
    embedding: List[float]
    metadata: Dict[str, Any]


class VectorStoreBase:
    """Abstract-ish interface for vector stores used in this repo."""

    def upsert(self, records: Iterable[VectorRecord]) -> None:
        raise NotImplementedError()

    def query(self, vector: Sequence[float], top_k: int = 10) -> List[Tuple[VectorRecord, float]]:
        raise NotImplementedError()

    def delete(self, ids: Iterable[str]) -> None:
        raise NotImplementedError()


class InMemoryVectorStore(VectorStoreBase):
    def __init__(self):
        self._store: Dict[str, VectorRecord] = {}

    def upsert(self, records: Iterable[VectorRecord]) -> None:
        for r in records:
            # store normalized copy for faster queries
            self._store[r.id] = VectorRecord(r.id, _normalize_vector(r.embedding), r.metadata or {})

    def query(self, vector: Sequence[float], top_k: int = 10) -> List[Tuple[VectorRecord, float]]:
        q = _normalize_vector(vector)
        scores: List[Tuple[float, VectorRecord]] = []
        for rec in self._store.values():
            score = sum(x * y for x, y in zip(q, rec.embedding[: len(q)]))
            scores.append((score, rec))
        scores.sort(key=lambda t: t[0], reverse=True)
        return [(rec, float(score)) for score, rec in scores[:top_k]]

    def delete(self, ids: Iterable[str]) -> None:
        for _id in ids:
            self._store.pop(_id, None)


class SQLiteVectorStore(VectorStoreBase):
    """A tiny file-backed vector store storing embeddings and metadata as JSON.

    Note: queries are computed in Python by scanning rows. This is fine for
    development and small datasets; switch to a proper vector DB for scale.
    """

    def __init__(self, path: str = "data/vector_store.db"):
        self.path = path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                metadata TEXT
            )
            """
        )
        self._conn.commit()

    def upsert(self, records: Iterable[VectorRecord]) -> None:
        cur = self._conn.cursor()
        for r in records:
            cur.execute(
                "REPLACE INTO vectors (id, embedding, metadata) VALUES (?, ?, ?)",
                (r.id, json.dumps(list(r.embedding)), json.dumps(r.metadata or {})),
            )
        self._conn.commit()

    def query(self, vector: Sequence[float], top_k: int = 10) -> List[Tuple[VectorRecord, float]]:
        q = _normalize_vector(vector)
        cur = self._conn.cursor()
        cur.execute("SELECT id, embedding, metadata FROM vectors")
        rows = cur.fetchall()
        scored: List[Tuple[float, VectorRecord]] = []
        for _id, emb_json, meta_json in rows:
            emb = json.loads(emb_json)
            # truncate or pad as needed
            n = min(len(emb), len(q))
            if n == 0:
                score = 0.0
            else:
                score = cosine_similarity(q[:n], emb[:n])
            rec = VectorRecord(_id, _normalize_vector(emb), json.loads(meta_json) if meta_json else {})
            scored.append((score, rec))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [(rec, float(score)) for score, rec in scored[:top_k]]

    def delete(self, ids: Iterable[str]) -> None:
        cur = self._conn.cursor()
        for _id in ids:
            cur.execute("DELETE FROM vectors WHERE id = ?", (_id,))
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


def embed_and_upsert(store: VectorStoreBase, chunks: Iterable[Dict[str, Any]], embed_fn) -> None:
    """Helper: compute embeddings for `chunks` using `embed_fn` and upsert.

    - `chunks` is an iterable of dicts. Each should have an `id` key and any
      metadata fields. The resulting VectorRecord will store the embedding under
      `embedding` and the original chunk as metadata under `metadata`.
    - `embed_fn(text) -> List[float]` is a sync function that returns a vector.
    """
    records: List[VectorRecord] = []
    for c in chunks:
        cid = c.get("id") or c.get("chunk_id")
        if not cid:
            raise ValueError("chunk missing 'id' or 'chunk_id'")
        text = c.get("text") or c.get("raw_text") or c.get("chunk_text") or ""
        vec = embed_fn(text)
        records.append(VectorRecord(str(cid), list(vec), {**c}))
    store.upsert(records)
