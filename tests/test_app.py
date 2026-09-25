"""Tests for Flask web application routes and REST endpoints."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Apex Policy AI" in response.data or b"Company Policy" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "apex-policy-rag-assistant"
    assert data["indexed_chunks"] > 0
    assert data["vector_store"] == "ready"


def test_chat_endpoint_valid_question(client):
    response = client.post(
        "/chat",
        json={"question": "What is the daily meal per diem cap?"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "citations" in data
    assert "latency_ms" in data


def test_chat_endpoint_empty_question(client):
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"


def test_chat_endpoint_non_json(client):
    response = client.post("/chat", data="not a json payload")
    assert response.status_code == 400
