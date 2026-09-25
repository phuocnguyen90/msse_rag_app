"""Tests for document parsing, chunking, and vector indexing."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import chunk_document_by_sections, parse_document_metadata  # noqa: E402
from src.embeddings import _generate_mock_embedding, OpenRouterEmbeddingFunction  # noqa: E402


def test_parse_document_metadata():
    sample_content = """# Corporate Travel and Expense Policy
**Document ID:** POL-EXP-2025
**Effective Date:** March 1, 2025

## 1. Overview
Policy text here.
"""
    meta = parse_document_metadata(sample_content, "03_travel_meals_and_expense_policy.md")
    assert meta["doc_id"] == "POL-EXP-2025"
    assert "Travel" in meta["title"]
    assert meta["source"] == "03_travel_meals_and_expense_policy.md"


def test_chunk_document_by_sections():
    sample_content = """# Header
## 1. Section One
Paragraph under section one with enough details to test chunking logic properly.

## 2. Section Two
Another paragraph under section two.
"""
    meta = {"doc_id": "TEST-01", "title": "Test Title", "source": "test.md"}
    chunks = chunk_document_by_sections(sample_content, meta, max_chunk_chars=300, overlap_chars=50)

    assert len(chunks) >= 2
    sections = [c["metadata"]["section"] for c in chunks]
    assert "1. Section One" in sections
    assert "2. Section Two" in sections


def test_mock_embedding_generation():
    vec = _generate_mock_embedding("Test policy text", dim=2048)
    assert len(vec) == 2048
    # Test deterministic property
    vec2 = _generate_mock_embedding("Test policy text", dim=2048)
    assert vec == vec2


def test_openrouter_embedding_fallback():
    fn = OpenRouterEmbeddingFunction(api_key=None)
    res = fn(["Hello world"])
    assert len(res) == 1
    assert len(res[0]) == 2048
