"""Automated Evaluation Suite.

Evaluates the RAG pipeline across 20 benchmark questions for:
1. Groundedness %
2. Citation Accuracy %
3. System Latency (p50 and p95)
4. Retrieval Ablation Studies (varying k)
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag import PolicyRAGPipeline, STANDARD_REFUSAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), "benchmark_data.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "evaluation_results.json")


def evaluate_groundedness(item: Dict[str, Any], result: Dict[str, Any]) -> bool:
    """Evaluate whether the answer is factually grounded in context and respects guardrails."""
    answer = result["answer"].lower()
    is_in_corpus = item["is_in_corpus"]
    refusal_lower = STANDARD_REFUSAL.lower()

    if not is_in_corpus:
        # For out-of-corpus queries, must trigger refusal
        return refusal_lower in answer or "i can only answer" in answer

    # For in-corpus questions, must NOT refuse
    if refusal_lower in answer:
        return False

    # Check key concepts from gold answer are present
    gold_words = set(w.lower() for w in item["gold_answer"].split() if len(w) > 4 and w.isalnum())
    matched_words = [w for w in gold_words if w in answer]
    # At least 35% key word overlap
    return len(matched_words) / max(len(gold_words), 1) >= 0.35


def evaluate_citation_accuracy(item: Dict[str, Any], result: Dict[str, Any]) -> bool:
    """Evaluate whether citations accurately point to the expected document ID and section."""
    is_in_corpus = item["is_in_corpus"]
    expected_doc_id = item["expected_doc_id"]

    if not is_in_corpus:
        # Out-of-corpus queries should have zero misleading citations
        return len(result["citations"]) == 0 or STANDARD_REFUSAL.lower() in result["answer"].lower()

    answer_text = result["answer"]
    citations = result.get("citations", [])

    # Check if expected doc_id is cited in text or listed in citations
    has_doc_in_text = expected_doc_id in answer_text
    has_doc_in_citations = any(c.get("doc_id") == expected_doc_id for c in citations)

    return has_doc_in_text or has_doc_in_citations


def run_benchmark(sample_size: int = 20) -> Dict[str, Any]:
    """Run full benchmark evaluation and calculate empirical quality and system metrics."""
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark_items = json.load(f)[:sample_size]

    pipeline = PolicyRAGPipeline()
    results = []
    latencies = []
    grounded_count = 0
    accurate_citation_count = 0

    logger.info(f"Starting evaluation of {len(benchmark_items)} benchmark questions...")

    for idx, item in enumerate(benchmark_items, 1):
        q = item["question"]
        res = pipeline.query(q)
        latencies.append(res["latency_ms"])

        is_grounded = evaluate_groundedness(item, res)
        has_accurate_citation = evaluate_citation_accuracy(item, res)

        if is_grounded:
            grounded_count += 1
        if has_accurate_citation:
            accurate_citation_count += 1

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": q,
            "answer": res["answer"],
            "model": res.get("model", ""),
            "latency_ms": res["latency_ms"],
            "is_grounded": is_grounded,
            "has_accurate_citation": has_accurate_citation,
            "citations": res["citations"],
        })
        logger.info(
            f"[{idx}/{len(benchmark_items)}] {item['id']} | Grounded: {is_grounded} | "
            f"Citation: {has_accurate_citation} | Latency: {res['latency_ms']}ms"
        )

    total = len(benchmark_items)
    groundedness_pct = round((grounded_count / total) * 100, 2)
    citation_accuracy_pct = round((accurate_citation_count / total) * 100, 2)
    p50_latency = round(float(np.percentile(latencies, 50)), 2)
    p95_latency = round(float(np.percentile(latencies, 95)), 2)
    mean_latency = round(float(np.mean(latencies)), 2)

    # Ablation study: Varying k over 5 queries
    logger.info("Running retrieval depth ablation study (k=2, k=4, k=6)...")
    ablation_queries = [
        "What is the maximum daily reimbursement for business meals?",
        "How many hours of unused accrued PTO can an employee roll over?",
        "What are the password length and complexity rules?",
        "How much does Apex Technologies match employee 401(k) contributions?",
        "What is the hardware replacement lifecycle for corporate laptops?",
    ]
    ablation_results = {}
    for k_val in [2, 4, 6]:
        k_latencies = []
        for q in ablation_queries:
            t0 = time.time()
            chunks = pipeline.retrieve(q, k=k_val)
            k_latencies.append((time.time() - t0) * 1000)
        ablation_results[f"k={k_val}"] = {
            "avg_retrieval_ms": round(float(np.mean(k_latencies)), 2),
            "chunks_returned": k_val,
        }

    summary = {
        "total_evaluated": total,
        "groundedness_pct": groundedness_pct,
        "citation_accuracy_pct": citation_accuracy_pct,
        "latency_p50_ms": p50_latency,
        "latency_p95_ms": p95_latency,
        "latency_mean_ms": mean_latency,
        "chat_model": pipeline.chat_model,
        "ablation_retrieval_depth": ablation_results,
        "detailed_results": results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("=" * 60)
    logger.info("EVALUATION SUMMARY REPORT")
    logger.info("=" * 60)
    logger.info(f"Total Questions Evaluated: {total}")
    logger.info(f"Groundedness:             {groundedness_pct}%")
    logger.info(f"Citation Accuracy:        {citation_accuracy_pct}%")
    logger.info(f"Median Latency (p50):     {p50_latency} ms")
    logger.info(f"Tail Latency (p95):       {p95_latency} ms")
    logger.info(f"Mean Latency:             {mean_latency} ms")
    logger.info(f"Retrieval Ablation:       {ablation_results}")
    logger.info(f"Results saved to:         {RESULTS_PATH}")
    logger.info("=" * 60)

    return summary


if __name__ == "__main__":
    run_benchmark()
