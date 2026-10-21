# Development Phase 4: Controlled Retrieval Diagnosis and Evidence Audit

This is an opt-in offline workflow for CiteFirst Phase 4 development.
Phase 4 development focuses on **controlled retrieval diagnosis, metric reconciliation, and evaluation infrastructure**.
It is completely separate from the application's internally named "Phase 4" answer-generation stage.
The 18 reviewed questions (Q001–Q018) are development cases; they are not untouched held-out data.
Candidate question cards Q019–Q026 are approved by the project owner (`human_verified: true`). All 16 secondary relevance decisions (8 relevant, 8 nonrelevant) and 4 corrective fixtures (`human_verified: true`) were signed by Qusai on 2026-10-21 and imported. All 26 generated-answer verdicts across Q001–Q026 were personally evaluated and signed by Qusai on 2026-10-21 in `phase4_human_answer_verdict_form.md` (SHA-256: `172bb3a46973534430aa2c2e909cac76a76d0801c2618dbd22ca80a152ceeb08`) and structured in `phase4_human_answer_verdicts.json`. (Historical pre-sign-off state: previously proposed as unjudged / pending review).
No production defaults have been modified.

---

## 1. Frozen Control, Provenance, and Verification

The evaluation environment and baseline control are strictly anchored to audited local files:

| Item | Local Recorded Value & Integrity Fingerprint | Verification Method & Limits |
| :--- | :--- | :--- |
| **Source Base** | `phase3/evidence-evaluation` at `36d088f6799b6fa357cdc96fb50a5310b78844aa`<br>`origin/main` at `e4952fc3e134db02afb626ac920a1fcbc6a689b8` | `git rev-parse`; both resolve to identical tree `fc27a90e2cd44cdc14555384e41852b763074dce` (0 diff) |
| **Reviewed Dataset** | `reviewed_dataset.json` (18 eligible records)<br>SHA-256: `395b11567576562e5528c52801f0c8da79f86cbd66fc8e7ec0e1dad8ea847487` | Cryptographic SHA-256 digest of exact file bytes. Preserves all 18 human-approved dispositions. |
| **Evaluation Index** | `vector_vault_eval` directory:<br>Child chunks (`ieee_papers`): 7,816<br>Parent chunks (`ieee_papers_parent`): 2,418<br>Index Tag: `vault-eval-c7816-p2418-sha256-4035c42aeb62` | Verified via ChromaDB collection counts and schema checks. Read-only; never rebuilt or overwritten. |
| **Corpus Digest Limit** | Reported PDF corpus manifest SHA-256:<br>`4035c42aeb626527ef714fd3105fdab3157a095bae64f782d84add65558e2583` | **Important limitation:** A sorted PDF file-list digest and chunk counts do **not** constitute a cryptographic hash of the underlying SQLite/HNSW vector index bytes. |
| **BM25 Cache** | `vector_vault_eval/bm25_corpus.json`<br>SHA-256: `974089122253ea1eddcd4afca224aa6f5a15487be8f4f13f0ba478e2d90c6846` | File digest verified. Loaded via `rank_bm25` tokenizer cache. |
| **Dense Model** | `BAAI/bge-small-en-v1.5`<br>Prefix: `Represent this sentence for searching relevant passages: ` | Loaded lazily on CPU via sentence-transformers/HuggingFace cache. |
| **Reranker Model** | `BAAI/bge-reranker-base` | Loaded lazily on CPU via CrossEncoder. |
| **Runtime Settings** | `settings.json`<br>SHA-256: `da7f4b49f6b70b3482753755dbc0cea1984c75ca757bdfb3810fcb9c10f4aeae` | Loaded via `settings_config.load_settings()`. `DISTANCE_THRESHOLD=0.70`, `FETCH_K=30`, `PROCESS_K=10`, RRF $k=60$. |

---

## 2. Metric Semantics and Protocol Distinctions

Metrics reported across CiteFirst are defined with strict semantics to avoid inflated or misleading claims:

