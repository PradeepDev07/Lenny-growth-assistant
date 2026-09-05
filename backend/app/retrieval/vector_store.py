import json
import os
import re
import math
from typing import Any, Dict, List, Optional
from collections import Counter

def _find_cache_file() -> str:
    """Resolve vector_cache.json path across local, monorepo, and container environments."""
    if "VECTOR_CACHE_FILE" in os.environ and os.path.exists(os.environ["VECTOR_CACHE_FILE"]):
        return os.environ["VECTOR_CACHE_FILE"]

    candidates = [
        # Monorepo root from backend/app/retrieval/
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "vector_cache.json")),
        # Backend folder
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vector_cache.json")),
        # Docker container standard paths
        "/app/vector_cache.json",
        "/app/backend/vector_cache.json",
        "vector_cache.json",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


CHUNKS_CACHE_FILE = _find_cache_file()


def tokenize(text: str) -> List[str]:
    """Tokenize text into lower-case alphanumeric tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Retriever:
    """Robust, deterministic BM25 search engine with metadata field boosting."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs: int = 0
        self.doc_term_freqs: List[Counter] = []

    def fit(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.total_docs = len(documents)
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.doc_freqs = {}

        if not documents:
            self.avg_doc_len = 0.0
            return

        total_len = 0
        for doc in documents:
            # Combine content with title and guest for indexing
            text = f"{doc.get('source_title', '')} {doc.get('guest', '')} {doc.get('content', '')}"
            tokens = tokenize(text)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_len += length

            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            for token in tf.keys():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_len / max(1, self.total_docs)

    def idf(self, term: str) -> float:
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0.0
        return math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> List[float]:
        q_tokens = tokenize(query)
        if not q_tokens or self.total_docs == 0:
            return [0.0] * self.total_docs

        scores = [0.0] * self.total_docs
        for token in q_tokens:
            token_idf = self.idf(token)
            if token_idf <= 0:
                continue

            for idx in range(self.total_docs):
                tf = self.doc_term_freqs[idx].get(token, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[idx]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                term_score = token_idf * ((tf * (self.k1 + 1.0)) / denom)

                # Boost if token is directly in guest name or title
                doc = self.documents[idx]
                if token in tokenize(doc.get("guest", "")):
                    term_score *= 2.5
                elif token in tokenize(doc.get("source_title", "")):
                    term_score *= 1.8

                scores[idx] += term_score

        return scores


class VectorStore:
    """Persistent vector store with high-accuracy retrieval."""

    def __init__(self, cache_file: str = CHUNKS_CACHE_FILE):
        self.cache_file = os.path.abspath(cache_file)
        self.retriever = BM25Retriever()
        self.documents: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        """Load indexed chunks from disk cache if present."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.retriever.fit(self.documents)
            except Exception:
                self.documents = []

    def save(self):
        """Save indexed documents to disk."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        data = {
            "documents": self.documents,
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add new chunks and re-index."""
        existing_ids = {doc["id"] for doc in self.documents}
        new_chunks = [c for c in chunks if c["id"] not in existing_ids]

        if not new_chunks:
            self.retriever.fit(self.documents)
            return

        self.documents.extend(new_chunks)
        self.retriever.fit(self.documents)
        self.save()

    def clear(self):
        """Clear all indexed documents."""
        self.documents = []
        self.retriever.fit([])
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def search(self, query: str, top_k: int = 4, min_score: float = 0.05) -> List[Dict[str, Any]]:
        """Search top-k most relevant chunks using BM25 with metadata boosting."""
        if not self.documents or not query.strip():
            return []

        scores = self.retriever.score(query)
        scored_pairs = list(enumerate(scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs[:top_k]:
            if score >= min_score:
                doc_copy = dict(self.documents[idx])
                doc_copy["score"] = round(float(score), 4)
                results.append(doc_copy)

        return results


# Global vector store instance
vector_store = VectorStore()
