# CiteFirst Phase 4 Corrected Execution Report & Evidence Audit

- **Date:** 2026-10-20
- **Repository Branch:** `phase3/evidence-evaluation`
- **Local Commit:** `36d088f6799b6fa357cdc96fb50a5310b78844aa`
- **Target Upstream:** `origin/main` (`e4952fc3e134db02afb626ac920a1fcbc6a689b8`)
- **Status:** Open Development Phase 4 (Evaluation & Retrieval Audit; production defaults unchanged)

---

## 1. Exact Repository & Provenance State

### 1.1 Git Status and Tracked Tree Parity
- **Branch:** `phase3/evidence-evaluation` tracking `origin/phase3/evidence-evaluation`.
- **Local HEAD:** `36d088f6799b6fa357cdc96fb50a5310b78844aa`
- **Remote Upstream (`origin/main`):** `e4952fc3e134db02afb626ac920a1fcbc6a689b8`
- **Tree Verification:**
  - `git rev-parse HEAD^{tree}` $\rightarrow$ `fc27a90e2cd44cdc14555384e41852b763074dce`
  - `git rev-parse origin/main^{tree}` $\rightarrow$ `fc27a90e2cd44cdc14555384e41852b763074dce`
  - `git diff-tree HEAD origin/main` $\rightarrow$ **Empty (0 diff between tracked trees)**.
  - *Conclusion:* Tracked trees match 100% byte-for-byte at the commit boundary.

### 1.2 Full File Changes Inventory
- **Tracked Modifications:**
  - `README.md`: Documented opt-in Phase 4 diagnostic runner and development scope.
  - `components/settings/SettingsPanel.tsx`: Clarified `TOTAL_DOCS` as legacy UI setting unused by retrieval evaluation.
  - `database.py`: Added opt-in `trace` parameter and `candidate_source` filtering (`hybrid`, `dense-only`, `bm25-only`) to `search_vault`; preserved production fallback and parent expansion.
  - `docs/evaluation/methodology.md`: Added warning on development scope of 18 reviewed questions and protocol differences.
- **Untracked Additions:**
  - `phase4_diagnostics.py`: Diagnostic runner with CRLF dataset acceptance, metric aggregation, candidate-pool slicing for reranking, and JSON export.
  - `tests/test_phase4_diagnostics.py`: Unit test suite covering source ranks, trace preservation, mocked retrieval, CRLF hash acceptance, and candidate-window slicing.
  - `scripts/verify_frozen_30_rerank.py`: Standalone verification runner for frozen 30-candidate rerank audit.
  - `scripts/capture_normal_production_path.py`: Observational runner capturing normal production pipeline behavior.
  - `scripts/generate_report_tables.py`: Standalone table generation script computing verified metrics directly from JSON outputs.
  - `docs/evaluation/phase4.md`: Methodology, protocol specification, and reconciled metrics.
  - `docs/evaluation/decision_record_phase4_baseline.md`: Formal configuration decision record retaining hybrid baseline.
  - `docs/evaluation/phase4_new_questions.json`: Approved question cards (Q019–Q026) across 8 distinct unrepresented papers (`human_verified: true`, approved by project owner).
  - `docs/evaluation/phase4_new_questions.schema.json`: JSON schema for candidate cards.
  - `docs/evaluation/phase4_relevance.json`: 16 secondary source rows signed by reviewer Qusai on 2026-10-21 (8 relevant, 8 nonrelevant; historical pre-sign-off status: unjudged).
  - `docs/evaluation/phase4_relevance.schema.json`: JSON schema for secondary relevance annotations.
  - `docs/evaluation/corrective_decision_fixtures.json`: 4 fixtures distinguishing triage categories (`human_verified: true`, `proposal_status: "human_verified"`, signed by reviewer Qusai on 2026-10-21; historical pre-sign-off status: unverified_proposal).
  - `docs/evaluation/phase4_generation_worksheet.json`: Generation evaluation schema capturing exact context, prompt/model settings, faithfulness, citation page audits, latency, and cost.
  - `docs/evaluation/phase4_human_evidence_signoff.md`: Working copy of sign-off form reflecting all 20 accepted human decisions (16 relevance + 4 fixtures) signed by reviewer Qusai on 2026-10-21 with normalized post-sign-off descriptions. (Authoritative signed original preserved at repository root).
  - `docs/evaluation/phase4_human_answer_verdict_form.md`: Authoritative signed answer-verdict form signed by reviewer Qusai on 2026-10-21 covering all 26 QIDs (6 ACCEPT, 9 PARTIAL, 11 REJECT; SHA-256: `172bb3a46973534430aa2c2e909cac76a76d0801c2618dbd22ca80a152ceeb08`).
  - `docs/evaluation/phase4_human_answer_verdicts.json`: Structured machine-readable human answer verdicts across all 26 QIDs conforming to schema.
  - `docs/evaluation/phase4_human_answer_verdicts.schema.json`: JSON schema for structured human answer verdicts.

`git diff --check` executed with exit code 0 (clean, no trailing whitespace, no merge markers).

### 1.3 Reviewed Dataset Hash & CRLF Resolution
- **GitHub Origin Blob (`origin/main:reviewed_dataset.json`):**
  - Raw Size: **128,112 bytes**
  - Raw SHA-256: `11b467995f423495e53207539c20764cf8d531b71a3162de7b5c8a3d57b6417b`
  - Line Endings: Unix LF (`\n`, 791 line breaks).
- **Windows Working Copy (`reviewed_dataset.json`):**
  - Raw Size: **128,903 bytes**
  - Raw SHA-256: `395b11567576562e5528c52801f0c8da79f86cbd66fc8e7ec0e1dad8ea847487`
  - Line Endings: Windows CRLF (`\r\n`, exactly 791 line breaks).
- **Mathematical Equivalence:**
  - Byte Difference: $128,903 - 128,112 = +791$ bytes (exactly 1 extra byte per line break for carriage return `\r`).
  - Normalized LF Hash: Converting `\r\n` $\rightarrow$ `\n` produces exactly `11b467995f423495e53207539c20764cf8d531b71a3162de7b5c8a3d57b6417b`.
  - JSON Semantic Identity: `json.loads(origin_blob) == json.loads(local_file)` is `True`. All 18 approved dispositions, claim supports, and quotes are identical.
- **Handling in Code:**
  - `phase4_diagnostics.py` explicitly recognizes both raw hashes (`REVIEWED_SHA256` and `REVIEWED_SHA256_CRLF`).
  - Verified by unit test: `test_reviewed_dataset_crlf_and_lf_hashes_accepted`.
  - The actual raw hash used in local execution runs is preserved as `395b11567576562e5528c52801f0c8da79f86cbd66fc8e7ec0e1dad8ea847487`.