1. **Known-Positive Source Hit@K:**
   - Evaluates whether the specific known-positive source paper appears in the top $K$ *distinct papers* of the retrieved candidate pool.
   - Distinct papers are deduplicated preserving the rank of their highest-scoring chunk.
   - **Available Denominator:** If a 30-chunk pool contains fewer than $K$ distinct papers, the cutoff is marked *unavailable* for that query. The metric is computed strictly over available queries ($N_{\text{avail}} \le 18$).
2. **Known-Source MRR (Mean Reciprocal Rank):**
   - Reciprocal of the 1-based rank of the first occurrence of the known source paper ($\frac{1}{\text{rank}}$). If not found, score is 0.
3. **Historical First-Ten-Chunks Protocol:**
   - Historical Phase 3 protocol requested only 10 raw chunks. Queries with fewer than $K$ distinct papers were padded as failures rather than marked unavailable.
   - Coverage over 18 queries was: $K=1$ (18/18), $K=3$ (3/18), $K=5$ (2/18), $K=10$ (0/18).
4. **Disallowed Unjudged Metrics:**
   - We do **not** calculate corpus-wide Recall@K (secondary relevant papers across the 66-paper corpus remain unjudged).
   - We do **not** calculate Precision@K or NDCG@K from unjudged papers.
   - Unjudged candidate papers are **never** treated as negative distractors.

---

## 3. Discrepancy Reconciliation and Audit Findings

Auditing the bundled artifacts and raw historical data identified and resolved the following discrepancies:

1. **Hybrid Pool-30 Hit@1 Contradiction:**
   - Previous narrative reports claimed 18/18 for Pool-30 Hit@1.
   - **Correct Evidence:** `phase4-hybrid.json` reports **17/18 (0.9444)**. Q015 is at paper rank 2 behind `2002.08909v1.pdf`. The correct known-source MRR is **0.9722**.
   - Available cutoff counts in 30 chunks: $K=3$ has 9 available (9/9), $K=5$ has 5 available (5/5), $K=10$ has 1 available (1/1).
2. **Average Distinct Papers in Top 30 Chunks:**
   - Previous report claimed 4.39 (hybrid), 2.94 (dense), and 7.67 (BM25).
   - **Correct Evidence:** Hybrid averages **3.78**, Dense-only averages **2.33**, and BM25-only averages **7.06**.
3. **Dense-Only and BM25-Only Cutoff Coverage:**
   - Dense-only $K=3$ coverage is **6/18** (with known source found for 5/6 available queries, 0.8333).
   - BM25-only $K=5$ coverage is **11/18** and $K=10$ coverage is **4/18** (not 14/18 and 6/18).
4. **Q015 Fused Chunk IDs and Page Metadata:**
   - Fused rank-2 source chunk in hybrid trace: `ecf4a7334cc085e2_p1_child_6` from `2005.11401v4.pdf` (physical page 2).
   - Approved page-3 chunk: `ecf4a7334cc085e2_p2_child_19` at fused chunk rank 4.
5. **Historical Q015 Competitor Log Audit:**
   - Previous narrative text mentioned `1294261.1294281.pdf` (The Tail at Scale) as the rank-1 competitor.
   - Local inspection of the raw Phase 3 logs (`evaluation_results/phase3-document-pool-30-pilot/per-question.jsonl` from commit `50e182c4197f3eeb3f1203942424683c2cd7c60b`) confirmed that Rank 1 was **always `2002.08909v1.pdf` (REALM)**.
   - The reference to `1294261.1294281.pdf` in the Phase 3 pilot summary was an isolated transcription clerical error.
6. **Reranker Latency:**
   - The 18 latency values in the previous frozen-rerank audit averaged **22.67s** per query on CPU (not 21.8s).
   - In the finalized verified run (`phase4-hybrid-rerank-30-final.json`), scoring all 30 candidate pairs averaged **36.13s** per query.
