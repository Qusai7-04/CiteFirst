# Phase 4 — Secondary Relevance Review (16 rows)

**Reviewer:** Qusai  |  **Date:** 2026-10-21
**Source file:** `phase4_relevance.json`  |  **Decisions:** all 16 rows now judged (none left `unjudged`)

## How each row was checked
- The named PDF was text-extracted (every page was digital — no OCR needed) and the listed **physical page** was read directly.
- For every proposed **nonrelevant** row the **entire paper** was searched for topic terms — the title alone was never used as proof of irrelevance.

## Decisions

| # | Query | Paper (file) | Page | Proposed | **Judgment** | Passage matches page? |
|---|-------|--------------|------|----------|--------------|------------------------|
| 1 | Q019 | 1406.2661v1.pdf (GAN) | 4 | relevant | **relevant** | Yes (Proposition 1 verbatim) |
| 2 | Q019 | 1512.03385v1.pdf (ResNet) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |
| 3 | Q020 | 1412.6980v9.pdf (Adam) | 2 | relevant | **relevant** | Yes (default settings verbatim) |
| 4 | Q020 | 1406.2661v1.pdf (GAN) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |
| 5 | Q021 | 1512.03385v1.pdf (ResNet) | 2 | relevant | **relevant** | Yes (F(x):=H(x)-x verbatim) |
| 6 | Q021 | 1412.6980v9.pdf (Adam) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |
| 7 | Q022 | 2401.15884v3.pdf (CRAG) | 5 | relevant | **relevant** | Yes (Action Trigger verbatim) |
| 8 | Q022 | 2005.11401v4.pdf (RAG) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |
| 9 | Q023 | 945445.945450.pdf (GFS) | 4 | relevant | **relevant** | Yes (light compression of §2.5) |
| 10 | Q023 | 1294261.1294281.pdf | 1 | nonrelevant | **nonrelevant** | **NO — passage mislabeled (see flag)** |
| 11 | Q024 | 2310.11511v1.pdf (SELF-RAG) | 4 | relevant | **relevant** | Yes (Table 1 verbatim-ish) |
| 12 | Q024 | 2401.15884v3.pdf (CRAG) | 1 | nonrelevant | **nonrelevant** | Yes (title page) — caveat below |
| 13 | Q025 | AMA_..._compressed.pdf | 3 | relevant | **relevant** | Yes (light paraphrase of Fig. 2) |
| 14 | Q025 | 1406.2661v1.pdf (GAN) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |
| 15 | Q026 | 2603.25600v1.pdf | 1 | relevant | **relevant** | Yes (abstract verbatim) |
| 16 | Q026 | 1807.06209v4.pdf (Planck) | 1 | nonrelevant | **nonrelevant** | Yes (title page) |

Result: the 8 proposed-relevant rows are confirmed relevant; the 8 proposed-nonrelevant rows are confirmed nonrelevant. **Two issues need attention** (below).

## Issues to resolve before these are applied

### 1. Q023 row 10 — passage does not match the file (data-integrity flag)
The proposed passage/title is **"The Tail at Scale"**, but physical page 1 of `1294261.1294281.pdf` is the title page of **"Dynamo: amazon's highly available key-value store"** (DOI 10.1145/1294261.1294281). The string "The Tail at Scale" appears **0 times** anywhere in the PDF, and there is no "64 MB", "lazy space", or "chunk size" content. The file is therefore nonrelevant to the GFS chunk-parameter question, **but the row's passage is mislabeled** — either correct the passage or attach the intended (Dean & Barroso) paper.

### 2. Q024 row 12 — CRAG does touch SELF-RAG (caveat, not a reversal)
`2401.15884v3.pdf` (CRAG) is **nonrelevant to the SELF-RAG reflection-token *definitions*** (it never lists Retrieve/ISREL/ISSUP/ISUSE). However, it does mention Self-RAG and "reflection tokens" in passing (e.g. p7: Self-RAG "tuned the LLaMA2 on the instruction-tuning data containing several sets of reflection tokens"; also pp. 2, 4, 8–10, 15–16 in tables and related work). The judgment stays **nonrelevant** for a token-definition question; revisit if the question is broader.

## Caveat on the questions file
`phase4_new_questions.json` was **not supplied**. The question intent for Q019–Q026 was inferred from each row's proposed passage (Q019 GAN optimal discriminator; Q020 Adam defaults; Q021 ResNet residual mapping; Q022 CRAG confidence actions; Q023 GFS chunk size; Q024 SELF-RAG reflection tokens; Q025 AMA multi-agent memory; Q026 CGM mass via OVII). If the actual questions differ, these judgments should be re-checked.

## Scope
These are **16 judgments only**. The other potentially relevant papers in the corpus remain unjudged, so corpus-wide **Recall@K / Precision@K are not valid** from this file.