### 1.4 Artifact Provenance Summary
| Component | State / Digest | Provenance Verification Method & Limits |
|---|---|---|
| **66 PDFs** | `4035c42aeb626527ef714fd3105fdab3157a095bae64f782d84add65558e2583` | Exact SHA-256 of sorted sha256 sums of all 66 PDFs in `papers/`. |
| **Corpus Digest Limit** | Reported sorted manifest digest | **Critical Limit:** A PDF file list digest and chunk counts do **not** constitute a cryptographic fingerprint of vector-index bytes. |
| **Chroma Child Collection** | `ieee_papers`: 7,816 child chunks | Persistent Chroma collection count query. Unmodified. |
| **Chroma Parent Collection** | `ieee_papers_parent`: 2,418 parent chunks | Persistent Chroma collection count query. Unmodified. |
| **BM25 Cache** | `974089122253ea1eddcd4afca224aa6f5a15487be8f4f13f0ba478e2d90c6846` | Exact SHA-256 of `vector_vault_eval/bm25_corpus.json`. |
| **Runtime Settings Hash** | `da7f4b49f6b70b3482753755dbc0cea1984c75ca757bdfb3810fcb9c10f4aeae` | SHA-256 of loaded dictionary `json.dumps(load_settings(), sort_keys=True)`. |
| **Dense Model** | `BAAI/bge-small-en-v1.5` | Lazy CPU load; hub git revision unpinned (local cache). |
| **Reranker Model** | `BAAI/bge-reranker-base` | Lazy CPU load via `logic_engine._get_reranker()`. |
| **Hardware** | Windows 11 AMD64, multi-core CPU | Local CPU execution without CUDA. |

---

## 2. Artifact-to-Claim Audit & Reconciled Retrieval Metrics

### 2.1 Metric Scope & Semantics
- **Diagnostic Nature:** Evaluated exclusively on the 18 human-approved development questions across 15 papers.
- **Not Corpus-Wide Recall@K:** Unjudged secondary papers returned in candidate pools are not negative labels. Claiming true Recall@K requires exhaustive relevance judgments across all 66 papers for each query.
- **Precision@K & NDCG@K Ineligibility:** Precision@K requires binary relevance decisions on every document in the retrieved prefix. NDCG@K additionally requires defensible graded relevance labels and an ideal DCG baseline.
- **Terminology:** All values are reported as **"Known-Positive Source Hit@K"** and **"Known-Source MRR"** with explicit cutoff availability denominators.

### 2.2 Machine-Generated Per-Question Table (Q001–Q018)

*Table generated directly by `scripts/generate_report_tables.py` parsing `evaluation_results/phase4-hybrid.json`, `phase4-dense-only.json`, `phase4-bm25-only.json`, and `phase4-hybrid-rerank-30-final.json`:*

| QID | Target Gold Paper | Physical Pages | Hybrid Rank | Dense Rank | BM25 Rank | Post-Rerank Paper Rank | First Chunk Rank | Appr. Page Rank | Survive Process-K | Survive Adaptive | Distinct Papers (Top 30) | Available Cutoffs |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Q001** | `rsta.1895.0004.pdf` | 17 | 1 | 1 | 1 | **1** | 1 | 6 | Yes | Yes | 1 | K=1 |
| **Q002** | `An_Experimentalist_Approach_to_Ethical_Governance_of_Emerging_Technologies.pdf` | 5 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 9 | K=1, K=3, K=5 |
| **Q003** | `Comparisons_of_Observational_Angles_Between_Moon-Based_Platform_and_Artificial_Satellites.pdf` | 1, 2, 3, 4 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 3 | K=1, K=3 |
| **Q004** | `2603.25694v1.pdf` | 20 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 1 | K=1 |
| **Q005** | `From_Ethics_Washing_to_Ethics_Bashing_A_Moral_Philosophy_View_on_Tech_Ethics.pdf` | 11, 14, 15 | 1 | 1 | 2 | **1** | 1 | 1 | Yes | Yes | 2 | K=1 |
| **Q006** | `Akiyama_2019_ApJL_875_L1.pdf` | 2, 5, 6, 8, 9 | 1 | 1 | 1 | **1** | 1 | 2 | Yes | Yes | 4 | K=1, K=3 |
| **Q007** | `1807.06209v4.pdf` | 29, 30, 31 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 2 | K=1 |
| **Q008** | `Experiencing_Immersive_Virtual_Nature_for_Well-Being_Restoration_Performance_and_Nature_Connectedness_A_Scoping_Review.pdf` | 4, 5, 8 | 1 | 1 | 1 | **1** | 1 | 3 | Yes | Yes | 2 | K=1 |
| **Q009** | `Exploration_on_Experimental_Economics_and_the_Education_Reform_of_New_Finance_and_Economics.pdf` | 1 | 1 | 1 | 1 | **1** | 1 | 10 | Yes | No | 3 | K=1, K=3 |
| **Q010** | `1294261.1294281.pdf` | 4 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 7 | K=1, K=3, K=5 |
| **Q011** | `PIIS0092867411001279.pdf` | 17, 18 | 1 | 1 | 1 | **1** | 1 | 3 | Yes | Yes | 6 | K=1, K=3, K=5 |
| **Q012** | `Structural_formation_of_the_universe_As_observed_by_X-ray_satellites.pdf` | 5 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 15 | K=1, K=3, K=5, K=10 |
| **Q013** | `PIIS0092867411001279.pdf` | 18 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 1 | K=1 |
| **Q014** | `Dance_Guiding_Art_Innovation_Framework_Based_on_Video_Action_Recognition_Technology.pdf` | 1, 2, 3 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 2 | K=1 |
| **Q015** | `2005.11401v4.pdf` | 3, 4, 7 | 2 | 4 | 1 | **1** | 1 | 1 | Yes | Yes | 5 | K=1, K=3, K=5 |
| **Q016** | `On_the_Response_of_Nanoelectrode_Impedance_Spectroscopy_Measures_to_Plant_Animal_and_Human_Viruses.pdf` | 2, 5, 6, 7 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 1 | K=1 |
| **Q017** | `On_the_Response_of_Nanoelectrode_Impedance_Spectroscopy_Measures_to_Plant_Animal_and_Human_Viruses.pdf` | 5, 7 | 1 | 1 | 1 | **1** | 1 | 2 | Yes | Yes | 1 | K=1 |
| **Q018** | `rsta.1895.0004.pdf` | 17 | 1 | 1 | 1 | **1** | 1 | 1 | Yes | Yes | 3 | K=1, K=3 |

### 2.3 Machine-Generated Aggregate Variant Comparison

*Table generated directly by `scripts/generate_report_tables.py`:*