7. **Correction of Q019–Q026 Card Subjects:**
   - The report narrative previously referenced outdated card subjects. The actual bundled JSON (`phase4_new_questions.json`) and physical PDFs establish:
     - **Q019:** GANs (`1406.2661v1.pdf`, Proposition 1 p.4, Theorem 1 p.5)
     - **Q020:** Adam (`1412.6980v9.pdf`, Hyperparameters p.2, Bias correction p.2–3)
     - **Q021:** ResNet (`1512.03385v1.pdf`, Residual mapping $F(x) := H(x)-x$ p.2, Shortcuts p.3)
     - **Q022:** CRAG (`2401.15884v3.pdf`, Action triggers {Correct, Incorrect, Ambiguous} p.5)
     - **Q023:** GFS (`945445.945450.pdf`, 64 MB chunk size, lazy allocation p.4)
     - **Q024:** SELF-RAG (`2310.11511v1.pdf`, Reflection tokens Retrieve, IsRel, IsSup, IsUse p.4)
     - **Q025:** AMA (`AMA_AdaptiveMemoryviaMultiAgentCollaboration_compressed.pdf`, 4 agents p.3)
     - **Q026:** X-ray CGM (`2603.25600v1.pdf`, OVII resonant line at 574 eV p.1)

---

## 4. Local Experimental Results

### Candidate Pool Retrieval Diagnostics (Candidate Pool = 30)

Diagnostic runs on the 18 development questions (`phase4_diagnostics.py`):

| Metric | Hybrid (Control) | Dense-Only | BM25-Only | Hybrid + Frozen 30 Rerank |
| :--- | :--- | :--- | :--- | :--- |
| **Known-Source Hit@1** | 17/18 (0.9444) | 17/18 (0.9444) | 17/18 (0.9444) | **18/18 (1.0000)** |
| **Known-Source Hit@3** | 9/9 (1.0000) (9 unavail) | 5/6 (0.8333) (12 unavail) | 16/16 (1.0000) (2 unavail) | **9/9 (1.0000) (9 unavail)** |
| **Known-Source Hit@5** | 5/5 (1.0000) (13 unavail) | 2/2 (1.0000) (16 unavail) | 11/11 (1.0000) (7 unavail) | **5/5 (1.0000) (13 unavail)** |
| **Known-Source Hit@10** | 1/1 (1.0000) (17 unavail) | 0/0 (n/a) (18 unavail) | 4/4 (1.0000) (14 unavail) | **1/1 (1.0000) (17 unavail)** |
| **Known-Source MRR** | 0.9722 | 0.9583 (-0.0139) | 0.9722 (0.0000) | **1.0000 (+0.0278)** |
| **First Chunk Rank 1** | 17/18 (0.9444) | 17/18 (0.9444) | 17/18 (0.9444) | **18/18 (1.000)** |
| **Survive PROCESS_K (10)** | n/a | n/a | n/a | **18/18 (1.000)** |
| **Survive Adaptive Softmax** | n/a | n/a | n/a | **17/18 (0.9444)** |
| **Avg Distinct Papers (Top 30)**| 3.78 | 2.33 | 7.06 | 3.78 (evaluated pool) |
| **Mean Timing (Seconds)** | 3.67s | 2.03s | 0.35s | 36.13s (CPU) |

### Regression Review:
- **Dense-Only:** Fails Q015 severely (known source drops to rank 4). Heavy source crowding (only 2.33 distinct papers per 30 chunks).
- **BM25-Only:** Promotes Q015 to rank 1, but regresses Q005 (`1810.04805v2.pdf`, BERT) from rank 1 to rank 2.
- **Frozen 30 Reranker:** Verified with `prerank_candidate_ids == rerank_candidate_ids`. Promotes all 18 known sources to rank 1. Approved page survives into `PROCESS_K` for 18/18 cases and adaptive selection for 17/18 cases.

---

## 5. Observational Initial-Stage Simulation of Production Path

