# Deployment and CI/CD Requirements

To ensure modern software delivery standards and satisfy the maximum rubric score, you will establish an automated Continuous Integration (CI) pipeline with GitHub Actions and deploy your RAG application to **Render** using an Infrastructure-as-Code blueprint modeled after [malware-detect/render.yaml](file:///home/phuoc/git/msse/malware-detect/render.yaml).

---

## 1. Continuous Integration & Delivery (CI/CD Pipeline)

- **Platform**: Implement automated workflows using **GitHub Actions** (`.github/workflows/ci-cd.yml`).
- **Trigger Conditions**:
  - The pipeline must trigger automatically on every `push` and `pull_request` targeting the `main` branch.
- **Required Workflow Jobs**:
  1. **Lint & Automated Tests (`test`)**:
     - Check out code using `actions/checkout@v4`.
     - Set up Python (e.g., Python 3.12) with pip caching via `actions/setup-python@v5`.
     - Install dependencies: `python -m pip install --upgrade pip` and `pip install -r requirements.txt`.
     - Run linting (e.g., `flake8` or `ruff`).
     - Execute the test suite using `pytest -v tests/` (verifying ingestion, retrieval, guardrail logic, and `/health` response).
  2. **Gated Automated Deployment (`deploy`)**:
     - Depends on the `test` job passing (`needs: test`).
     - Executes exclusively on push events to `main` (`if: github.ref == 'refs/heads/main' && github.event_name == 'push'`).
     - Triggers Render deployment via deploy webhook:
       ```bash
       curl -X POST "$RENDER_DEPLOY_HOOK_URL"
       ```
       where `RENDER_DEPLOY_HOOK_URL` is configured as a GitHub Repository Secret.

---

## 2. Cloud Hosting on Render (`render.yaml`)

- **Hosting Platform**: Render Free Tier Web Service (Python environment).
- **Infrastructure as Code**: Provide a root `render.yaml` configuration:
  ```yaml
  services:
    - type: web
      name: policy-rag-assistant
      env: python
      region: oregon
      plan: free
      buildCommand: pip install -r requirements.txt && python src/ingest.py
      startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 "app.main:create_app()"
      healthCheckPath: /health
      envVars:
        - key: PYTHON_VERSION
          value: 3.12.3
        - key: FLASK_ENV
          value: production
        - key: OPENROUTER_EMBEDDING_MODEL
          value: nvidia/llama-nemotron-embed-vl-1b-v2:free
        - key: OPENROUTER_CHAT_MODEL
          value: meta-llama/llama-3.1-8b-instruct:free
        - key: OPENROUTER_API_KEY
          sync: false  # Injected securely via Render Dashboard
  ```
- **Build & Initialization**:
  - The build step installs dependencies and builds/persists the local vector index so that the service starts immediately without re-indexing latency on boot.
- **Port Binding**: Ensure the server binds to `0.0.0.0:$PORT` provided dynamically by Render.
- **Health Check Endpoint**: Set `healthCheckPath: /health` so Render can monitor container uptime and route traffic only when the service is healthy.

---

## 3. Deployment Artifacts & Documentation

- **`deployed.md`**: Create a file in the project root documenting:
  - Public live URL (e.g., `https://policy-rag-assistant.onrender.com/`).
  - Active endpoints (`/`, `/chat`, `/health`).
  - Sample `curl` verification command and expected output.
  - Notice confirming collaborator invitation for **`quantic-grader`**.
- **Local Fallback**:
  - In addition to cloud deployment, the application must run locally via simple setup commands (`python -m venv .venv && pip install -r requirements.txt && python run.py`).