| Metric | Hybrid (Control) | Dense-Only | BM25-Only | Hybrid + Frozen 30 Rerank |
| :--- | :---: | :---: | :---: | :---: |
| **Known-Source Hit@1** | 0.9444 (18/18) | 0.9444 (18/18) | 0.9444 (18/18) | **1.0000 (18/18)** |
| **Known-Source Hit@3** | 1.0000 (9/9 avail, 9 unavail) | 0.8333 (6/6 avail, 12 unavail) | 1.0000 (16/16 avail, 2 unavail) | **1.0000 (9/9 avail, 9 unavail)** |
| **Known-Source Hit@5** | 1.0000 (5/5 avail, 13 unavail) | 1.0000 (2/2 avail, 16 unavail) | 1.0000 (11/11 avail, 7 unavail) | **1.0000 (5/5 avail, 13 unavail)** |
| **Known-Source Hit@10** | 1.0000 (1/1 avail, 17 unavail) | n/a (0 avail, 18 unavail) | 1.0000 (4/4 avail, 14 unavail) | **1.0000 (1/1 avail, 17 unavail)** |
| **Known-Source MRR** | 0.9722 | 0.9583 | 0.9722 | **1.0000** |
| **Avg Distinct Papers** | 3.78 | 2.33 | 7.06 | 3.78 (evaluated pool) |
| **Mean Timing (Seconds)** | 1.39s | 0.19s | 2.60s | 36.13s (CPU) |

### 2.4 Reconciliation of Past Discrepancies
1. **Hybrid Pool-30 Hit@1 Contradiction:**
   - Previous report claimed 18/18 (100%) for pool-30 Hit@1.
   - **Correct Evidence:** `phase4-hybrid.json` reports **17/18 (0.9444)**. Q015 is at paper rank 2 behind `2002.08909v1.pdf`. The true known-source MRR is **0.9722**.
   - Available cutoff counts: $K=3$ has 9 available (9/9), $K=5$ has 5 available (5/5), $K=10$ has 1 available (1/1).
2. **Average Distinct Papers in Top 30 Chunks:**
   - Previous report claimed 4.39 (hybrid), 2.94 (dense), and 7.67 (BM25).
   - **Correct Evidence:** Hybrid averages **3.78**, Dense-only averages **2.33**, and BM25-only averages **7.06**.
3. **Dense-Only and BM25-Only Cutoff Coverage:**
   - Dense-only $K=3$ coverage is **6/18** (with known source found for 5/6 available queries, 0.8333).
   - BM25-only $K=5$ coverage is **11/18** and $K=10$ coverage is **4/18** (not 14/18 and 6/18).
4. **Q015 Fused Chunk IDs and Page Metadata:**
   - In hybrid candidate trace, the top chunk for `2005.11401v4.pdf` was `ecf4a7334cc085e2_p1_child_6` (fused chunk rank 2, physical page 2).
   - The approved page-3 chunk was `ecf4a7334cc085e2_p2_child_19` (fused chunk rank 4).
5. **Q009 Adaptive Softmax Pruning Nuance:**
   - For Q009, the approved page placed at chunk rank 10. While it survived `PROCESS_K` (10), it was pruned by the gentle 0.90 softmax mass cutoff.
   - As a result, adaptive survival across the 18 queries is **17/18 (0.9444)**, an exact and honest finding.
6. **Reranker Latency:**
   - The 18 latency values in the previous frozen-rerank audit averaged **22.67s** per query on CPU (not 21.8s).
   - In the finalized verified run (`phase4-hybrid-rerank-30-final.json`), scoring all 30 candidate pairs averaged **36.13s** per query.

---

## 3. Q015 Causal Account & Discrepancy Resolution

### 3.1 Historical Reporting Error vs Machine Reality
- **Historical Narrative Discrepancy:** A bullet point in historical summary text claimed that `1294261.1294281.pdf` placed Rank 1 ahead of target paper `2005.11401v4.pdf` for Q015.
- **Machine Evidence Audit:** Local inspection of raw Phase 3 logs (`evaluation_results/phase3-document-pool-30-pilot/per-question.jsonl` line 15 and `phase3-ten-chunk-pilot/per-question.jsonl` line 15) confirmed that Rank 1 was **always `2002.08909v1.pdf` (REALM: Retrieval-Augmented Language Model Pre-Training, Guu et al.)**.
- **Cause:** The mention of `1294261.1294281.pdf` was an isolated transcription typo.

### 3.2 RRF Inversion Mechanism
Target query: *"What parametric and non-parametric components comprise RAG architectures, and what training procedure updates their pre-trained seq2seq and retrieval models?"*

- **Competitor chunk:** `8957308ed2e79c01_p2_child_21` (`2002.08909v1.pdf`, Page 3)
  - Dense rank: #3
  - BM25 rank: #5
  - RRF calculation: $\frac{1}{60 + 3} + \frac{1}{60 + 5} = \frac{1}{63} + \frac{1}{65} \approx 0.015873 + 0.015385 = \mathbf{0.031258}$ $\rightarrow$ **Rank 1**.
- **Gold target top chunk:** `ecf4a7334cc085e2_p1_child_6` (`2005.11401v4.pdf`, Page 2)
  - Dense rank: #12
  - BM25 rank: #3
  - RRF calculation: $\frac{1}{60 + 12} + \frac{1}{60 + 3} = \frac{1}{72} + \frac{1}{63} \approx 0.013889 + 0.015873 = \mathbf{0.029762}$ $\rightarrow$ **Rank 2**.
- **Approved target chunk:** `ecf4a7334cc085e2_p2_child_19` (`2005.11401v4.pdf`, Page 3)
  - Dense rank: #28
  - BM25 rank: #1
  - RRF calculation: $\frac{1}{60 + 28} + \frac{1}{60 + 1} = \frac{1}{88} + \frac{1}{61} \approx 0.011364 + 0.016393 = \mathbf{0.027757}$ $\rightarrow$ **Rank 4**.

Because RRF awards balanced performance across both modalities, REALM (top 5 in both) placed 1st, while RAG placed 2nd and 4th.

### 3.3 Evidence Passage Survival Across Stages
- Approved supporting physical pages for `2005.11401v4.pdf`: **Pages 3, 4, and 7**.
- In the initial hybrid pool, chunk `ecf4a7334cc085e2_p2_child_19` (Page 3) placed at Rank 4.
- When scored by `BAAI/bge-reranker-base`:
  - `ecf4a7334cc085e2_p2_child_19` scored **highest of all 30 candidates**, rising to **Rank 1**.
  - Target paper RAG promoted to Rank 1 paper-level.
  - Approved Page 3 chunk survives into `PROCESS_K` (Rank 1 of 10) and adaptive selection.

---

## 4. Cross-Encoder Reranker Repair & Candidate-Window Audit

### 4.1 Provenance & Assertion Verification
- `phase4_diagnostics.py` was updated to explicitly assert:
  `assert prerank_candidate_ids == reranker_candidate_ids`
