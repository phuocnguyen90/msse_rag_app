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

        model = data.get("model", None)
        if isinstance(model, str):
            model = model.strip() or None
        else:
            model = None

        result = pipeline.query(question=question, k=k, model=model)
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

    @app.route("/models", methods=["GET"])
    def get_models():
        """Return available LLM candidates for testing and dynamic selection."""
        pipeline: PolicyRAGPipeline = app.config["RAG_PIPELINE"]
        return jsonify({
            "default_model": pipeline.chat_model,
            "models": [
                {"id": "nex-agi/nex-n2.5-mini:free", "name": "Nex-N2.5 Mini (Fastest ~0.8s)", "tag": "Recommended"},
                {"id": "google/gemma-4-26b-a4b-it:free", "name": "Google Gemma 4 (26B)", "tag": "Google"},
                {"id": "nvidia/nemotron-3.5-lightning:free", "name": "NVIDIA Nemotron 3.5 Lightning", "tag": "NVIDIA"},
                {"id": "liquid/lfm-2.5-2.6b:free", "name": "Liquid LFM 2.5 (2.6B)", "tag": "Liquid"},
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
