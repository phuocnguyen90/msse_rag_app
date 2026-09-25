"""Smoke tests for quick CI/CD build validation and runtime readiness."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_core_imports():
    """Verify all primary packages and project modules import cleanly."""
    import chromadb
    import flask
    import gunicorn
    import openai
    import src.embeddings
    import src.ingest
    import src.rag
    import app.app

    assert chromadb is not None
    assert flask is not None
    assert gunicorn is not None
    assert openai is not None
    assert src.rag is not None
    assert app.app is not None


def test_app_factory():
    """Verify Flask application initializes with healthy health-check endpoint."""
    from app.app import create_app

    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "healthy"