- Both the prerank candidate pool and the reranker receive the exact same ordered 30 candidate IDs.
- File `evaluation_results/phase4-hybrid-rerank-30-final.json` records:
  - Code file SHA-256 for `database.py`: `6aa6ee061084ade701f71f4202b394d731721b1630950f5f35ff107251fe0ac1`
  - Code file SHA-256 for `phase4_diagnostics.py`: `ba05f2b89bd0fdca827a016ab68b17ca8e49cf4a1d84713a9b2f6037e2ca00b6`
  - Final runner verified candidate match for all 18 queries (`candidate_ids_match_prerank: true`).

### 4.2 Standalone Audit Reproduction
- Created `scripts/verify_frozen_30_rerank.py` to independently execute the frozen 30-candidate audit and output `evaluation_results/frozen_30_rerank_audit.json`.
- Both runners independently confirm:
  - Post-rerank paper rank: **18/18 (1.000) at Rank 1**.
  - Post-rerank known-source MRR: **1.0000**.
  - First chunk rank: **18/18 at Rank 1**.
  - Survival into `PROCESS_K`: **18/18 (100%)**.
  - Survival into adaptive selection: **17/18 (94.44%)** (Q009 pruned at rank 10).

---

## 5. Observational Initial-Stage Simulation of Production Path

In the user-facing application, `database.py` executes:
```python
fetch_n = n_results * 3 # FETCH_K=30 -> fetch_n=90
```
`search_vault(n_results=30)` retrieves up to 90 merged chunks and filters by distance threshold (0.70), returning 47–90 chunks.
`logic_engine.evaluate_chunks()` scores **all** returned chunks with `BAAI/bge-reranker-base`.

The script `scripts/capture_normal_production_path.py` implements an **observational initial-stage simulation** of retrieval, batched cross-encoder reranking, adaptive selection, and initial `CORRECT` classification. It does **not** execute actual ambiguous resolution, supplemental retrieval, the combined preflight LLM check, query rewrite, final generation, or the complete `logic_engine.run_logic_engine` control flow.

### 5.1 Initial-Stage Simulation Findings (N=18)
- **Returned Chunks per Query:** 47 to 90 chunks (mean: **82.50 chunks**).
- **Reranked Chunks per Query:** 47 to 90 chunks (mean: **82.50 chunks**; all returned chunks are scored by the cross-encoder reranker).
- **Raw (Pre-Rerank) Known-Paper Rank 1:** **17/18 (94.44%)** (Q015 raw rank 2 behind REALM).
- **Post-Rerank Known-Paper Rank 1:** **18/18 (100.0%)** (Reranker promotes Q015 from rank 2 to rank 1).
- **Approved Passage in Initial-Stage Selected Context:** **14/18 (77.78%)**:
  - *Note:* This 14/18 result is an **initial-stage simulation observation**, not a measured final generation-context success rate across the full pipeline.
  - **Q001:** Targets `rsta.1895.0004.pdf` (approved page 17; initial selected page 16).
  - **Q008:** Targets `Experiencing_Immersive_Virtual_Nature_for_Well-Being_Restoration_Performance_and_Nature_Connectedness_A_Scoping_Review.pdf` (approved pages 4, 5, 8; initial selected pages 6, 7).
  - **Q009:** Targets `Exploration_on_Experimental_Economics_and_the_Education_Reform_of_New_Finance_and_Economics.pdf` (approved page 1; initial selection page 2; approved page 1 placed at candidate rank 10 and was pruned by the gentle 0.90 softmax mass cutoff).
  - **Q011:** Targets `PIIS0092867411001279.pdf` (approved pages 17, 18; zero chunks achieved `sigmoid_score >= CORRECT_THRESHOLD` of 0.55; all 9 top-K chunks scored `AMBIGUOUS` in [0.25, 0.55), producing an initial no-`CORRECT` signal).
- **Initial No-CORRECT Signal Count:** **1/18 (5.56%)** (Q011 only; this is an initial signal, not the actual fallback rate after ambiguous resolution).
- **Timing (CPU):** Initial-stage latency averaged **93.84s** per query (retrieval: 3.47s, reranking: 90.37s). This excludes later pipeline stages, supplemental retrieval, and answer generation.
- **Live LLM Generation Status:** Recorded as **`NOT RUN`** in initial simulation.

### 5.2 Critical Contrast: Frozen 30 Diagnostic vs. Production Path
The isolated 30-candidate diagnostic (`phase4-hybrid-rerank-30-final.json` and `frozen_30_rerank_audit.json`) evaluates **exactly 30 pre-ranked chunks** (mean CPU latency 36.13s), whereas the live production path evaluates **47–90 pre-filtered chunks** (mean 82.5 chunks, mean CPU latency ~90.4s). Both achieve 18/18 known paper rank 1 post-rerank, but the production pipeline experiences wider chunk competition during adaptive softmax selection and tri-state grading.

---

## 6. Candidate Question Cards & Human Review Worksheets

### 6.1 Accurate Card Audit Against Local PDFs (Q019–Q026)

All 8 candidate cards are preserved in `docs/evaluation/phase4_new_questions.json`.
- **Approved Dispositions:** Q019–Q024 and Q026 were human approved by the project owner. Q025 was approved after correcting its supporting evidence to the verbatim Figure 2 caption on page 3 of `AMA_AdaptiveMemoryviaMultiAgentCollaboration_compressed.pdf`.
- **Preserved Dispositions & Corrections:**
  - Q019–Q024 and Q026 approved as specified.
  - Q025 verified quote: *"Figure 2: Overview of the AMA framework. The system orchestrates four agents to enable adaptive memory evolution. The Retriever routes inputs to optimal granularities based on intent. The Judge audits content relevance to trigger feedback loops and detects conflicts. The Refresher executes updates or deletions to rectify these inconsistencies. Finally, the Constructor synthesizes the validated context into structured memory entries."*

#### Candidate Q019
- **Indexed Filename:** `1406.2661v1.pdf` (Generative Adversarial Nets, Goodfellow et al.)
- **Physical Page:** 4 (Proposition 1), Page 5 (Theorem 1)
- **Question:** In Generative Adversarial Nets, what is the theoretical optimal discriminator $D_G^*(x)$ for a fixed generator $G$, and at what value of $p_g$ is the global minimum of the virtual training criterion $C(G)$ achieved?
- **Proposed Answer:** For a fixed generator $G$, the optimal discriminator is $D_G^*(x) = \frac{p_{\text{data}}(x)}{p_{\text{data}}(x) + p_g(x)}$. The virtual training criterion $C(G)$ achieves its global minimum if and only if $p_g = p_{\text{data}}$, where $C(G)$ achieves the value $-\log 4$.
- **Exact Quotes:**
  - *Page 4:* "Proposition 1. For G fixed, the optimal discriminator D is D*_G(x) = pdata(x) / (pdata(x) + pg(x))"
  - *Page 5:* "Theorem 1. The global minimum of the virtual training criterion C(G) is achieved if and only if pg = pdata. At that point, C(G) achieves the value -log 4."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q020