In the user-facing application, `database.py` executes:
```python
fetch_n = n_results * 3 # FETCH_K=30 -> fetch_n=90
```
`search_vault(n_results=30)` retrieves up to 90 merged chunks and filters by distance threshold (0.70), returning 47–90 chunks.
`logic_engine.evaluate_chunks()` scores **all** returned chunks with `BAAI/bge-reranker-base`.

The script `scripts/capture_normal_production_path.py` implements an **observational initial-stage simulation** of retrieval, batched cross-encoder reranking, adaptive selection, and initial `CORRECT` classification. It does **not** execute actual ambiguous resolution, supplemental retrieval, the combined preflight LLM check, query rewrite, final generation, or the complete `logic_engine.run_logic_engine` control flow.

Observational capture (`scripts/capture_normal_production_path.py` -> `evaluation_results/normal_production_path_trace.json`) confirms:
- **Candidate Pool:** 47–90 pre-filtered chunks (mean 82.50 chunks) are retrieved and scored by the reranker per query.
- **Paper Rank 1:** Raw pre-rerank paper rank 1 is **17/18** (Q015 raw rank 2); post-rerank paper rank 1 is **18/18 (100%)**.
- **Approved Passage in Initial-Stage Selected Context:** **14/18 (77.78%)**:
  - *Note:* This 14/18 result is an **initial-stage simulation observation**, not a measured final generation-context success rate across the full pipeline.
  - **Q001:** Targets `rsta.1895.0004.pdf` (approved page 17; initial selected page 16).
  - **Q008:** Targets `Experiencing_Immersive_Virtual_Nature_for_Well-Being_Restoration_Performance_and_Nature_Connectedness_A_Scoping_Review.pdf` (approved pages 4, 5, 8; initial selected pages 6, 7).
  - **Q009:** Targets `Exploration_on_Experimental_Economics_and_the_Education_Reform_of_New_Finance_and_Economics.pdf` (approved page 1; initial selection page 2; approved page 1 placed at candidate rank 10 and was pruned by the gentle 0.90 softmax mass cutoff).
  - **Q011:** Targets `PIIS0092867411001279.pdf` (approved pages 17, 18; zero chunks achieved `sigmoid_score >= CORRECT_THRESHOLD` of 0.55; all 9 top-K chunks scored `AMBIGUOUS` in [0.25, 0.55), producing an initial no-`CORRECT` signal).
- **Initial No-CORRECT Signal Count:** **1/18 (5.56%)** (Q011 only; this is an initial signal, not the actual fallback rate after ambiguous resolution).
- **Latency (CPU):** Total initial-stage latency averaged **93.84s** (retrieval: 3.47s, reranking: 90.37s). This excludes later pipeline stages, supplemental retrieval, and answer generation.
- **Live Provider Generation Status:** Recorded as **`NOT RUN`** in initial simulation.

---

## 6. Human Evidence Review Decisions & Pilot Split

### Candidate Cards Q019–Q026 Status: Human Verified
All 8 candidate question cards in `docs/evaluation/phase4_new_questions.json` are **APPROVED** by `project owner (user)` on `2026-10-20, Asia/Kolkata`:
- `human_verified: true`
- `reviewer: "project owner (user)"`
- `review_date: "2026-10-20, Asia/Kolkata"`
- `provenance: "Explicit human approval against physical PDF pages"`
- **Q025 Quotation Repair:** Repaired verbatim from page 3 Figure 2 caption (`"The system orchestrates four agents to enable adaptive memory evolution. The Retriever routes inputs to optimal granularities based on intent. The Judge audits content relevance to trigger feedback loops and detects conflicts. The Refresher executes updates or deletions to rectify these inconsistencies. Finally, the Constructor synthesizes the validated context into structured memory entries."`).
- **Q023 Corpus Check:** `raft.pdf` verified indexed in `vector_vault_eval` (`ieee_papers` collection, 5 chunks), retained as valid distractor.

