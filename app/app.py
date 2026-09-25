"""Flask Web Application and REST API.

Provides:
- GET /: Web chat interface
- POST /chat: REST endpoint returning answers, citations, and snippets
- GET /health: Health check endpoint for uptime and monitoring
"""

import logging
import os
import sys
from typing import Optional
from flask import Flask, jsonify, render_template, request

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag import PolicyRAGPipeline  # noqa: E402

logger = logging.getLogger(__name__)


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

        result = pipeline.query(question=question, k=k)
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

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint for Render monitoring and automated smoke tests."""
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        indexed_chunks = 0
        try:
            indexed_chunks = pipeline.collection.count()
            vector_status = "ready"
        except Exception as e:
            logger.error(f"Vector DB health check issue: {e}")
            vector_status = "degraded"

        return jsonify({
            "status": "healthy",
            "service": "apex-policy-rag-assistant",
            "version": "1.0.0",
            "vector_store": vector_status,
            "indexed_chunks": indexed_chunks,
            "chat_model": pipeline.chat_model,
        }), 200

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)
