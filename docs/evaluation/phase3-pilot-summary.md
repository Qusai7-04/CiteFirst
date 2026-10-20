# Phase 3 Pilot Evaluation Summary

## 1. Overview and Scope

This document records the empirical results of the Phase 3 evidence-evaluation retrieval pilot for CiteFirst.
The evaluation benchmarks the pre-CRAG hybrid retriever (`database.search_vault`, combining BGE dense embeddings and sparse BM25 with reciprocal rank fusion) against the canonical human-reviewed dataset [`reviewed_dataset.json`](../../reviewed_dataset.json) on a fixed 66-PDF evaluation vault.

> [!IMPORTANT]
> **Pilot Status (Non-Definitive)**: This evaluation represents a bounded pilot across 18 candidate questions. It establishes that the evaluation pipeline, evidence gating, and dual protocols function properly and deterministically. It does **not** constitute a definitive claim of 66-paper retrieval accuracy, nor does it measure generated-answer correctness, citation/page accuracy, faithfulness, or abstention.

---

## 2. Dataset and Corpus Provenance

* **Canonical Reviewed Dataset**: [`reviewed_dataset.json`](../../reviewed_dataset.json)
  * Record count: **18**
  * SHA-256: `395b11567576562e5528c52801f0c8da79f86cbd66fc8e7ec0e1dad8ea847487`
  * Status: 18 eligible retrieval, 0 abstention, 0 excluded.
  * Human verification: 100% human-verified (`human_verified: true`, `reviewer: "Qusai (human review)"`, `review_date: "2026-10-20"`).
* **Original Unmodified Dataset**: [`golden_dataset.json`](../../golden_dataset.json)
  * Preserved unchanged; SHA-256: `5ee6866f05beba02edbe04321543d5a6aa9d30dbfaba0fecc219d9c6328754ab`.
* **Evaluation Index**: `./vector_vault_eval`
  * Ingested from all 66 PDFs in `papers/` (manifest SHA-256: `4035c42aeb626527ef714fd3105fdab3157a095bae64f782d84add65558e2583`).
  * Total chunks: 7,816 child chunks (100 words, 20 overlap), 2,418 parent chunks (350 words, 75 overlap).
  * Embedding model: `BAAI/bge-small-en-v1.5` (384 dimensions).
  * Index tag: `vault-eval-c7816-p2418-sha256-4035c42aeb62`.
* **Corpus Representation**:
  * The 18 questions are sourced from **15 distinct papers** out of 66 (22.7% paper representation).
  * Three papers have 2 questions (11.1% weighting each): `rsta.1895.0004.pdf` (Q001, Q018), `PIIS0092867411001279.pdf` (Q011, Q013), and `On_the_Response_of_Nanoelectrode...pdf` (Q016, Q017).
  * Twelve papers have 1 question each (5.6% weighting each).
  * Question-level averages weight co-sourced papers twice relative to single-question papers.
* **Corpus-Wide Secondary Relevance**:
  * An automated text scan of all 66 PDFs evaluated candidate term matches outside the primary cited sources.
  * Spurious/partial matches were inspected (e.g. Rawls/Habermas in general moral philosophy for Q002, dynamometer diesel testing for Q010, unrelated galaxy cluster papers for Q012, deep-learning choreography for Q014, REALM MIPS for Q015) and confirmed non-answering for the specific multi-part questions.
  * However, because the remaining 51 papers have not undergone exhaustive manual passage-by-passage review against all 18 topics, **secondary relevance completeness remains unverified / unconfirmed**.
  * True unjudged papers are omitted from Precision and NDCG prefixes rather than assumed irrelevant.

---

## 3. Protocol Definitions and Units

The unit of evaluation is the **canonical indexed source filename** (e.g. `rsta.1895.0004.pdf`), not an ephemeral chunk ID.
Chunks are retrieved via `database.search_vault(question, n_results=fetch_n)` in fused RRF score order.
Paper deduplication uses `list(dict.fromkeys(chunk['source']))`, assigning each paper the rank of its first-occurring chunk. Duplicate chunk hits from the same paper consume candidate positions but never duplicate document rank.

### Protocol 1: `within_first_ten_chunks`
* **Candidate Chunks Requested**: 10.
* **Scope**: Measures which distinct papers surface within the top 10 returned chunks.
* **Padding Behavior**: If fewer than $K$ distinct papers appear in the 10-chunk window, missing ranks are treated as non-relevant for that query.
* **Limitation**: This is **not** a document top-10 ranking; in practice, high-scoring chunks often cluster on 1 or 2 papers. Across 18 queries, **0 queries reached 10 distinct papers** in this window (coverage: $K=1: 18$, $K=3: 3$, $K=5: 2$, $K=10: 0$).
* **Hit@K Interpretation**: Hit@K = 1.0 indicates that the known gold paper was retrieved within the first 10 chunks (at rank $\le K$). It does not imply 10 unique documents were ranked.