### Secondary Relevance Rows (Signed 2026-10-21 by Qusai)
All 16 candidate rows in `docs/evaluation/phase4_relevance.json` were personally reviewed, signed, and dated by reviewer Qusai on 2026-10-21 and imported:
- 8 decisions `relevant`, 8 decisions `nonrelevant`
- `reviewer: "Qusai"`
- Conforms strictly to `phase4_relevance.schema.json`.
- Historical pre-sign-off state (prior to 2026-10-21): rows were initially recorded as `judgment: "unjudged"`, `reviewer: null` and were strictly never treated as negative distractors.

### Corrective Decision Fixtures (Signed 2026-10-21 by Qusai)
All 4 reference fixtures in `docs/evaluation/corrective_decision_fixtures.json` were personally reviewed, signed, and dated by reviewer Qusai on 2026-10-21 and imported:
- `proposal_status: "human_verified"`
- `human_verified: true`, `reviewer: "Qusai (signed 2026-10-21)"`
- Decisions: CORR-001 `relevant`, CORR-002 `partially_relevant`, CORR-003 `irrelevant`, CORR-004 `insufficient_evidence`.
- Page numbers verified against physical PDF pages: CORR-001/002 on Adam page 2; CORR-003 MultiHead attention on physical page 5 of `1706.03762v7.pdf` (formerly mislabeled page 3); CORR-004 on physical page 4 of `1512.03385v1.pdf`.
- CORR-002 working rationale distinguishes the single supplied passage (default hyperparameter values) from other content elsewhere in the Adam PDF (bias-corrected update formulas on page 2, and the Section 3 explanation on page 3 of why zero initialization causes early bias).
- Historical pre-sign-off state: previously proposed as `proposal_status: "unverified_proposal"`, `human_verified: false`.

### Prespecified Source-Grouped Split & Disclosed Pilot (`docs/evaluation/phase4_split_manifest.json`)
Historical split plan formulated prior to generation:
- **Development Fixed Set:** Q001–Q018 (15 papers)
- **Development Expansion Group:** GANs (`1406.2661v1.pdf`), Adam (`1412.6980v9.pdf`), ResNet (`1512.03385v1.pdf`), CRAG (`2401.15884v3.pdf`) $\rightarrow$ Total Development Generation Set: **22 questions (Q001–Q022) across 19 source papers**.
- **Historical Reserved Group / Actual Disclosed Pilot:** GFS (`945445.945450.pdf`), SELF-RAG (`2310.11511v1.pdf`), AMA (`AMA_AdaptiveMemory...`), CGM (`2603.25600v1.pdf`) $\rightarrow$ **4 questions (Q023–Q026) across 4 source papers**.
- **Split Terminology & Disclosed Pilot Status:** Because retrieval outcomes for Q023–Q026 had already been inspected prior to generation, Q023–Q026 constitute a **disclosed, previously exposed pilot**, NOT a pristine or untouched holdout. The completed pilot must not be called pristine.
- **Small Sample Limitation:** 4 questions across 4 papers is a small pilot. It cannot establish broad statistical generalization.
- **Abstention Status:** Scored $N = 0$. Evaluation of abstention is deferred until human-verified unanswerable cases are established.

---

## 7. Signed Human Answer Evaluation Results (Signed 2026-10-21 by Qusai)

All 26 generated answers (OpenRouter `meta-llama/llama-3.3-70b-instruct`) were personally evaluated, graded, and signed by reviewer Qusai on 2026-10-21:
- **Authoritative Signed Form:** [`phase4_human_answer_verdict_form.md`](../../phase4_human_answer_verdict_form.md) (SHA-256: `172bb3a46973534430aa2c2e909cac76a76d0801c2618dbd22ca80a152ceeb08`)
- **Structured Results Artifact:** [`docs/evaluation/phase4_human_answer_verdicts.json`](phase4_human_answer_verdicts.json) conforming to [`phase4_human_answer_verdicts.schema.json`](phase4_human_answer_verdicts.schema.json).