- **Indexed Filename:** `1412.6980v9.pdf` (Adam: A Method for Stochastic Optimization, Kingma & Ba)
- **Physical Pages:** 2 (Hyperparameters & Algorithm 1), Page 2–3 (Bias correction derivation)
- **Question:** What default hyperparameter values does the Adam paper recommend for $\alpha$, $\beta_1$, $\beta_2$, and $\epsilon$, and what causes the initialization bias in the first and second moment estimates that requires correction?
- **Proposed Answer:** The authors recommend default settings of $\alpha = 0.001$, $\beta_1 = 0.9$, $\beta_2 = 0.999$, and $\epsilon = 10^{-8}$. Initialization bias is caused by initializing the running average vectors with zeros, which biases estimates toward zero during early timesteps.
- **Exact Quotes:**
  - *Page 2:* "Good default settings for the tested machine learning problems are alpha = 0.001, beta1 = 0.9, beta2 = 0.999 and epsilon = 10^-8."
  - *Page 3:* "which is caused by initializing the running average with zeros. In algorithm 1 we therefore divide by this term to correct the initialization bias."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q021
- **Indexed Filename:** `1512.03385v1.pdf` (Deep Residual Learning for Image Recognition, He et al.)
- **Physical Pages:** 2 (Residual block mapping), Page 3 (Shortcut parameter-free complexity)
- **Question:** How does the deep residual learning framework formulate the building block mapping, and do the identity shortcut connections add extra parameters or computational complexity?
- **Proposed Answer:** Rather than fitting a direct underlying mapping $H(x)$, the stacked nonlinear layers explicitly fit a residual mapping $F(x) := H(x) - x$, recasting the original mapping as $F(x) + x$. The identity shortcut connections introduce neither extra parameters nor computational complexity.
- **Exact Quotes:**
  - *Page 2:* "Formally, denoting the desired underlying mapping as H(x), we let the stacked nonlinear layers fit another mapping of F(x) := H(x)-x. The original mapping is recast into F(x)+x."
  - *Page 3:* "The shortcut connections in Eqn.(1) introduce neither extra parameter nor computation complexity."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q022
- **Indexed Filename:** `2401.15884v3.pdf` (Corrective Retrieval Augmented Generation, Yan et al.)
- **Physical Page:** 5 (Action triggers and knowledge refinement)
- **Question:** In Corrective Retrieval Augmented Generation (CRAG), what three knowledge retrieval actions can be triggered based on the retrieval evaluator's confidence score, and how does the system process retrieved knowledge under each action?
- **Proposed Answer:** CRAG triggers three actions: Correct (confidence > upper threshold), Incorrect (all confidence scores < lower threshold), and Ambiguous (intermediate scores). Under Correct, retrieved documents are refined via decompose-then-recompose knowledge refinement; under Incorrect, retrieved documents are discarded and external web search is executed; under Ambiguous, refined internal knowledge and external web search results are combined.
- **Exact Quotes:**
  - *Page 5:* "If the confidence score is higher than the upper threshold, the retrieved document is identified as Correct... a retrieval is assumed Incorrect when the confidence scores of all retrieved documents are below the lower threshold... both types of processed knowledge in Correct and Incorrect are combined to complement each other."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q023
- **Indexed Filename:** `945445.945450.pdf` (The Google File System, Ghemawat et al.)
- **Physical Page:** 4 (Chunk size and allocation)
- **Question:** In the Google File System (GFS), what is the default chunk size, how are chunk replicas stored on chunkservers, and what lazy mechanism avoids space wastage from internal fragmentation?
- **Proposed Answer:** GFS uses a default chunk size of 64 MB. Each chunk replica is stored as a plain Linux file on a chunkserver and is extended only as needed. Lazy space allocation avoids wasting space due to internal fragmentation.
- **Verified Quote (Page 4, Sec. 2.5):** "We have chosen 64 MB, which is much larger than typical file system block sizes. Each chunk replica is stored as a plain Linux file on a chunkserver and is extended only as needed. Lazy space allocation avoids wasting space due to internal fragmentation..."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q024
- **Indexed Filename:** `2310.11511v1.pdf` (Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection, Asai et al.)
- **Physical Page:** 4 (Table 1: Reflection tokens)
- **Question:** In SELF-RAG, what are the four types of reflection tokens used for self-reflection and what do the Retrieve and IsRel tokens evaluate?
- **Proposed Answer:** SELF-RAG introduces four reflection token groups: Retrieve, IsRel, IsSup, and IsUse. Retrieve decides when to invoke retrieval on demand, and IsRel evaluates whether a retrieved passage provides useful information to solve the input.
- **Verified Excerpt (Page 4, Table 1):** "Table 1: Definitions of reflection tokens... Retrieve: Decides when to retrieve with R... ISREL: d provides useful information to solve x... ISSUP: whether y is supported by d... ISUSE: overall usefulness"
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q025
- **Indexed Filename:** `AMA_AdaptiveMemoryviaMultiAgentCollaboration_compressed.pdf` (Adaptive Memory via Multi-Agent Collaboration)
- **Physical Page:** 3 (Framework architecture)
- **Question:** In the Adaptive Memory via Multi-Agent Collaboration (AMA) framework, what are the four specialized agents that orchestrate memory evolution and what are their respective roles?
- **Proposed Answer:** AMA orchestrates four specialized agents: (1) Retriever routes inputs to optimal granularities based on intent; (2) Judge audits content relevance and detects conflicts; (3) Refresher executes updates or deletions; and (4) Memory Constructor formats verified information into Raw Text, Fact Knowledge, and Episode storage.
- **Verified Quote (Page 3, Fig. 2):** "Figure 2: Overview of the AMA framework. The system orchestrates four agents to enable adaptive memory evolution. The Retriever routes inputs to optimal granularities based on intent. The Judge audits content relevance to trigger feedback loops and detects conflicts. The Refresher executes updates or deletions to rectify these inconsistencies. Finally, the Constructor synthesizes the validated context into structured memory entries."
- **Potential Duplicate:** None in Q001–Q018.

#### Candidate Q026
- **Indexed Filename:** `2603.25600v1.pdf` (Evaluating CGM Mass via Resonant Scattering)
- **Physical Page:** 1 (Abstract and Introduction)
- **Question:** What X-ray emission line does the paper propose using for evaluating circumgalactic medium (CGM) mass via resonant scattering, and at what transition energy?
- **Proposed Answer:** The paper proposes evaluating CGM mass using resonant scattering of the helium-like oxygen (OVII) resonant line at an energy of $E = 574\text{ eV}$.
- **Exact Quote (Page 1):** "We propose a novel method for evaluating the CGM mass using resonant scattering of the helium-like oxygen (OVII) resonant line at E = 574 eV."
- **Potential Duplicate:** None in Q001–Q018.

