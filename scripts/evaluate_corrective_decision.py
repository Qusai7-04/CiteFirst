"""
Corrective Decision Evaluation Harness.
Evaluates the corrective decision fixtures against logic_engine reranking and
evaluate_chunks() without changing production thresholds. Reports decision accuracy against
unverified proposals, confusion counts, inappropriate retries, and latency.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

INDEX_DIR = ROOT / "vector_vault_eval"
os.environ["CITEFIRST_VECTOR_DIR"] = str(INDEX_DIR.resolve())

from logic_engine import (
    evaluate_chunks, _get_reranker, _sigmoid, _trim,
    CORRECT_THRESHOLD, AMBIGUOUS_THRESHOLD
)

FIXTURES_PATH = ROOT / "docs/evaluation/corrective_decision_fixtures.json"

CATEGORY_TO_TRISTATE = {
    "relevant": "CORRECT",
    "partially_relevant": "AMBIGUOUS",
    "irrelevant": "INCORRECT",
    "insufficient_evidence": "INCORRECT"
}

def evaluate_fixtures():
    if not FIXTURES_PATH.exists():
        print(f"Error: {FIXTURES_PATH} does not exist")
        sys.exit(1)

    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    fixtures = data if isinstance(data, list) else data.get("fixtures", [])

    print(f"Evaluating {len(fixtures)} corrective decision fixtures...")
    print(f"Thresholds: CORRECT >= {CORRECT_THRESHOLD}, AMBIGUOUS >= {AMBIGUOUS_THRESHOLD}")
    print("Label Status: All fixture labels are strictly UNVERIFIED PROPOSALS pending human review.\n")

    results = []
    confusion = {
        "CORRECT": {"CORRECT": 0, "AMBIGUOUS": 0, "INCORRECT": 0},
        "AMBIGUOUS": {"CORRECT": 0, "AMBIGUOUS": 0, "INCORRECT": 0},
        "INCORRECT": {"CORRECT": 0, "AMBIGUOUS": 0, "INCORRECT": 0},
    }

    total_latency = 0.0

    for fix in fixtures:
        fid = fix["id"]
        q = fix["query"]
        passages = fix.get("passages", [])
        passage_text = passages[0]["text"] if passages else ""
        source_fn = passages[0].get("source_filename", "test.pdf") if passages else "test.pdf"
        page_idx = passages[0].get("page", 1) - 1 if passages and passages[0].get("page") else 0
        raw_gold = fix["gold_decision"]
        expected_tristate = CATEGORY_TO_TRISTATE.get(raw_gold, "INCORRECT")

        mock_chunks = [passage_text]
        mock_metas = [{"source": source_fn, "page_index": page_idx, "chunk_id": f"c_{fid}"}]

        t0 = time.perf_counter()

        # 1. Direct reranker score & grading
        raw_logit = float(_get_reranker().predict([q, _trim(passage_text)]))
        score = _sigmoid(raw_logit)
        if score >= CORRECT_THRESHOLD:
            actual_grade = "CORRECT"
        elif score >= AMBIGUOUS_THRESHOLD:
            actual_grade = "AMBIGUOUS"
        else:
            actual_grade = "INCORRECT"

        lat = time.perf_counter() - t0
        total_latency += lat

        confusion[expected_tristate][actual_grade] += 1
        is_match = (expected_tristate == actual_grade)

        results.append({
            "fixture_id": fid,
            "query": q,
            "gold_category": raw_gold,
            "expected_tristate": expected_tristate,
            "actual_grade": actual_grade,
            "sigmoid_score": round(score, 4),
            "latency_seconds": round(lat, 4),
            "match": is_match,
            "suppressed_evidence": (expected_tristate == "CORRECT" and actual_grade != "CORRECT"),
            "inappropriate_retry": (expected_tristate == "CORRECT" and actual_grade == "AMBIGUOUS")
        })

        print(f"[{fid}] Expected={expected_tristate:<10} Actual={actual_grade:<10} Score={score:.4f} Latency={lat:.4f}s {'[MATCH]' if is_match else '[DIFF]'}")

    print("\nConfusion Matrix (Rows=Proposed Expected, Columns=Actual System):")
    header = f"{'':<12} {'CORRECT':<10} {'AMBIGUOUS':<10} {'INCORRECT':<10}"
    print(header)
    for row_label in ["CORRECT", "AMBIGUOUS", "INCORRECT"]:
        row = confusion[row_label]
        print(f"{row_label:<12} {row['CORRECT']:<10} {row['AMBIGUOUS']:<10} {row['INCORRECT']:<10}")

    mean_lat = total_latency / len(fixtures) if fixtures else 0
    print(f"\nMean Latency: {mean_lat:.4f}s across {len(fixtures)} fixtures")

    out_path = ROOT / "evaluation_results/corrective_decision_run.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_data = {
        "status": "completed",
        "label_status": "unverified_proposal",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mean_latency_seconds": round(mean_lat, 4),
        "confusion_matrix": confusion,
        "results": results
    }
    out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
    print(f"Saved evaluation results to {out_path}")

if __name__ == "__main__":
    evaluate_fixtures()