### Protocol 2: `document_pool_top_k` (Candidate Pool = 30)
* **Candidate Chunks Requested**: 30.
* **Scope**: Evaluates document ranking from a pre-specified candidate pool of 30 chunks.
* **Cutoff Availability**: For any cutoff $K$ where fewer than $K$ distinct papers exist in the 30-chunk pool, the cutoff is marked **unavailable** and omitted from macro-average means.
* **Cutoff Coverage**:
  * $K=1$: 18 queries available (100% coverage, 0 unavailable).
  * $K=3$: 9 queries available (50% coverage, 9 unavailable).
  * $K=5$: 5 queries available (27.8% coverage, 13 unavailable).
  * $K=10$: 1 query available (5.6% coverage, 17 unavailable; only Q012 returned 15 distinct papers).

---

## 4. Empirical Results

### Summary Table

| Metric | Protocol 1 (`within_first_ten_chunks`) | Protocol 2 (`document_pool_top_k`, pool=30) | Notes |
|:---|:---:|:---:|:---|
| **Queries Attempted / Scored / Failed** | 18 / 18 / 0 | 18 / 18 / 0 | Deterministic execution |
| **Mean Reciprocal Rank (MRR)** | **0.9722** ($N=18$) | **0.9722** ($N=18$) | 17 at Rank 1, 1 at Rank 2 |
| **Hit@1 / Recall@1** | **0.9444** ($N=18$) | **0.9444** ($N=18$) | Q015 ranked at #2 |
| **Hit@3** | **1.0000** ($N=18$) | **1.0000** ($N=9$) | Pool-30 omits 9 unavailable cutoffs |
| **Hit@5** | **1.0000** ($N=18$) | **1.0000** ($N=5$) | Pool-30 omits 13 unavailable cutoffs |
| **Hit@10** | **1.0000** ($N=18$) | **1.0000** ($N=1$) | Pool-30 omits 17 unavailable cutoffs ($N=1$ only!) |
| **Precision@1** | **1.0000** ($N=17$) | **1.0000** ($N=17$) | 1 query unjudged at prefix rank 1 |
| **Precision@3** | **0.3333** ($N=11$) | N/A (unjudged omitted) | Protocol 1 pads missing ranks |
| **Precision@5** | **0.2000** ($N=11$) | N/A (unjudged omitted) | Protocol 1 pads missing ranks |
| **Precision@10** | **0.1000** ($N=11$) | N/A (unjudged omitted) | Protocol 1 pads missing ranks |
| **Baseline Status** | `pilot_only` | `pilot_only` | Non-definitive pilot |

### Per-Question Ranks

* **Rank 1 (17/18 questions)**:
  * Q001 (`rsta.1895.0004.pdf`), Q002 (`An_Experimentalist_Approach...pdf`), Q003 (`Comparisons_of_Observational...pdf`), Q004 (`2603.25694v1.pdf`), Q005 (`From_Ethics_Washing...pdf`), Q006 (`Akiyama_2019_ApJL_875_L1.pdf`), Q007 (`1807.06209v4.pdf`), Q008 (`Experiencing_Immersive...pdf`), Q009 (`Exploration_on_Experimental...pdf`), Q010 (`1294261.1294281.pdf`), Q011 (`PIIS0092867411001279.pdf`), Q012 (`Structural_formation...pdf`), Q013 (`PIIS0092867411001279.pdf`), Q014 (`Dance_Guiding_Art...pdf`), Q016 (`On_the_Response_of_Nano...pdf`), Q017 (`On_the_Response_of_Nano...pdf`), Q018 (`rsta.1895.0004.pdf`).
* **Rank 2 (1/18 questions)**:
  * Q015: Dense Passage Retriever (`2005.11401v4.pdf`). Surfaced at Rank 2 behind `1294261.1294281.pdf`.

---

## 5. Deliberately Unmeasured Metrics (Deferred to Phase 4)

The following dimensions are **not** measured by this deterministic retrieval evaluation and require live LLM generation evaluation in Phase 4:
1. **Generated Answer Correctness**: Evaluation of the final LLM response against human reference answers.
2. **Faithfulness**: Fact verification checking whether generated claims are strictly entailed by the context passed to the generator.
3. **Citation & Page Accuracy**: Verification that cited page numbers and paper titles match the exact physical PDF page supporting each statement.
4. **Abstention Readiness**: Evaluation of system behavior on truly unanswerable questions (currently 0 unanswerable queries in the 18-record dataset).

---

## 6. How to Reproduce

From the repository root in PowerShell:

```powershell
# 1. Point to the populated 66-PDF evaluation vault
$env:CITEFIRST_VECTOR_DIR = (Resolve-Path .\vector_vault_eval).Path

# 2. Run schema and evidence audit (no retrieval called)
python evaluator.py --dataset reviewed_dataset.json --audit-only --output-dir evaluation_results/phase3-final-audit

# 3. Run Protocol 1 (within_first_ten_chunks)
python evaluator.py --dataset reviewed_dataset.json --index-tag "vault-eval-c7816-p2418-sha256-4035c42aeb62" --protocol within_first_ten_chunks --output-dir evaluation_results/phase3-ten-chunk-pilot

# 4. Run Protocol 2 (document_pool_top_k, pool 30)
python evaluator.py --dataset reviewed_dataset.json --index-tag "vault-eval-c7816-p2418-sha256-4035c42aeb62" --protocol document_pool_top_k --candidate-pool 30 --output-dir evaluation_results/phase3-document-pool-30-pilot
```