---

### 6.2 Secondary Relevance Rows (`phase4_relevance.json`)
All 16 candidate rows in `docs/evaluation/phase4_relevance.json` were personally reviewed, signed, and dated by reviewer Qusai on 2026-10-21 and imported:
- 8 decisions `relevant`, 8 decisions `nonrelevant`
- `reviewer: "Qusai"`
- Documented verified reasons and passage snippets (including Q023 Dynamo title repair, Q023 GFS full light-compression text, and Q025 verbatim Figure 2 caption).
- Historical pre-sign-off state (prior to 2026-10-21): rows were initially recorded as `judgment: "unjudged"`, `reviewer: null` and were strictly never treated as negative distractors.

---

### 6.3 Corrective Decision Fixtures (`corrective_decision_fixtures.json`)
4 reference fixtures covering the four triage categories were personally reviewed, signed, and dated by reviewer Qusai on 2026-10-21 and imported:
- `proposal_status: "human_verified"`
- `human_verified: true`, `reviewer: "Qusai (signed 2026-10-21)"`
- Decisions: CORR-001 `relevant`, CORR-002 `partially_relevant`, CORR-003 `irrelevant`, CORR-004 `insufficient_evidence`.
- Page numbers verified against physical PDF pages: CORR-001/002 on Adam page 2; CORR-003 MultiHead attention on physical page 5 of `1706.03762v7.pdf` (formerly mislabeled page 3); CORR-004 exact supplied ImageNet passage on physical page 4 of `1512.03385v1.pdf`.
- CORR-002 working rationale distinguishes the single supplied passage (default hyperparameter values) from other content elsewhere in the Adam PDF (bias-corrected update formulas on page 2, and the Section 3 explanation on page 3 of why zero initialization causes early bias).
- Historical pre-sign-off state: previously proposed as `proposal_status: "unverified_proposal"`, `human_verified: false`.

---

### 6.4 Human Evidence Review Rubric
To support the user's manual evidence verification, the following rubric is provided:
1. **Source & Page Verification:** Verify that the cited passage exists verbatim on the exact physical PDF page (1-based index).
2. **Claim Grounding:** Check each required claim against the passage text. If a claim makes an unsupported inference, require exact text correction or reject the claim.
3. **Relevance Triage:**
   - `relevant`: Passage directly answers the question without need for unstated inferences.
   - `partially_relevant`: Passage provides partial information or parameters but lacks a necessary component of the question.
   - `irrelevant`: Passage is completely off-topic.
   - `insufficient_evidence`: Passage is from the target paper on the right topic, but lacks the specific data requested.
4. **Unanswerable Marking:** If a question asks for information absent from the paper and corpus, mark `answerable: false`.

---

### 6.5 Prespecified Partitions
- **Development Set (N=22 across 19 papers):**
  - Q001–Q018 (15 papers)
  - Q019–Q022 (4 papers: GANs `1406.2661v1.pdf`, Adam `1412.6980v9.pdf`, ResNet `1512.03385v1.pdf`, CRAG `2401.15884v3.pdf`)
- **Disclosed Previously Exposed Pilot Set (N=4 across 4 papers):**
  - Q023–Q026 (GFS `945445.945450.pdf`, SELF-RAG `2310.11511v1.pdf`, AMA `AMA_AdaptiveMemory...`, CGM `2603.25600v1.pdf`)
  - **Disclosure:** These questions previously had their retrieval outcomes inspected; any evaluation run on them is a disclosed pilot, not an untouched holdout.

---

## 7. OpenRouter LLM Provider Migration & Model Freezing

### 7.1 Provider Configuration & Migration
- **Adapter Migration:** Implemented official OpenRouter integration in `providers.py` using the official `openai` SDK client (`OpenAI(api_key=..., base_url="https://openrouter.ai/api/v1")`). Added `openai>=1.50.0` to `requirements.txt`.
- **Target Variable:** Constructed client explicitly using `OPENROUTER_API_KEY` from git-ignored `.env`, preventing accidental fallback to unrelated keys or leaking secrets.
- **Distinguishable Sanitized Error Classification:**
  - `401`: Authentication failure / invalid API key (`AuthenticationError`)
  - `402`: Insufficient account credits (`InsufficientCreditsError`)
  - `403`: Forbidden / model policy error (`ForbiddenError`)
  - `404`: Nonexistent model (`ModelNotFoundError`)
  - `429`: Rate limit / allowance exhaustion (`RateLimitExhaustedError`)
  - Empty or blocked output: Sanitized and categorized as `BlockedOutputError` or `EmptyResponseError`
  - Transient `5xx`: Bounded exponential backoff retries (5s, 10s)
  - No provider failure is ever silently converted into a successful fallback, passed relevance check, or legitimate abstention.
- **Audited Error Handling:** Modified `_combined_relevance_check`, `extract_best_sentence`, `supplemental_search`, and `rewrite_query` in `logic_engine.py` to re-raise `providers.ProviderError` and `EnvironmentError`.
- **Reliable Invocation Trace Mechanism:**
  - Replaced the ineffective global monkey-patching of `database.search_vault` with an explicit `InvocationTrace` callback passed to `run_logic_engine`.
  - Captures actual retrieval searches, candidates, reranker scores, exact final context, exact prompt, model ID, response text, token usage, cost, and latency at the real call site.
  - Verified by regression test `test_invocation_trace_captures_pipeline_searches` in `tests/test_phase4_live_capture.py`.

### 7.2 Model Selection, Cost Estimation & Freezing
- **Selected & Frozen Model:** `meta-llama/llama-3.3-70b-instruct`
- **Model Catalog Specifications (`GET https://openrouter.ai/api/v1/models`):**
  - Context Window: 131,072 tokens
  - Max Output Allowance: 4,096 tokens
  - Pricing: **$0.10 / million prompt tokens**, **$0.32 / million completion tokens**
  - Parameter Support: Native system prompts, temperature, top_p, and frequency/presence penalties.
- **Key Allowance & Spending Limit Verification (`GET https://openrouter.ai/api/v1/key`):**
  - Spending Limit: **$100.00**
  - Current Usage: **~$0.015** (less than 2 cents used across initial batch runs)
  - Limit Remaining: **$99.985**
  - Status: OpenRouter API key active with a $100 spending limit configured; sufficient allowance for evaluation runs without quota blockers (note: a configured key spending limit defines maximum allowed usage, not prepaid credit balance).
- **Batch Cost Estimation:**
  - Based on the live Q001 execution path (19 OpenRouter calls, 4,218 total tokens, $0.00115 cost):
  - Estimated 26-question batch total: **~110,000 tokens** ($\approx$ **$0.025 to $0.035 total cost**).
  - Easily accommodates full development (N=22) and disclosed pilot (N=4) runs.
