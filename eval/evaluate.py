"""Automated Evaluation Suite with Stress Testing & Failure Mode Analysis.

Evaluates the RAG pipeline across 25 benchmark questions spanning:
1. Standard Factual (Happy Path)
2. Borderline Tension / Cross-Policy Conflicts
3. Borderline Boundary Conditions
4. Disguised Unspecified Corporate Scenarios
5. Adversarial Out-of-Scope Refusal
6. Retrieval Ablation Studies (varying k=2, 4, 6)
"""

import argparse
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
        # Out-of-corpus queries must trigger standard refusal
        return refusal_lower in answer or "i can only answer" in answer

    # In-corpus questions must NOT trigger refusal
    if refusal_lower in answer:
        return False

    # Check key concepts from gold answer are present
    gold_words = set(w.lower() for w in item["gold_answer"].split() if len(w) > 3 and w.isalnum())
    matched_words = [w for w in gold_words if w in answer]
    # At least 30% key concept overlap
    return len(matched_words) / max(len(gold_words), 1) >= 0.30


def evaluate_citation_accuracy(item: Dict[str, Any], result: Dict[str, Any]) -> bool:
    """Evaluate whether citations accurately point to the expected document ID."""
    is_in_corpus = item["is_in_corpus"]
    expected_doc_id = item["expected_doc_id"]

    if not is_in_corpus:
        # Out-of-corpus queries should have zero misleading citations or standard refusal
        return len(result["citations"]) == 0 or STANDARD_REFUSAL.lower() in result["answer"].lower()

    answer_text = result["answer"]
    citations = result.get("citations", [])

    # Check if expected doc_id is cited in text or listed in citations
    has_doc_in_text = expected_doc_id in answer_text
    has_doc_in_citations = any(c.get("doc_id") == expected_doc_id for c in citations)

    return has_doc_in_text or has_doc_in_citations


def run_benchmark(sample_size: int = 25, delay_seconds: float = 1.5) -> Dict[str, Any]:
    """Run full benchmark evaluation with rate throttling and category failure analysis."""
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark_items = json.load(f)[:sample_size]

    pipeline = PolicyRAGPipeline()
    results = []
    latencies = []
    grounded_count = 0
    accurate_citation_count = 0

    category_stats: Dict[str, Dict[str, Any]] = {}

    logger.info(f"Starting evaluation of {len(benchmark_items)} benchmark questions (delay={delay_seconds}s)...")

    for idx, item in enumerate(benchmark_items, 1):
        q = item["question"]
        cat = item["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "grounded": 0, "accurate_citation": 0, "failures": []}

        category_stats[cat]["total"] += 1

        res = pipeline.query(q)
        latencies.append(res["latency_ms"])

        is_grounded = evaluate_groundedness(item, res)
        has_accurate_citation = evaluate_citation_accuracy(item, res)

        if is_grounded:
            grounded_count += 1
            category_stats[cat]["grounded"] += 1
        if has_accurate_citation:
            accurate_citation_count += 1
            category_stats[cat]["accurate_citation"] += 1

        # Track failure details
        failure_reasons = []
        if not is_grounded:
            failure_reasons.append("groundedness_failure")
        if not has_accurate_citation:
            failure_reasons.append("citation_failure")

        if failure_reasons:
            category_stats[cat]["failures"].append({
                "id": item["id"],
                "question": q,
                "failure_reasons": failure_reasons,
                "risk_note": item.get("failure_risk_note", ""),
                "actual_answer": res["answer"],
                "gold_answer": item["gold_answer"],
            })

        results.append({
            "id": item["id"],
            "category": cat,
            "question": q,
            "answer": res["answer"],
            "model": res.get("model", ""),
            "latency_ms": res["latency_ms"],
            "is_grounded": is_grounded,
            "has_accurate_citation": has_accurate_citation,
            "failure_risk_note": item.get("failure_risk_note", ""),
            "citations": res["citations"],
        })

        logger.info(
            f"[{idx}/{len(benchmark_items)}] {item['id']} ({cat}) | "
            f"Grounded: {is_grounded} | Citation: {has_accurate_citation} | "
            f"Model: {res.get('model', 'offline')} | Latency: {res['latency_ms']:.1f}ms"
        )

        # Politeness delay to prevent free tier rate limits
        if delay_seconds > 0 and idx < len(benchmark_items):
            time.sleep(delay_seconds)

    total = len(benchmark_items)
    groundedness_pct = round((grounded_count / total) * 100, 2)
    citation_accuracy_pct = round((accurate_citation_count / total) * 100, 2)
    p50_latency = round(float(np.percentile(latencies, 50)), 2)
    p95_latency = round(float(np.percentile(latencies, 95)), 2)
    mean_latency = round(float(np.mean(latencies)), 2)

    # Format category breakdown percentages
    category_breakdown = {}
    for cat, stats in category_stats.items():
        cat_total = stats["total"]
        category_breakdown[cat] = {
            "total": cat_total,
            "groundedness_pct": round((stats["grounded"] / cat_total) * 100, 1),
            "citation_accuracy_pct": round((stats["accurate_citation"] / cat_total) * 100, 1),
            "failure_count": len(stats["failures"]),
            "failures": stats["failures"],
        }

    # Ablation study: Varying k over 5 queries with rate delay
    logger.info("Running retrieval depth ablation study (k=2, k=4, k=6)...")
    ablation_queries = [
        "What is the maximum daily reimbursement for business meals?",
        "Can I use my home office stipend to purchase a network-attached storage drive?",
        "A vendor sent me a gift basket valued at exactly $50.00. Do I surrender it?",
        "Can an employee take accrued PTO hours concurrently during paid parental leave?",
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
        "category_breakdown": category_breakdown,
        "ablation_retrieval_depth": ablation_results,
        "detailed_results": results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("=" * 60)
    logger.info("EVALUATION & FAILURE MODE ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Questions Evaluated: {total}")
    logger.info(f"Overall Groundedness:     {groundedness_pct}%")
    logger.info(f"Overall Citation Acc:     {citation_accuracy_pct}%")
    logger.info(f"Median Latency (p50):     {p50_latency} ms")
    logger.info(f"Tail Latency (p95):       {p95_latency} ms")
    logger.info(f"Mean Latency:             {mean_latency} ms")
    logger.info("Category Performance Breakdown:")
    for cat, data in category_breakdown.items():
        logger.info(
            f"  - {cat:22s} ({data['total']} items): "
            f"Grounded={data['groundedness_pct']}%, Citation={data['citation_accuracy_pct']}%, "
            f"Failures={data['failure_count']}"
        )
    logger.info(f"Retrieval Depth Ablation: {ablation_results}")
    logger.info(f"Results written to:       {RESULTS_PATH}")
    logger.info("=" * 60)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline on policy benchmark.")
    parser.add_argument("--sample", type=int, default=25, help="Number of questions to evaluate (default: 25)")
    parser.add_argument("--delay", type=float, default=1.5, help="Politeness sleep in seconds between queries (default: 1.5)")
    args = parser.parse_args()

    run_benchmark(sample_size=args.sample, delay_seconds=args.delay)