### Metric Definitions
- **Overall Human Verdict:**
  - `ACCEPT`: The generated answer directly and factually answers the core question with grounded claims and without substantive omission or distortion.
  - `PARTIAL`: The answer substantively answers a significant part of a compound question or provides partially correct/grounded information, but omits key required claims or is hindered by refusal phrasing despite partial coverage.
  - `REJECT`: The answer fails to answer the question, omits all or nearly all required claims (typically via soft refusal), or provides incorrect answers to the core question.
- **Factual Correctness (vs. Gold Reference):** `Correct` (all facts accurate), `Partially Correct` (some facts accurate, some missing/inaccurate), `Incorrect` (core facts inaccurate or omitted).
- **Faithfulness (vs. Context Passed to LLM):** `Faithful` (all statements strictly grounded in passed chunks), `Partially Faithful` (minor ungrounded inferences), `Unfaithful` (hallucinations contrary to passed context).
- **Citation Support:** `Supported` (cited paper supports the claims), `Partially Supported` (citation partially relevant or lacks page/claim precision), `Unsupported` (citation off-topic).

### Partitioned Results Summary

| Evaluation Partition | Total Questions | ACCEPT | PARTIAL | REJECT | Factual Correctness (C / PC / I) | Faithfulness (F / PF / U) | Citation Support (S / PS / U) | Claim Coverage (Cov / Part / Omit) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development (Q001–Q022)** | 22 | **2 (9.1%)** | **9 (40.9%)** | **11 (50.0%)** | 2 / 12 / 8 | 19 / 3 / 0 | 16 / 6 / 0 | 14 / 21 / 39 (N=74 claims) |
| **Disclosed Pilot (Q023–Q026)** | 4 | **4 (100.0%)** | **0 (0.0%)** | **0 (0.0%)** | 4 / 0 / 0 | 4 / 0 / 0 | 4 / 0 / 0 | 9 / 0 / 0 (N=9 claims) |
| *Combined Descriptive Total* | *26* | *6 (23.1%)* | *9 (34.6%)* | *11 (42.3%)* | *6 / 12 / 8* | *23 / 3 / 0* | *20 / 6 / 0* | *23 / 21 / 39 (N=83 claims)* |

*Note: The four pilot questions (Q023–Q026) were previously exposed during retrieval inspection; their 4/4 ACCEPT rate reflects a disclosed pilot, NOT an untouched holdout result.*

### 26-Question Audit Table

