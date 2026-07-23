"""
Embedding service for RAG pipeline.
Supports OpenAI embeddings (live) and deterministic local embeddings (mock mode).
"""

import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path


class EmbeddingService:
    """Service for generating and comparing embeddings."""

    def __init__(self, provider: str = "mock"):
        self.provider = provider
        self.dimension = 384  # MiniLM-L6-v2 dimension
        self._openai_client = None
        self._local_model = None
        self._initialize()

    def _initialize(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY", "")
                if api_key:
                    self._openai_client = OpenAI(api_key=api_key)
                else:
                    self.provider = "mock"
            except ImportError:
                self.provider = "mock"
        elif self.provider in ["groq", "openrouter", "ollama"]:
            # These use deterministic local embeddings fallback
            self.provider = "local"
        else:
            self.provider = "mock"

    def _deterministic_hash_embedding(self, text: str) -> List[float]:
        """Generate deterministic embeddings using hash-based approach for mock mode."""
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Create a pseudo-random but deterministic vector of dimension 384
        np.random.seed(int.from_bytes(hash_bytes[:8], 'big'))
        vec = np.random.randn(self.dimension)
        # Normalize
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        if self.provider == "openai" and self._openai_client:
            try:
                response = self._openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception:
                return self._deterministic_hash_embedding(text)
        else:
            return self._deterministic_hash_embedding(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self.provider == "openai" and self._openai_client:
            try:
                response = self._openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts
                )
                return [data.embedding for data in response.data]
            except Exception:
                return [self._deterministic_hash_embedding(t) for t in texts]
        else:
            return [self._deterministic_hash_embedding(t) for t in texts]

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

    def search(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for most similar documents to a query."""
        if not documents:
            return []

        query_embedding = self.generate_embedding(query)

        # If FAISS is available and we have enough documents, use it
        if len(documents) > 10 and self.provider != "mock":
            try:
                import faiss
                doc_embeddings = np.array([
                    self.generate_embedding(d.get("content", d.get("description", "")))
                    for d in documents
                ]).astype('float32')
                
                index = faiss.IndexFlatIP(self.dimension)
                index.add(doc_embeddings)
                
                query_vec = np.array([query_embedding]).astype('float32')
                scores, indices = index.search(query_vec, min(top_k, len(documents)))
                
                results = []
                for i, idx in enumerate(indices[0]):
                    results.append({
                        **documents[idx],
                        "similarity_score": float(scores[0][i])
                    })
                return results
            except (ImportError, Exception):
                pass

        # Fallback: linear scan with cosine similarity
        scored = []
        for doc in documents:
            content = doc.get("content", doc.get("description", ""))
            doc_embedding = self.generate_embedding(content)
            score = self.cosine_similarity(query_embedding, doc_embedding)
            scored.append((score, doc))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{**doc, "similarity_score": score} for score, doc in scored[:top_k]]

