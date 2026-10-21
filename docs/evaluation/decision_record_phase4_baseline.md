# Phase 4 Configuration Decision Record: Provisional Retrieval Baseline

**Date:** 2026-10-20  
**Status:** Approved Provisional Baseline (Production Unchanged)  
**Decision Authority:** CiteFirst Engineering / Development Phase 4  

---

## 1. Context and Problem Statement

During Phase 3 evaluation and early Phase 4 diagnostics on the 18 human-approved development queries (Q001–Q018), hybrid retrieval (`search_vault` using dense BAAI/bge-small-en-v1.5 and BM25 with Reciprocal Rank Fusion) achieved:
- Known-positive source Hit@1: 17/18 (0.9444)
- Known-source MRR: 0.9722
- Only Q015 failed to achieve distinct-paper rank 1 (retrieved at paper rank 2 behind `2002.08909v1.pdf`, REALM).

We investigated whether switching candidate retrieval to single-source (`dense-only` or `bm25-only`) or modifying reranking parameters could improve retrieval quality without introducing regressions.

---

## 2. Hypothesized Failure Mechanisms

1. **Dense-only hypothesis:** BM25 lexical matches introduce distracting false-positive chunks into RRF fusion, crowding out dense semantic matches.
2. **BM25-only hypothesis:** Dense embeddings suffer from semantic drift on keyword-heavy or author-specific queries, and exact BM25 lexical matching can resolve Q015.

---

## 3. Experimental Controls and Fixed Parameters

All experiments were conducted against the fixed, audited Phase 3 environment:
- **Vector Vault:** `vector_vault_eval` (7,816 child chunks, 2,418 parent chunks)
- **Vault Tag:** `vault-eval-c7816-p2418-sha256-4035c42aeb62`
- **Reviewed Dataset:** `reviewed_dataset.json` (18 queries, SHA-256 `395b11567576562e5528c52801f0c8da79f86cbd66fc8e7ec0e1dad8ea847487`)
- **Settings SHA-256:** `da7f4b49f6b70b3482753755dbc0cea1984c75ca757bdfb3810fcb9c10f4aeae`
- **Dense Embedding Model:** `BAAI/bge-small-en-v1.5`
- **Cross-Encoder Model:** `BAAI/bge-reranker-base`
- **Distance Threshold:** `0.70`

---

## 4. Evaluated Variants and Empirical Results

Three retrieval variants were evaluated with candidate pool size = 30 chunks on the 18 development questions:

| Metric | Hybrid (Control) | Dense-Only | BM25-Only |
| :--- | :--- | :--- | :--- |
| **Known-Source Hit@1** | **17/18 (0.9444)** | 17/18 (0.9444) | 17/18 (0.9444) |
| **Known-Source Hit@3** | **9/9 (1.000)** (9 unavail) | 5/6 (0.8333) (12 unavail) | 16/16 (1.000) (2 unavail) |
| **Known-Source Hit@5** | **5/5 (1.000)** (13 unavail) | 2/2 (1.000) (16 unavail) | 11/11 (1.000) (7 unavail) |
| **Known-Source Hit@10** | **1/1 (1.000)** (17 unavail) | 0/0 (n/a) (18 unavail) | 4/4 (1.000) (14 unavail) |
| **Known-Source MRR** | **0.9722** | 0.9583 (-0.0139) | 0.9722 (0.0000) |
| **Avg Distinct Papers (Top 30)** | **3.78** | 2.33 (-1.44) | 7.06 (+3.28) |
| **Mean Retrieval Latency** | **3.67s** | 2.03s (-1.64s) | 0.35s (-3.31s) |

### Per-Question Regression Review:
- **Dense-Only:** Regresses Q015 further from rank 2 down to rank 4. Severe source crowding (averages only 2.33 distinct papers in 30 chunks; 12/18 queries have < 3 distinct papers).
- **BM25-Only:** Resolves Q015 to rank 1, but creates a direct regression on Q005 (`1810.04805v2.pdf`, BERT), moving its known source from rank 1 to rank 2.
- **Reranker Impact on Hybrid:** Evaluating the first 30 hybrid candidates with `BAAI/bge-reranker-base` brings Q015 to rank 1, achieving **18/18 (1.000) Hit@1 and MRR 1.000** on distinct papers, with 18/18 surviving `PROCESS_K` and 17/18 surviving adaptive threshold.

---

## 5. Architectural Decision

**Decision:** **Retain Hybrid Retrieval + Cross-Encoder Reranking as the Provisional Baseline.**
**Production Action:** **No change to production configuration.**

### Rationale:
1. Production `logic_engine.py` already includes `evaluate_chunks()` with `BAAI/bge-reranker-base`. Reranking is an existing architecture component, not an unproven Phase 4 addition.
2. Neither dense-only nor BM25-only provides a Pareto improvement over hybrid; both induce known-source rank regressions on the development set.
3. Reranker over hybrid candidates already elevates 18/18 known sources to rank 1.
4. Changing production thresholds or candidate sources at this stage is premature before human review of candidate cards Q019–Q026 and held-out validation.

---

## 6. Guardrails and Scope Boundaries

- **Single Variable Tuning:** Future tuning will evaluate exactly one variable per experiment (e.g. `PROCESS_K` depth or candidate pool size), never multi-parameter grid searches.
- **Cost Limit:** Cross-encoder reranking latency is ~22–36 seconds per query on CPU. Any candidate pool expansion beyond 30 candidates is constrained by latency budget.
- **Index Protection:** The existing vector vault and evaluation index must remain read-only. No reindexing or chunking alterations without an isolated, separate vault.
- **Held-Out Isolation:** The provisional baseline remains strictly provisional on development questions Q001–Q018. Held-out questions will be executed exactly once after human evidence review.
