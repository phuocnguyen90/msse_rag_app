# Project Rubric

Scores of **2 and above** are considered passing. Submissions receiving a **1 or 0** will not receive credit and must be revised and resubmitted.

---

## Detailed Scoring Matrix

| Score | Classification | Criteria & Expectations |
| :---: | :--- | :--- |
| **5** | **Outstanding** *(Maximum Score)* | Addresses **ALL** project requirements with exemplary quality:<br>• **Outstanding RAG Application**: Correct responses with accurately matching citations; ingest and vector indexing execute flawlessly.<br>• **Excellent Architecture**: Clean, modular, well-structured application architecture separating ingestion, retrieval, LLM orchestration, and API/UI serving.<br>• **Optional Public Deployment**: Public deployment on Render, Railway (or equivalent free tier) is fully functional and accessible.<br>• **Robust CI/CD**: GitHub Actions workflow runs cleanly on every push/PR with dependency installation and build/smoke tests.<br>• **Excellent Design Documentation**: In-depth justifications of all architectural decisions (embedding model, chunking, $k$, prompt format, vector DB) in `design-and-evaluation.md` and transparent AI tool reflections in `ai-tooling.md`.<br>• **Rigorous Evaluation**: High-quality empirical results covering groundedness, citation accuracy, and $p_{50}$/$p_{95}$ latency over a comprehensive benchmark dataset.<br>• **Compelling Video Demonstration**: Clear, professional 5–10 min screen-share demo covering all features, design, evaluation, and CI/CD with full member presence, speaking, and ID verification. |
| **4** | **Very Good** | Addresses **MOST** project requirements:<br>• Excellent RAG application with correct responses and generally matching citations; indexing works.<br>• Very good, well-structured application architecture.<br>• Optional public deployment almost fully functional.<br>• CI/CD runs on push/PR.<br>• Very good documentation of design choices.<br>• Very good evaluation results covering groundedness, citation accuracy, and latency.<br>• Very good, clear demo of features, design, and evaluation. |
| **3** | **Good** | Addresses **SOME** project requirements:<br>• Very good RAG application with mainly correct responses and generally matching citations; indexing works.<br>• Good, well-structured application architecture.<br>• Optional public deployment partially functional or omitted.<br>• CI/CD runs on push/PR.<br>• Good documentation of design choices.<br>• Good evaluation results including most required metrics.<br>• Good, clear demo of features, design, and evaluation. |
| **2** | **Passable** *(Minimum Passing)* | Addresses **FEW** project requirements:<br>• Passable RAG application with limited correct responses and few matching citations; indexing works partially.<br>• Passable application architecture.<br>• Public deployment not fully functional or absent.<br>• CI/CD runs on push/PR.<br>• Passable documentation of design choices.<br>• Passable evaluation results covering only some metrics.<br>• Passable demo of features, design, and evaluation. |
| **1** | **Unsatisfactory** *(Failing)* | Addresses the project but **MOST** requirements are missing:<br>• Incomplete or non-functional application.<br>• No CI/CD workflow configured.<br>• No or very limited evaluation performed.<br>• Missing design documentation.<br>• No video demonstration provided. |
| **0** | **No Credit** *(Failing)* | Student did not complete the assignment, plagiarized all or part of the submission, or completely failed to address the project requirements. |

---

## Key Rubric Pillars for Score 5 Execution

1. **RAG Pipeline Fidelity**: Chunking captures complete semantic units; retrieval consistently surfaces relevant passages; prompt engineering strictly enforces groundedness; and citations reliably point to supporting excerpts without hallucinations.
2. **Defensive Guardrails**: System cleanly identifies and refuses out-of-scope inquiries with the mandated policy-bound refusal statement.
3. **Comprehensive Evaluation**: Metrics are quantitatively calculated across 15–30 diverse questions with clear reporting of groundedness %, citation accuracy %, and response latencies ($p_{50}$ and $p_{95}$).
4. **CI/CD & Operational Discipline**: GitHub Actions automatically verifies application importability and runs smoke tests on push/PR.
5. **Presentation & Academic Integrity**: Video demonstration adheres strictly to time constraints (5–10 min), verifies member identity on camera, and cleanly presents all required technical deliverables.
