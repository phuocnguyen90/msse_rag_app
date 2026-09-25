# Evaluation and Metrics Requirements

Rigorous evaluation is essential to confirm that your RAG pipeline generates truthful, grounded responses and meets operational performance standards.

---

## 1. Evaluation Benchmark Dataset

- **Dataset Size**: Construct an evaluation set of **15 to 30 test questions** reflecting real-world employee queries.
- **Coverage**: Questions must span across multiple policy domains:
  - Paid Time Off (PTO), parental leave, sick days
  - Information security and acceptable equipment use
  - Travel, meal, and lodging expense reimbursement
  - Remote and hybrid work guidelines
  - Company observed holidays and working hours
  - Out-of-scope / adversarial test queries (designed to verify guardrail refusal behavior)
- **Reference Elements**: For each question in the benchmark dataset, provide:
  - `question_id`: Unique identifier
  - `question`: Test prompt
  - `ground_truth_answer`: Reference gold answer
  - `ground_truth_doc_ids`: Expected citation document IDs and sections
  - `expected_behavior`: Normal answer vs. Guardrail refusal

---

## 2. Required Answer Quality Metrics

You must evaluate and report the following information-quality metrics:

1. **Groundedness (% Consistency)** (Required):
   - **Definition**: The percentage of generated answers whose factual content is strictly consistent with and fully supported by the retrieved context.
   - **Criteria**: Answers must not hallucinate facts or introduce claims absent from or contradicted by the source passages.
   - **Formula**:
     $$\text{Groundedness} = \frac{\text{Number of Grounded Answers}}{\text{Total Evaluated Answers}} \times 100\%$$

2. **Citation Accuracy (% Correct Attribution)** (Required):
   - **Definition**: The percentage of answers whose listed citations correctly point to the specific passage(s) directly backing the stated information.
   - **Criteria**: Citations must be precise, verifiable, and not deceptive or irrelevant.
   - **Formula**:
     $$\text{Citation Accuracy} = \frac{\text{Number of Accurately Cited Answers}}{\text{Total Evaluated Answers}} \times 100\%$$

3. **Exact / Partial Match (% Gold Agreement)** (Optional):
   - Percentage of generated answers that match or semantically capture the concise gold-standard answer.

---

## 3. Required System Performance Metrics

You must measure and report system operational metrics:

- **Latency (p50 and p95)** (Required):
  - Measure the end-to-end response time (from question receipt to complete answer delivery) across **10 to 20 representative queries**.
  - Report:
    - **Median Latency ($p_{50}$)**: The 50th percentile response time.
    - **Tail Latency ($p_{95}$)**: The 95th percentile response time, capturing worst-case delays.
  - Break down latency into retrieval vs. generation phases where feasible.

---

## 4. Optional Ablation Studies

To demonstrate advanced AI engineering rigor, consider conducting and reporting ablation experiments:
- **Retrieval Depth ($k$)**: Comparing performance with $k=2$, $k=4$, and $k=8$.
- **Chunk Size & Overlap**: Testing compact chunks (e.g., 256 tokens) vs. larger chunks (e.g., 1024 tokens).
- **Prompt Variations**: Comparing strict zero-shot grounding vs. few-shot chain-of-thought grounding.