#### Development Set (Q001–Q022)
| QID | Target Paper | Route | Overall Verdict | Factual Correctness | Faithfulness | Citation Support | Checked Pages | Reviewer Rationale Summary |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Q001** | `rsta.1895.0004.pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 17 (context p. 7) | Faithful soft refusal that omits all three required claims; does not answer question. |
| **Q002** | `An_Experimentalist_Approach...pdf` | `partial_match` | **PARTIAL** | Partially Correct | Faithful | Partially Supported | p. 5 | Covers procedural justice partially; omits Rawls/Habermas philosophical synthesis. |
| **Q003** | `Comparisons_of_Observational...pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 1, 2 (context); approved p. 3–4 also checked | Faithful soft refusal; omits all four required claims. |
| **Q004** | `2603.25694v1.pdf` | `success` | **PARTIAL** | Partially Correct | Faithful | Partially Supported | p. 20 | Answers 'what' (degeneracy exists) but omits the 'why' requested by question. |
| **Q005** | `From_Ethics_Washing...pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 11, 14, 15 | Soft refusal omitting all claims; approved pages were missing from passed context. |
| **Q006** | `Akiyama_2019_ApJL_875_L1.pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 2, 5, 6, 8, 9 | Soft refusal omitting all four required claims; approved pages missing from context. |
| **Q007** | `1807.06209v4.pdf` | `success` | **PARTIAL** | Partially Correct | Faithful | Supported | p. 29, 30, 31 | Covers claims 2–4 but omits p.29 degeneracy-direction claim entirely. |
| **Q008** | `Experiencing_Immersive...pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 4, 5, 8 | Soft refusal omitting all claims; approved pages were not in passed context (had p. 2, 3). |
| **Q009** | `Exploration_on_Experimental...pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 1 | Soft refusal omitting all claims; approved page 1 missing from passed context (had p. 2). |
| **Q010** | `1294261.1294281.pdf` | `success` | **REJECT** | Partially Correct | Partially Faithful | Partially Supported | p. 4 | Direct answer on customer experience omitting tail-latency/cost claims; states context lacks direct quote. |
| **Q011** | `PIIS0092867411001279.pdf` | `partial_match` | **REJECT** | Incorrect | Faithful | Supported | p. 17, 18 | Soft refusal omitting all claims; ambiguous retrieval scores triggered fallback. |
| **Q012** | `Structural_formation...pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 5 | All required claims correctly and concisely stated, fully grounded on approved p. 5. |
| **Q013** | `PIIS0092867411001279.pdf` | `partial_match` | **PARTIAL** | Partially Correct | Partially Faithful | Partially Supported | p. 18 | Required claims substantively accurate, but answer frames itself as refusal. |
| **Q014** | `Dance_Guiding_Art...pdf` | `partial_match` | **PARTIAL** | Partially Correct | Partially Faithful | Partially Supported | p. 1, 2, 3 | Refusal-style answer covering parts of claims 1–3, but omits claim 4. |
| **Q015** | `2005.11401v4.pdf` | `partial_match` | **REJECT** | Partially Correct | Faithful | Supported | p. 3, 4, 7 | Soft refusal omitting most required claims (omits 21M Wikipedia FAISS details). |
| **Q016** | `On_the_Response_of_Nano...pdf` | `partial_match` | **REJECT** | Partially Correct | Faithful | Supported | p. 2, 5, 6, 7 | Soft refusal omitting all substantive required claims; faithful to limited context. |
| **Q017** | `On_the_Response_of_Nano...pdf` | `partial_match` | **REJECT** | Partially Correct | Faithful | Supported | p. 5, 7 | Soft refusal omitting most required claims; faithful to limited context. |
| **Q018** | `rsta.1895.0004.pdf` | `success` | **PARTIAL** | Partially Correct | Faithful | Supported | p. 17 | Covers two claims fully, two partially; misses intermediate step in dissipation. |
| **Q019** | `1406.2661v1.pdf` | `success` | **PARTIAL** | Partially Correct | Faithful | Supported | p. 4, 5 | Covers global minimum fully; only partially addresses optimal discriminator formula. |
| **Q020** | `1412.6980v9.pdf` | `success` | **PARTIAL** | Incorrect | Faithful | Partially Supported | p. 2, 3 | Initialization bias correct, but defaults incorrect due to AdaMax confusion. |
| **Q021** | `1512.03385v1.pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 2, 3 | Both required claims fully covered and grounded in ResNet p. 2–3 context. |
| **Q022** | `2401.15884v3.pdf` | `success` | **PARTIAL** | Partially Correct | Faithful | Supported | p. 5 | States three actions correctly, but omits knowledge refinement processing details. |

