# Corrective Fixtures Review — CORR-001 … CORR-004

**Reviewer:** Qusai  |  **Date:** 2026-10-21
**Source:** `corrective_decision_fixtures.json` (not attached — see caveat)
**Decision key:** APPROVE = proposed decision correct as-is · REVISE = right direction, label/wording should change · REJECT = wrong

## Summary

| Case | Proposed | **Decision** | Page checked |
|------|----------|--------------|--------------|
| CORR-001 | relevant | **APPROVE** | Adam (1412.6980v9-2) p2 |
| CORR-002 | partially_relevant | **APPROVE** | Adam (1412.6980v9-2) p2 |
| CORR-003 | irrelevant | **APPROVE** | Transformer (1706.03762v7) p3 |
| CORR-004 | insufficient_evidence | **APPROVE** | ResNet (1512.03385v1-2), full-text check |

All four proposed decisions are correct. `human_verified` is **false** on every case.

## Reasoning

**CORR-001 — APPROVE (relevant).** Page 2 of the Adam paper states verbatim: "Good default settings for the tested machine learning problems are α = 0.001, β1 = 0.9, β2 = 0.999 and ϵ = 10−8." All three values the question asks for (β₁, β₂, ε) are on the inspected page, so the passage answers the exact question.

**CORR-002 — APPROVE (partially_relevant).** The same page-2 passage gives the defaults and shows the bias-corrected estimates in Algorithm 1, but it does **not** explain why zero-initializing the moment vectors causes a bias — page 2 only says "Section 3 explains our initialization bias correction technique." Judged strictly on the supplied passage (no outside evidence), it answers the defaults half but not the "why" half, so `partially_relevant` is right.

**CORR-003 — APPROVE (irrelevant).** The supplied Transformer passage (p3) reads: "We employ a residual connection [11] around each of the two sub-layers, followed by layer normalization [1]. That is, the output of each sub-layer is LayerNorm(x + Sublayer(x))…". The question is about the **ResNet** residual mapping (F(x) := H(x) − x with identity shortcuts). The Transformer passage describes its own post-norm residual wrapping and never gives the ResNet formulation, so it does not address the question.

**CORR-004 — APPROVE (insufficient_evidence).** The supplied ResNet passage is on the target topic but has no exact training runtime in seconds. I searched the whole ResNet PDF to test this: it reports FLOPs (3.8 / 11.3 billion) and iteration counts ("terminate training at 64k iterations"), but no "seconds" or other time-unit runtime figure. The passage therefore does not supply the requested figure, and its silence doesn't prove no such figure exists elsewhere — which is exactly what `insufficient_evidence` means.

## Caveat
`corrective_decision_fixtures.json` was **not attached**. The cases were reviewed against the exact question described in the task's "What you should verify" column, with the supplied passages identified from the attached PDFs (Adam p2; Transformer residual-connection passage on p3; ResNet residual-mapping passage). If the fixture questions or passages differ from this reconstruction, re-check before entering them.

## Certification
`human_verified: false` is kept on all four cases. These are AI-recorded review decisions — Gemini may enter the approved judgments and reviewer details, but must not self-certify them as human-verified.
