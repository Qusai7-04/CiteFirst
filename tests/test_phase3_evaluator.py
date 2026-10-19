import json

from evaluator import evaluate_dataset, run_ml_evaluation
from test_phase3_dataset import annotated


def test_all_eligible_processed_by_default_and_limit_explicit():
    rows = [annotated(id=f"Q{i:03d}", question=f"Question {i}?")
            for i in range(12)]
    calls = []

    def retrieve(question, n_results):
        calls.append(question)
        assert n_results == 10
        return {"metadatas": [[{"source": "paper.pdf", "page_index": 1,
                                "chunk_id": "child-1"}]]}

    audit, results, summary = evaluate_dataset(rows, "hash", retriever=retrieve)
    assert len(audit) == len(results) == len(calls) == 12
    assert summary["counts"]["scored"] == 12
    assert summary["metrics"]["r@1"]["count"] == 12
    assert results[0]["retrieved_chunks"][0]["page"] == 2
    assert "tn" not in json.dumps(summary).lower()
    calls.clear()
    _, limited, summary = evaluate_dataset(rows, "hash", retriever=retrieve, limit=10)
    assert len(calls) == 10
    assert [r["status"] for r in limited[-2:]] == ["skipped_limit"] * 2
    assert summary["config"]["limit"] == 10


def test_failures_and_exclusions_not_scored():
    def fail(*args, **kwargs):
        raise RuntimeError("retrieval failed")

    rows = [annotated(), {"question": "Candidate only"}]
    _, results, summary = evaluate_dataset(rows, "hash", retriever=fail)
    assert results[0]["status"] == "failed"
    assert results[1]["status"] == "needs_human_review"
    assert summary["counts"]["failed"] == 1
    assert summary["counts"]["excluded"] == 1
    assert summary["metrics"] == {}
    assert summary["baseline_status"] == "retrieval_failed"


def test_baseline_status_distinguishes_no_labels_failure_and_partial():
    _, _, blocked = evaluate_dataset([{"question": "Candidate only"}], "hash")
    assert blocked["baseline_status"] == "blocked_no_verified_labels"
    rows = [annotated(id="Q001", question="One?"),
            annotated(id="Q002", question="Two?")]

    def sometimes_fails(question, n_results):
        if question == "Two?":
            raise RuntimeError("offline vault")
        return {"metadatas": [[{"source": "paper.pdf", "chunk_id": "c1"}]]}

    _, results, partial = evaluate_dataset(rows, "hash", retriever=sometimes_fails)
    assert [row["status"] for row in results] == ["scored", "failed"]
    assert partial["baseline_status"] == "partial_results"
    assert partial["counts"]["scored"] == partial["counts"]["failed"] == 1


def test_chunk_window_is_not_misreported_as_ten_unique_papers():
    rows = [annotated()]

    def repeated_chunks(question, n_results):
        return {"metadatas": [[{"source": "paper.pdf", "chunk_id": f"c{i}"}
                                for i in range(12)]]}

    _, results, summary = evaluate_dataset(rows, "hash", retriever=repeated_chunks)
    assert results[0]["chunk_candidates_returned"] == 10
    assert results[0]["distinct_papers_returned"] == 1
    assert len(results[0]["retrieved_papers"]) == 1
    assert summary["config"]["chunk_candidate_limit"] == 10


def test_scored_cli_requires_fixed_index_tag(tmp_path):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([annotated()]))
    for tag in (None, "unrecorded", " unknown "):
        try:
            run_ml_evaluation(path, tmp_path / "results", index_tag=tag)
        except ValueError as exc:
            assert "--index-tag" in str(exc)
        else:
            raise AssertionError("A scored run accepted an unrecorded index")
    # The checked-in unverified candidates still permit a no-model audit summary.
    path.write_text(json.dumps([{"question": "Draft only"}]))
    summary = run_ml_evaluation(path, tmp_path / "results")
    assert summary["baseline_status"] == "blocked_no_verified_labels"


def test_audit_only_never_imports_or_calls_retrieval(tmp_path):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([annotated()]))
    summary = run_ml_evaluation(path, tmp_path / "results", audit_only=True)
    assert summary["counts"]["attempted"] == 0
    assert summary["baseline_status"] == "not_run_audit_only"
    assert (tmp_path / "results" / "annotation-gaps.csv").exists()
    assert (tmp_path / "results" / "per-question.jsonl").exists()
    assert "dataset_sha256" in json.loads(
        (tmp_path / "results" / "aggregate.json").read_text())
    per_query = json.loads((tmp_path / "results" / "per-question.jsonl").read_text())
    assert per_query["status"] == "skipped_audit_only"
    assert per_query["config_sha256"] == summary["config_sha256"]
    assert summary["counts"]["present"] == 1
    assert summary["config"]["limit"] is None