#### Disclosed Pilot Set (Q023–Q026)
| QID | Target Paper | Route | Overall Verdict | Factual Correctness | Faithfulness | Citation Support | Checked Pages | Reviewer Rationale Summary |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Q023** | `945445.945450.pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 4 | Covers all three claims (64MB chunk size, plain Linux files, lazy allocation). |
| **Q024** | `2310.11511v1.pdf` | `partial_match` | **ACCEPT** | Correct | Faithful | Supported | p. 4 | Fully covers reflection tokens and evaluator roles despite partial_match route. |
| **Q025** | `AMA...pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 3 | Correctly defines four agents (Retriever, Judge, Refresher, Constructor) and roles. |
| **Q026** | `2603.25600v1.pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 1 | Fully covers OVII resonant line and transition energy E = 574 eV for CGM mass. |

### Grounding & Failure Mode Analysis

#### Three Distinct Grounding Levels
1. **Target Filename Citation:** The target filename string appears in the model output (e.g., citing `'rsta.1895.0004.pdf'`). Emitted in 26/26 cases (100%); purely lexical, does **not** establish that the text or claims from that paper were used or supported.
2. **Approved Physical Page Presence:** The physical page containing the gold answer was present in `exact_context_passed_to_generation`. Present in 19/26 cases (73.1%, missing for Q005, Q006, Q008, Q009, Q011, Q020, and Q022).
3. **Human-Verified Answer Acceptance:** 6/26 generated answers received an overall ACCEPT verdict (2/22 Development, 4/4 Disclosed Pilot). This is an answer-level verdict, not a claim-support rate. Required claim coverage across all 83 evaluated claims is: 23 Covered (27.7%), 21 Partial (25.3%), and 39 Omitted (47.0%) [Dev: 14 Covered, 21 Partial, 39 Omitted; Pilot: 9 Covered, 0 Partial, 0 Omitted]. Citation support at the answer level is 20/26 Supported (76.9%) and 6/26 Partially Supported (23.1%).

#### Primary Failure Modes
- **Failure Mode 1 (Retrieval Gap — Missing Approved Pages):** For Q005, Q006, Q008, Q009, Q011, Q020, and Q022 (7/26 cases), the approved physical pages were absent from final generation context (e.g., Q008 context contained pages 2 and 3 rather than approved 4, 5, 8; Q009 context contained page 2 instead of approved page 1; Q020 context contained Section 7 / AdaMax on page 9 instead of Algorithm 1 on pages 2–3).
- **Failure Mode 2 (Refusals and Hedging with Present Context):** For questions such as Q001, Q002, Q003, Q013, Q014, and Q017, the model emitted explicit template refusals ("Direct Answer Not Found") even when relevant passages or approved pages were present in the passed context (e.g., in Q001, approved page 17 was present in chunk 2, but the model opened with a refusal). Questions like Q006, Q011, Q015, and Q016 opened with "couldn't find a direct answer", whereas Q010 answered directly regarding customer experience but omitted tail-latency contracts and noted the context lacked a direct quote. We distinguish directly observed text (refusal openings vs. omitted claims) from inferred pipeline causes (prompt hedging, reranker truncation).
- **Failure Mode 3 (AdaMax vs. Adam Parameter Confusion):** In Q020, because passed context contained Section 7 (AdaMax on p. 9), the model cited AdaMax parameters ($\beta_1=0.9, \beta_2=0.999$, but no $\epsilon=10^{-8}$; instead $\gamma, \alpha$), leading to an `Incorrect` factual correctness rating while the bias explanation was supported (`PARTIAL` overall).
- **Failure Mode 4 (Pipeline Route Independence):** Pipeline `success` route does not imply human `ACCEPT`. Q004, Q007, Q010, Q018, Q019, Q020, and Q022 executed on the `success` route but received human `PARTIAL` or `REJECT` due to omitted required claims.

### Evaluation Scope & Limits
1. **No Corpus-Wide Retrieval Precision/Recall:** The 16 selected secondary relevance judgments evaluate specific candidate rows and do not establish corpus-wide retrieval recall across all 66 papers.
2. **Partition Integrity:** Development questions (Q001–Q022) represent an iterative development evaluation partition (not a pristine blind set); Q023–Q026 are a disclosed, previously exposed pilot (retrieval candidates were inspected prior to generation). Neither partition constitutes an untouched holdout benchmark.
3. **Quality Threshold:** Completing the evaluation documents actual baseline performance (Dev ACCEPT rate: 2/22 = 9.1%); it does not imply that the application has achieved production readiness. True untouched evaluation across unexposed papers remains future work.
