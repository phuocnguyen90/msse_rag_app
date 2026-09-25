# Project Overview

For this project, you will design, build, evaluate, and (optionally) deploy a **Retrieval-Augmented Generation (RAG)** Large Language Model (LLM)-based application. The application will answer user questions about a curated corpus of company policies and procedures. You will also configure a basic CI/CD pipeline (e.g., GitHub Actions) that validates builds on pushes/pull requests and optionally automates deployment to a free-tier cloud host (e.g., Render, Railway). Finally, you will demonstrate the complete system through a recorded screen-share presentation covering your architecture, application features, evaluation metrics, and CI/CD runs.

You can complete this project either individually or as a group of no more than three people.

While you may hand-code any portion of the project, you are **highly encouraged** to utilize leading AI code generation models, AI IDEs, and asynchronous coding agents to accelerate development. You must document and describe your use of AI tooling in an accompanying document. You will be evaluated on the architectural quality, functional correctness, evaluation rigor, and documentation of the final application.

---

## Learning Outcomes

When completed successfully, this project will enable you to:
- **Demonstrate AI Engineering Excellence**: Build and integrate modern generative AI components into production-grade software workflows.
- **Select Appropriate AI Architectures**: Make principled decisions regarding document chunking, embeddings, vector indexing, retrieval strategies, and prompt engineering.
- **Implement an End-to-End RAG Application**: Ingest raw multi-format policy documents, index vector embeddings, execute semantic retrieval, enforce guardrails, and serve user queries via a web UI and REST API.
- **Systematically Evaluate LLM Performance**: Define and measure empirical information-quality metrics (groundedness, citation accuracy) and system performance metrics (p50/p95 latency).
- **Leverage AI Tooling Effectively**: Accelerate development responsibly using AI assistants, pair-programming agents, and automated code review workflows.

---

## Technical and Operational Principles

- **Zero-Cost / Free-Tier Priority**: Utilize free or zero-cost tiers wherever possible (e.g., Groq, OpenRouter free tiers, HuggingFace, local embeddings, local Chroma vector store, free Render/Railway hosting).
- **Reproducibility**: Ensure the environment, data ingestion, vector indexing, and evaluation benchmark can be deterministically reproduced using clear setup commands, explicit dependency pins, and fixed random seeds.
- **Traceability and Citations**: Every generated response must cite the source policy documents with verifiable snippet references and strictly adhere to company policy bounds.
