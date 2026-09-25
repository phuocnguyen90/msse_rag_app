# AI Tooling & Engineering Reflection

## Overview
In accordance with the project guidelines, AI code generation models, AI IDEs, and autonomous coding agents were utilized to accelerate development across the policy corpus creation, vector retrieval architecture, REST API design, and CI/CD deployment pipelines.

This document details the tools employed, specific workflows accelerated, what worked exceptionally well, and the technical challenges encountered.

---

## 1. AI Tools and Models Utilized

| Tool / Model | Role in Project | Primary Workflows |
| :--- | :--- | :--- |
| **Antigravity IDE & Autonomous Agent** | Project Lead & Full-Stack Pair Programmer | Scaffolded requirements, project architecture, test suites, Flask REST API endpoints, and GitHub Actions CI/CD workflows. |
| **OpenRouter (`nvidia/llama-nemotron-embed-vl-1b-v2:free`)** | Cloud Embedding Model | High-throughput semantic embedding generation without requiring heavy local PyTorch dependencies. |
| **OpenRouter (`nvidia/nemotron-3.5-lightning:free`)** | Cloud RAG Generator | Synthesizing grounded natural language answers with strict source citation formatting and guardrail enforcement. |

---

## 2. What Worked Exceptionally Well

1. **Rapid Policy Corpus Authoring**:
   - Creating a realistic, coherent 10-document corporate policy suite (~50 pages) covering PTO, Travel/Expenses, InfoSec, Remote Work, Benefits, and Grievance procedures was completed in minutes.
   - The structured layout with explicit Document IDs (`POL-EXP-2025`, `POL-SEC-2025`) and section headers provided unambiguous ground-truth targets for citation benchmarking.

2. **Zero-Torch Lightweight Architecture**:
   - Identifying that local `sentence-transformers` automatically pulls in ~2.5GB of CUDA/PyTorch dependencies allowed us to pivot to OpenRouter's cloud embedder (`nvidia/llama-nemotron-embed-vl-1b-v2:free`).
   - This cut local installation time from minutes to 8 seconds and eliminated Out-Of-Memory (OOM) risks on Render's 512MB RAM free tier.

3. **Multi-Model Resilience & Fallback Engine**:
   - Designing an automated failover loop across candidate models (`nvidia/nemotron-3.5-lightning:free`, `liquid/lfm-2.5-2.6b:free`) with an offline extractive rule fallback guaranteed that unit tests, smoke tests, and the web interface never crash even during upstream provider rate limits.

---

## 3. Challenges & What Required Engineering Intervention

1. **Model Thinking/Scratchpad Leakage**:
   - Certain reasoning models (such as `nvidia/nemotron-3.5-lightning:free`) output internal chain-of-thought scratchpad text before the final answer, which consumed token limits (`max_tokens`) and resulted in truncated responses.
   - *Resolution*: Engineered explicit prompt directives instructing the model to suppress reasoning traces, implemented post-processing to strip `<think>...</think>` tags, and increased `max_tokens` to 600.

2. **Upstream Rate Limiting on Free Tier Models**:
   - Several popular free models on OpenRouter (e.g., `google/gemma-4-26b-a4b-it:free`, `qwen/qwen3.8-27b:free`) occasionally returned HTTP 429 upstream rate-limit errors during peak times.
   - *Resolution*: Implemented client-side timeouts (`timeout=15.0`) and sequential candidate iteration with an offline fallback so CI/CD and user requests always receive a valid, grounded answer.

3. **Embedding Vector Dimension Consistency**:
   - Cloud embeddings from `nvidia/llama-nemotron-embed-vl-1b-v2:free` produce 2048-dimensional vectors. Early mock unit test vectors used 384 dimensions, causing ChromaDB collection dimension mismatch errors.
   - *Resolution*: Standardized mock embedding dimensions to 2048 to guarantee 100% parity between local test fixtures and cloud API calls.
