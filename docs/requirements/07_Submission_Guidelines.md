# Submission Guidelines

Your final project submission must be submitted as a **single PDF document** containing two accessible URLs:
1. A link to your accessible **GitHub repository**.
2. A link to your **recorded video demonstration**.

---

## 1. GitHub Repository Deliverables

The GitHub repository must be shared with the GitHub account **`quantic-grader`** and must include the following components:

- **Complete Source Code**: All scripts for document ingestion, vector storage, RAG pipeline, web application, tests, and CI/CD workflows.
- **Corpus Files**: The curated set of policy documents in raw text, markdown, HTML, or PDF format.
- **`README.md`**:
  - Comprehensive overview of the project.
  - Step-by-step local environment setup and installation commands (`pip install -r requirements.txt`).
  - Instructions on how to run document indexing and start the web application.
  - API endpoint documentation with example `curl` commands.
- **`design-and-evaluation.md`**:
  - **Design & Architecture Decisions**: Detailed rationale for technology choices (embedding model, chunking strategy, retrieval $k$, prompt engineering format, vector store, web framework).
  - **Evaluation Approach & Results**: Summary of the evaluation methodology, dataset composition, and empirical results for groundedness, citation accuracy, and $p_{50}$/$p_{95}$ latency (including any ablation studies).
- **`ai-tooling.md`**:
  - Transparent description of the AI code generation tools, IDEs, and agents utilized (e.g., Gemini, Claude, Cursor, Antigravity, Copilot).
  - Practical reflection on what workflows succeeded, limitations encountered, and prompt engineering strategies used for code generation.
- **`deployed.md` (Optional)**:
  - If you deployed the application to a cloud host (Render, Railway, etc.), provide the live, publicly accessible URL and testing instructions.

---

## 2. Video Demonstration Requirements

- **Duration**: Between **5 and 10 minutes** in length.
- **Format**: High-quality screen-share recording with clear voiceover audio.
- **Identity Verification**:
  - **All group members must be visibly present on camera and show their valid government-issued ID** at the beginning of the video.
  - **All group members must actively speak** during the presentation.
- **Required Video Sections**:
  1. **Identity & Introductions**: Member introduction and ID display.
  2. **Live Application Demo**:
     - Submitting standard policy questions and verifying generated answers.
     - Demonstrating citation accuracy and source snippet preview functionality.
     - Demonstrating guardrails in action (e.g., submitting out-of-scope queries and observing proper refusal).
     - Demonstrating the `/health` endpoint.
  3. **Architecture & Design Walkthrough**: Brief summary of ingestion, vector indexing, retrieval, and prompt injection pipeline.
  4. **Evaluation Summary**: Review of groundedness, citation accuracy, and latency metrics.
  5. **CI/CD & Deployment**: Brief walkthrough of the GitHub Actions workflow run and (if applicable) the live deployed application.

---

## 3. Submission Procedure

- Ensure your GitHub repository visibility settings grant access to **`quantic-grader`**.
- Export your submission as a **single PDF document** containing the GitHub URL and the video link (hosted on YouTube Unlisted, Loom, Google Drive with public view permissions, or Vimeo).
- Upload the PDF via the **"Submit Project"** button on the student dashboard.
- If working in a team of up to three members, **only ONE member submits** on behalf of the group.
- For questions or support, contact `msse+projects@quantic.edu`.
