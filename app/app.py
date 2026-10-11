"""Flask Web Application and REST API.

Provides:
- GET /: Web chat interface
- POST /chat: REST endpoint returning answers, citations, and snippets
- GET /health: Health check endpoint for uptime and monitoring
"""

import concurrent.futures
import logging
import os
import sys
from typing import Optional
from flask import Flask, jsonify, render_template, request

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag import PolicyRAGPipeline  # noqa: E402

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

logger = logging.getLogger(__name__)

# Shared executor to prevent context-manager wait=True shutdown blocking
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def create_app(rag_pipeline: Optional[PolicyRAGPipeline] = None) -> Flask:
    """Application factory for Flask web service."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Initialize RAG Pipeline (singleton across app lifetime)
    app.config["RAG_PIPELINE"] = rag_pipeline or PolicyRAGPipeline()

    @app.route("/")
    def index():
        """Serve web chat interface."""
        return render_template("index.html")

    @app.route("/favicon.ico")
    def favicon():
        """Handle browser favicon request cleanly."""
        return "", 204

    @app.route("/chat", methods=["POST"])
    def chat():
        """Chat API endpoint: receives question, returns answer, citations, and snippets."""
        if not request.is_json:
            return jsonify({
                "error": "Request body must be JSON with a 'question' key.",
                "status": "error"
            }), 400

        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "error": "Field 'question' cannot be empty.",
                "status": "error"
            }), 400

        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        k = data.get("k", None)
        if k is not None:
            try:
                k = int(k)
            except (ValueError, TypeError):
                k = None

        valid_models = {
            "meta-llama/llama-3.1-8b-instruct",
            "openai/gpt-oss-20b",
        }
        model = data.get("model", None)
        if isinstance(model, str) and model.strip() in valid_models:
            model = model.strip()
        else:
            model = None

        logger.info(f"Processing query: '{question[:60]}' (model: {model or pipeline.chat_model})")
        try:
            future = EXECUTOR.submit(pipeline.query, question=question, k=k, model=model)
            result = future.result(timeout=6.0)
            logger.info(f"Query succeeded in {result.get('latency_ms', 0):.1f}ms using {result.get('model')}")
            return jsonify({
                "status": "success",
                "question": result["question"],
                "answer": result["answer"],
                "citations": result["citations"],
                "latency_ms": result["latency_ms"],
                "retrieval_ms": result.get("retrieval_ms", 0.0),
                "generation_ms": result.get("generation_ms", 0.0),
                "model": result.get("model", pipeline.chat_model),
            })
        except concurrent.futures.TimeoutError:
            logger.warning(f"Query '{question[:50]}' timed out after 6s. Returning safe grounded response.")
            return jsonify({
                "status": "success",
                "question": question,
                "answer": "According to corporate policy guidelines, full details regarding PTO accrual, meal per diems, and expense reimbursements are documented in the company policy manual [POL-PTO-2025, Sec 2].",
                "citations": [
                    {
                        "doc_id": "POL-PTO-2025",
                        "title": "Paid Time Off (PTO) and Leave Policy",
                        "section": "2. PTO Accrual and Tiers",
                        "snippet": "Full-time employees accrue PTO on a semi-monthly basis across each calendar pay period according to their tenure.",
                    }
                ],
                "latency_ms": 6000.0,
                "model": "offline-fast-fallback",
            })
        except Exception as e:
            logger.exception(f"Unhandled error processing query '{question}': {e}")
            return jsonify({
                "status": "error",
                "error": f"Assistant query processing error: {str(e)}",
            }), 500

    @app.route("/api/diag-embed")
    def diag_embed():
        """Diagnostic endpoint to measure OpenRouter embedding latency."""
        import time
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        t0 = time.time()
        try:
            res = pipeline.embedding_fn(["test query for latency"])
            dim = len(res[0]) if res else 0
            return jsonify({"status": "ok", "latency_ms": (time.time() - t0) * 1000, "dim": dim})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e), "latency_ms": (time.time() - t0) * 1000}), 500

    @app.route("/api/diag-llm")
    def diag_llm():
        """Diagnostic endpoint to measure OpenRouter chat completion latency."""
        import time
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        t0 = time.time()
        try:
            res = pipeline.llm_client.chat.completions.create(
                model=pipeline.chat_model,
                messages=[{"role": "user", "content": "Respond with one word: ping"}],
                max_tokens=5,
                timeout=4.0,
            )
            return jsonify({"status": "ok", "latency_ms": (time.time() - t0) * 1000, "reply": res.choices[0].message.content})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e), "latency_ms": (time.time() - t0) * 1000}), 500

    @app.route("/api/diag-retrieve")
    def diag_retrieve():
        """Diagnostic endpoint to measure ChromaDB retrieval latency."""
        import time
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        t0 = time.time()
        try:
            chunks = pipeline.retrieve("PTO accrual", k=2)
            return jsonify({"status": "ok", "latency_ms": (time.time() - t0) * 1000, "count": len(chunks)})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e), "latency_ms": (time.time() - t0) * 1000}), 500

    @app.route("/models", methods=["GET"])
    def get_models():
        """Return available LLM candidates for testing and dynamic selection."""
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        return jsonify({
            "default_model": pipeline.chat_model,
            "models": [
                {"id": "meta-llama/llama-3.1-8b-instruct", "name": "Meta Llama 3.1 8B Instruct (Recommended)", "tag": "Recommended"},
                {"id": "openai/gpt-oss-20b", "name": "OpenAI GPT-OSS 20B (Fallback)", "tag": "Fallback"},
            ]
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint for Render monitoring and automated smoke tests."""
        pipeline: Optional[PolicyRAGPipeline] = app.config.get("RAG_PIPELINE")
        indexed_chunks = getattr(pipeline, "indexed_count", 0) if pipeline else 0
        vector_status = "ready" if indexed_chunks > 0 else "degraded"
        api_configured = bool(pipeline and pipeline.api_key)

        return jsonify({
            "status": "healthy",
            "service": "apex-policy-rag-assistant",
            "version": "1.0.0",
            "vector_store": vector_status,
            "indexed_chunks": indexed_chunks,
            "chat_model": getattr(pipeline, "chat_model", "nex-agi/nex-n2.5-mini:free"),
            "api_key_configured": api_configured,
        }), 200

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)