- **Preflight Smoke Test:**
  - Executed on Q001 end-to-end through `evaluate_single_question`.
  - **Route:** `partial_match` (fallback query rewrite $\rightarrow$ supplemental search $\rightarrow$ partial match generation).
  - **Latency:** ~275s (dominated by local CPU CrossEncoder reranking passes).
  - **Approved Passage in Context:** `True` (`rsta.1895.0004.pdf`, page 17, Chunk 2 `897a1fa691632484_p16_child_95`).
  - **Physical Page Verification:** The paper `rsta.1895.0004.pdf` contains 36 physical pages. Historical claims of pages 43–44 were erroneous. The verified OpenRouter live run establishes that Section 13 on physical page 17 was present in the final generation context.
  - **Generated Cited Answer:** Model-generated answer citing `rsta.1895.0004.pdf`; claim support and factual correctness awaiting human verification.
  - **Calls & Usage:** 19 OpenRouter calls, 4,218 tokens, $0.00115 cost, 0 errors.

---

## 8. Real Pipeline Execution & Provenance Reconciliation

### 8.1 Provenance Audit of Historical Artifacts
- **Historical Groq Attempt:**
  - Failed for all 22 development and 4 pilot questions due to `model_not_found` (`llama-3.3-70b-versatile`).
  - Preserved in `evaluation_results/historical_groq_dev_generation_results.json` and `evaluation_results/historical_groq_held_out_generation_results.json`.
- **Historical Gemini Attempt:**
  - 1 smoke question observed, but the measured batch aborted immediately on Q001 with `429 RESOURCE_EXHAUSTED` (Google AI Studio Free Tier limit of 20 requests/day).
  - Q002–Q026 were never run in that batch.
  - Preserved in `evaluation_results/historical_gemini_quota_dev_generation_results.json`.
- **Flawed 26-Row Worksheet (`docs/evaluation/phase4_generation_worksheet.json`):**
  - A separate script had copied Q001 and populated unrun questions with contexts taken from historical Groq outputs.
  - Archived as a flawed historical artifact to `evaluation_results/historical_flawed_phase4_generation_worksheet.json`.
  - Regenerated solely from genuine OpenRouter executions; unrun questions strictly record status `NOT_RUN` with empty context (`[]`).

### 8.2 Execution Tracking & Metric Disaggregation
Metrics are recomputed directly from raw artifacts with explicit separation of planned, attempted, and executed denominators:

| Run Stage / Partition | Planned (N) | Attempted (N) | Executed (N) | Paper Rank 1 (Raw) | Approved Passage in Context | Provider Errors | Status Breakdown | Human Review Status |
|---|---|---|---|---|---|---|---|---|
| **OpenRouter Development Set** | 22 | 22 | 22 | 21/22 (95.5%) | 15/22 (68.2%) | 0 | 9 Success, 13 Partial | **Signed: 2 ACCEPT, 9 PARTIAL, 11 REJECT** |
| **OpenRouter Disclosed Pilot** | 4 | 4 | 4 | 4/4 (100.0%) | 4/4 (100.0%) | 0 | 3 Success, 1 Partial | **Signed: 4 ACCEPT, 0 PARTIAL, 0 REJECT** |
| **Total OpenRouter Execution** | **26** | **26** | **26** | **25/26 (96.2%)** | **19/26 (73.1%)** | **0** | **12 Success, 14 Partial** | **Signed: 6 ACCEPT, 9 PARTIAL, 11 REJECT** |
| *Historical Gemini Dev Attempt* | 22 | 1 | 0 | 1/1 (100%) | 1/1 (100%) | 1 (429 Quota Exceeded) | 0 Executed | Aborted |
| *Historical Groq Dev Attempt* | 22 | 22 | 0 | 21/22 (95.5%) | 16/22 (72.7%) | 22 (`model_not_found`) | 0 Executed | Historical Failure |
| *Historical Groq Pilot Attempt* | 4 | 4 | 0 | 4/4 (100%) | 4/4 (100%) | 4 (`model_not_found`) | 0 Executed | Historical Failure |

*Note: Disclosed pilot (Q023–Q026) has had retrieval candidates previously inspected; it is reported strictly as an exposed pilot, not an untouched holdout.*
*OpenRouter API Cost Reconciliation: The exact sum of captured `provider_calls[].cost` across the 26 raw generation records is **$0.025214131** (comprising $0.023212879 across 246 development calls and $0.002001252 across 15 pilot calls). The approximate total account usage recorded on the OpenRouter dashboard for the session was **~$0.0266**. Without an itemized, per-request transaction billing export from the provider platform, the difference (~$0.0014) is preserved as an unconfirmed variance (plausible contributing factors include session pre-flight key verification, interactive testing, or platform-side rounding), without asserting an unproven single cause.*

---

## 9. Validation Suite & Integrity Checks

All 6 validation commands passed with **exit code 0**:

1. `python -m pytest`: **93 passed, 3 skipped, 0 failed** in 51.22s across 96 collected test items (including 17 live capture and invocation trace tests, 10 Phase 4 diagnostics tests, and provider resilience tests).
2. `python -m py_compile logic_engine.py providers.py scripts/run_real_pipeline_evaluation.py scripts/summarize_generation_runs.py scripts/package_safe_bundle.py phase4_diagnostics.py`: Clean (0 errors, exit code 0).
3. `npm run lint`: Clean (0 errors, exit code 0).
4. `npx tsc --noEmit`: Clean (0 errors, exit code 0).
5. `npm run build`: Clean (compiled in Next.js Turbopack, static generation 9/9 pages in 1115ms, exit code 0).
6. `git diff --check`: Clean (no trailing whitespace, no merge conflicts, exit code 0).

---

## 10. Safe Review Bundle & Open Human Review Decisions

### 10.1 Safe Review Bundle & Manifest Verification
- **SHA-256 Hash Manifest:** Programmatically verified SHA-256 checksums for all bundled files, establishing file integrity against the supplied manifest (checksum matching verifies byte-level integrity, not author digital signature).
- **Zero Secrets Excluded:** Automated leak checks verify no `.env`, API keys, PDF documents, Chroma vector vaults, or build caches are present in the package.
- **Clean Diff:** Provided as a standalone unified diff patch.

### 10.2 Completed Human Decisions & Final Review Results

#### 1. Completed Human Evidence Decisions (Signed 2026-10-21 by Qusai)
- **16 Secondary-Relevance Decisions (`docs/evaluation/phase4_relevance.json`):** 8 relevant, 8 nonrelevant, personally signed by Qusai on 2026-10-21 and imported. (Historical pre-sign-off state: previously proposed as unjudged).
- **4 Corrective Fixtures (`docs/evaluation/corrective_decision_fixtures.json`):** All 4 triage fixtures (`human_verified: true`, `proposal_status: "human_verified"`) signed by Qusai on 2026-10-21 and imported. Verified on physical pages: CORR-003 MultiHead passage on physical page 5 of `1706.03762v7.pdf` (formerly mislabeled page 3); CORR-004 exact supplied ImageNet passage on physical page 4 of `1512.03385v1.pdf`. CORR-002 working rationale distinguishes the single supplied passage (default hyperparameter values) from other content elsewhere in the Adam PDF. (Historical pre-sign-off state: previously proposed as unverified_proposal).

