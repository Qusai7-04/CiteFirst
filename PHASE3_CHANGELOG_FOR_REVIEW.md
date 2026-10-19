# CiteFirst Phase 3 review handoff

Base: GitHub main merge commit 63b7be0a02cbc4cccce8c86d3c6ddf2ac92ee301. The revised patch was built in a backend-complete local snapshot reconstructed from this commit. No remote file, branch, commit, or PR was changed. Inspect the patch and confirm the base before applying.

## Revised review fixes

- Default judgment coverage now includes only verified relevant papers; unjudged hits do not silently lower P@K or NDCG@K. Tests distinguish judged negatives and unjudged results.
- Evaluation status separates missing labels, complete retrieval failure, partial retrieval failure, audit-only mode, and pilot results. The analytics page explains these states.
- The original generated dataset is still 18 records. The first handoff's SHA-256 `2970c87b...` was incorrect for the base commit; the verified byte hash is `5ee6866f05beba02edbe04321543d5a6aa9d30dbfaba0fecc219d9c6328754ab`. Git history shows only the initial 18-record version, so the reported 20 remains unexplained.
- A scored CLI run now requires a non-placeholder `--index-tag`. Its manually supplied tag is an identifier, not proof of identical vector contents.
- `answerable` and `question_type` must agree. The home page no longer advertises historical precision, recall, F1, or accuracy as current results.
- The evaluator explicitly scores first-occurrence paper ranks within its top-ten **chunk** window. It records chunk and distinct-paper counts and does not present P@10 as retrieval of ten unique papers.

## Changed files

| Path | Reason |
|---|---|
| docs/evaluation/phase3-audit.md | Evidence-backed Stage 3A inventory, call graph, 10/18 cause, metric defects and readiness. |
| docs/evaluation/phase3-annotation-gaps.csv | One row per current candidate with explicit missing labels and human review status. |
| docs/evaluation/methodology.md | Metric units, denominators, judgment limits, commands and provider boundaries. |
| docs/evaluation/annotation-template.md | Illustrative, non-gold annotation fields and human workflow. |
| evaluation/__init__.py, evaluation/dataset.py | Backwards-compatible candidate audit, validation and dataset hash. |
| evaluation/metrics.py | Deterministic document metrics at K=1,3,5,10, with unjudged result handling. |
| evaluator.py | Remove old Groq-only grader, hidden first-ten slice, fabricated TN/accuracy/charts; add all-eligible retrieval CLI and reports. |
| api.py | Return real evaluator summary; remove fabricated fallback metrics. |
| components/analytics/AnalyticsDashboard.tsx, app/analytics/page.tsx, types/api.ts | Display readiness/counts and only available scores, with no misleading confusion matrix. |
| components/home/MetricsPreview.tsx | Replace unverified historical metrics on the home page with an evaluation-readiness link. |
| tests/test_phase3_metrics.py, tests/test_phase3_dataset.py, tests/test_phase3_evaluator.py | Synthetic edge cases, validation and no-hidden-limit regressions. |
| tests/test_eval_retention.py | Align API test with summary contract and prevent mock metric leakage. |
| .gitignore | Ignore generated evaluation_results/. |
| README.md | Correct evaluation commands, readiness and analytics description. |

No golden_dataset.json, retrieval algorithm, threshold, provider default, model, PDF, or vector data was changed. The old static chart-serving route remains for backwards compatibility, but the new evaluator does not generate or display those historical charts.

## Observed checks in the revised backend snapshot

- python -m pip install -r requirements-test.txt: completed in the scratch runtime.
- python -m pytest -q tests: 61 passed, 1 third-party Starlette/httpx deprecation warning.
- python -m compileall -q evaluator.py evaluation api.py tests/test_phase3_metrics.py tests/test_phase3_dataset.py tests/test_phase3_evaluator.py: passed.
- python evaluator.py --audit-only --output-dir evaluation_results: 18 present, 18 structurally valid candidates, 0 eligible, 18 excluded, 0 attempted/scored, status not_run_audit_only.
- python evaluator.py --output-dir evaluation_results: 18 present, 0 eligible/scored, status blocked_no_verified_labels. No local vault or LLM used.
- Full TypeScript typecheck and production build were unavailable in this reconstructed backend snapshot because complete frontend dependencies were not installed. Run npm checks in Gemini's complete checkout.

The backend suite passed with the declared test dependencies available. Full npm lint/typecheck/build could not be run against this reconstructed snapshot (the complete frontend source, lockfile, and dependencies are not present here). No live retrieval, Groq, or Ollama test ran: source PDFs and a local Chroma vault were unavailable. No actual retrieval, answer, citation, faithfulness, or abstention quality score exists.

## Review and application

1. Verify actual main still points at the base (or reconcile a later change), inspect PHASE3_REVIEW.patch and the changed files, then apply to a working branch in the complete repo.
2. Run python -m pip install -r requirements-test.txt; python -m pytest -q tests; python -m compileall -q api.py database.py logic_engine.py providers.py settings_config.py evaluator.py evaluation.
3. Run npm ci --no-audit --no-fund; npm run lint; npx tsc --noEmit; npm run build in the complete frontend checkout.
4. Run python evaluator.py --audit-only; review all 18 gap rows. With a separately reviewed annotated dataset and a fixed local vault, run python evaluator.py --dataset reviewed_dataset.json --index-tag <fixed-index-id>. An explicit smoke cap is --limit 10.
5. Review original PDFs and record permanent IDs, exact indexed filenames, one-based PDF pages, supporting quotes, approved answers, answerability, question type, split, and human verification. Label irrelevant retrieved papers before reporting precision/NDCG. Keep generated candidate answers separate from gold.

Risks: the API evaluation response shape changes; consumers outside the included analytics UI may require adaptation. A human_verified flag cannot prove the PDF quote is correct; a reviewer must inspect the PDFs. Recall is conditional on complete relevant-paper annotation. The evaluator measures hybrid search before CRAG and must not be described as full-pipeline quality. A ranked fused score is unavailable, so score fields are null. Rollback: reverse the patch against the reviewed base, retaining any separate human annotations and local index untouched. Do not delete or rebuild the vault as part of rollback.
