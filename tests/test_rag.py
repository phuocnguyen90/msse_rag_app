"""Tests for RAG pipeline retrieval and guardrail enforcement."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag import PolicyRAGPipeline, STANDARD_REFUSAL  # noqa: E402


def test_pipeline_initialization():
    pipeline = PolicyRAGPipeline()
    assert pipeline.collection is not None
    assert pipeline.collection.count() > 0


def test_retrieval_relevance():
    pipeline = PolicyRAGPipeline()
    chunks = pipeline.retrieve("What is the maximum reimbursement for meals?", k=3)
    assert len(chunks) > 0
    top_doc = chunks[0]
    assert "POL-EXP-2025" in top_doc["doc_id"] or "EXP" in top_doc["doc_id"]


def test_offline_guardrail_refusal():
    pipeline = PolicyRAGPipeline(api_key=None)
    # Test adversarial out-of-scope query
    result = pipeline.query("What was the score of yesterday's basketball game?")
    assert STANDARD_REFUSAL.lower() in result["answer"].lower() or "i can only answer" in result["answer"].lower()
    assert len(result["citations"]) == 0


def test_empty_query_handling():
    pipeline = PolicyRAGPipeline(api_key=None)
    result = pipeline.query("   ")
    assert "valid policy question" in result["answer"]
    assert result["latency_ms"] == 0.0