#### 2. Completed Human Answer Evaluations (Signed 2026-10-21 by Qusai)
All 26 generated answers from the OpenRouter baseline were personally evaluated, graded, and signed by reviewer Qusai on 2026-10-21:
- **Authoritative Signed Form:** [`phase4_human_answer_verdict_form.md`](phase4_human_answer_verdict_form.md) (SHA-256: `172bb3a46973534430aa2c2e909cac76a76d0801c2618dbd22ca80a152ceeb08`).
- **Structured Artifact:** [`docs/evaluation/phase4_human_answer_verdicts.json`](docs/evaluation/phase4_human_answer_verdicts.json) conforming to schema [`phase4_human_answer_verdicts.schema.json`](docs/evaluation/phase4_human_answer_verdicts.schema.json).

#### Partitioned Outcome Summary

| Partition | Total Qs | ACCEPT | PARTIAL | REJECT | Factual Correctness (C / PC / I) | Faithfulness (F / PF / U) | Citation Support (S / PS / U) | Claim Coverage (Cov / Part / Omit) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development (Q001–Q022)** | 22 | **2 (9.1%)** | **9 (40.9%)** | **11 (50.0%)** | 2 / 12 / 8 | 19 / 3 / 0 | 16 / 6 / 0 | 14 / 21 / 39 (N=74 claims) |
| **Disclosed Pilot (Q023–Q026)** | 4 | **4 (100.0%)** | **0 (0.0%)** | **0 (0.0%)** | 4 / 0 / 0 | 4 / 0 / 0 | 4 / 0 / 0 | 9 / 0 / 0 (N=9 claims) |
| *Combined Descriptive Total* | *26* | *6 (23.1%)* | *9 (34.6%)* | *11 (42.3%)* | *6 / 12 / 8* | *23 / 3 / 0* | *20 / 6 / 0* | *23 / 21 / 39 (N=83 claims)* |

*Terminology note: Q023–Q026 are a disclosed, previously exposed pilot (retrieval candidates were inspected prior to generation); the 4/4 ACCEPT must not be construed as an untouched holdout result.*

#### 26-Question Audit Table

##### Development Set (Q001–Q022)
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

##### Disclosed Pilot Set (Q023–Q026)
| QID | Target Paper | Route | Overall Verdict | Factual Correctness | Faithfulness | Citation Support | Checked Pages | Reviewer Rationale Summary |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Q023** | `945445.945450.pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 4 | Covers all three claims (64MB chunk size, plain Linux files, lazy allocation). |
| **Q024** | `2310.11511v1.pdf` | `partial_match` | **ACCEPT** | Correct | Faithful | Supported | p. 4 | Fully covers reflection tokens and evaluator roles despite partial_match route. |
| **Q025** | `AMA...pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 3 | Correctly defines four agents (Retriever, Judge, Refresher, Constructor) and roles. |
| **Q026** | `2603.25600v1.pdf` | `success` | **ACCEPT** | Correct | Faithful | Supported | p. 1 | Fully covers OVII resonant line and transition energy E = 574 eV for CGM mass. |

#### Three Distinct Grounding Levels
1. **Target Filename Citation:** Emitted in 26/26 cases (100%); purely lexical, does not establish physical page or claim-level grounding.
2. **Approved Physical Page Presence:** Gold physical page was present in final generation context for 19/26 cases (73.1%, missing for Q005, Q006, Q008, Q009, Q011, Q020, and Q022).
3. **Human-Verified Answer Acceptance:** 6/26 generated answers received an overall ACCEPT verdict (2/22 Development, 4/4 Disclosed Pilot). This is an answer-level verdict, not a claim-support rate. Required claim coverage across all 83 evaluated claims is: 23 Covered (27.7%), 21 Partial (25.3%), and 39 Omitted (47.0%) [Dev: 14 Covered, 21 Partial, 39 Omitted; Pilot: 9 Covered, 0 Partial, 0 Omitted]. Citation support at the answer level is 20/26 Supported (76.9%) and 6/26 Partially Supported (23.1%).

#### Primary Failure Modes Grounded in Actual Records
- **Failure Mode 1 (Retrieval Gap — Missing Approved Pages):** For Q005, Q006, Q008, Q009, Q011, Q020, and Q022 (7/26 cases), approved pages were absent from final context (e.g., Q008 context contained pages 2 and 3 rather than approved 4, 5, 8; Q009 context contained page 2 instead of approved page 1; Q020 context contained Section 7 / AdaMax on page 9 instead of Algorithm 1 on pages 2–3).
- **Failure Mode 2 (Refusals and Hedging with Present Context):** For questions such as Q001, Q002, Q003, Q013, Q014, and Q017, the model emitted explicit template refusals ("Direct Answer Not Found") even when relevant passages or approved pages were present in the passed context (e.g., in Q001, approved page 17 was present in chunk 2, but the model opened with a refusal). Questions like Q006, Q011, Q015, and Q016 opened with "couldn't find a direct answer", whereas Q010 answered directly regarding customer experience but omitted tail-latency contracts and noted the context lacked a direct quote. We distinguish directly observed text (refusal openings vs. omitted claims) from inferred pipeline causes (prompt hedging, reranker truncation).
- **Failure Mode 3 (AdaMax vs. Adam Parameter Confusion):** In Q020, because passed context contained Section 7 (AdaMax on p. 9), the model cited AdaMax parameters ($\beta_1=0.9, \beta_2=0.999$, but no $\epsilon=10^{-8}$; instead $\gamma, \alpha$), leading to an `Incorrect` factual correctness rating while the bias explanation was supported (`PARTIAL` overall).
- **Failure Mode 4 (Pipeline Route Independence):** Pipeline `success` route does not imply human `ACCEPT`. Q004, Q007, Q010, Q018, Q019, Q020, and Q022 executed on the `success` route but received human `PARTIAL` or `REJECT` due to omitted required claims.

#### Evaluation Limits
1. The 16 selected secondary relevance decisions do not establish corpus-wide retrieval precision or recall.
2. Partition Integrity: Development questions (Q001–Q022) represent an iterative development evaluation partition (not a pristine blind set); Q023–Q026 are a disclosed, previously exposed pilot (retrieval candidates were inspected prior to generation). Neither partition constitutes an untouched holdout benchmark.
3. Completing this evaluation documents baseline performance (Dev ACCEPT rate: 2/22 = 9.1%); it does not imply that the application has achieved production readiness. True untouched evaluation across unexposed papers remains future work.
