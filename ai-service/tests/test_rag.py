"""
Tests for RAG data loader and embedding service.
"""

import pytest
import json
import os
from pathlib import Path

from app.rag.data_loader import DataLoader
from app.rag.embeddings import EmbeddingService


class TestDataLoader:
    """Test the DataLoader class."""

    @pytest.fixture
    def loader(self):
        return DataLoader()

    def test_load_services(self, loader):
        services = loader.get_services()
        assert len(services) > 0
        assert any(s["name"] == "payment-gateway" for s in services)

    def test_load_incidents(self, loader):
        incidents = loader.get_incidents()
        assert len(incidents) > 0
        assert any(inc["id"] == "inc-001" for inc in incidents)

    def test_load_change_requests(self, loader):
        crs = loader.get_change_requests()
        assert len(crs) > 0
        assert any(cr["id"] == "cr-001" for cr in crs)

    def test_load_architecture(self, loader):
        arch = loader.get_architecture()
        assert arch["content"] != ""
        assert len(arch["sections"]) > 0

    def test_load_runbooks(self, loader):
        runbooks = loader.get_runbooks()
        assert len(runbooks) > 0
        assert any("payment" in rb["service"] for rb in runbooks)

    def test_load_source_registry(self, loader):
        registry = loader.get_source_registry()
        assert len(registry) > 0
        assert any(src["type"] == "repository" for src in registry)

    def test_get_counts(self, loader):
        counts = loader.get_counts()
        assert counts["services"] > 0
        assert counts["incidents"] > 0
        assert counts["change_requests"] > 0
        assert counts["runbooks"] > 0

    def test_keyword_search(self, loader):
        results = loader._keyword_search(
            loader.get_services(),
            "payment",
            ["name", "description"]
        )
        assert len(results) > 0
        assert any("payment" in r["name"] for r in results)


class TestEmbeddingService:
    """Test the EmbeddingService class."""

    @pytest.fixture
    def embeddings(self):
        return EmbeddingService(provider="mock")

    def test_generate_embedding(self, embeddings):
        vec = embeddings.generate_embedding("test text")
        assert len(vec) == embeddings.dimension
        assert all(isinstance(v, float) for v in vec)

    def test_generate_embeddings(self, embeddings):
        vecs = embeddings.generate_embeddings(["text1", "text2"])
        assert len(vecs) == 2
        assert len(vecs[0]) == embeddings.dimension

    def test_cosine_similarity(self, embeddings):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        similarity = embeddings.cosine_similarity(a, b)
        assert similarity == 0.0

        c = [1.0, 0.0, 0.0]
        similarity = embeddings.cosine_similarity(a, c)
        assert similarity == 1.0

    def test_search_empty(self, embeddings):
        results = embeddings.search("query", [])
        assert results == []

    def test_search(self, embeddings):
        docs = [
            {"id": "1", "content": "payment gateway service"},
            {"id": "2", "content": "user authentication service"},
            {"id": "3", "content": "order processing service"}
        ]
        results = embeddings.search("payment", docs, top_k=2)
        assert len(results) <= 2

