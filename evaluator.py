import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from logic_engine import run_logic_engine, VAULT_SCHEMA
from langchain_groq import ChatGroq

# ── Configuration ──────────────────────────────────────────────────────────────
DATASET_FILE = "golden_dataset.json"
TOTAL_DOCS   = 60

# ── Load grader model ──────────────────────────────────────────────────────────
print("Loading grader model...")

llm_grader   = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
GRADER_LABEL = "LLM (llama-3.1-8b-instant)"

print(f"Grader model loaded.  Pipeline vault schema: [{VAULT_SCHEMA}]\n")

if VAULT_SCHEMA == "legacy":
    print("━" * 60)
    print("  NOTE: Running evaluation on a LEGACY vault.")
    print("  For maximum metrics, re-ingest first:")
    print("    rm -rf ./vector_vault && python database.py")
    print("  The pipeline will use lower thresholds automatically.")
    print("━" * 60)
    print()


# ── Grader ─────────────────────────────────────────────────────────────────────

def grade_with_llm(query: str, ground_truth: str, fact: str,
                   strict: bool = False) -> bool:
    """
    strict=True  → Tier-1: does the combined context capture the ground truth?
    strict=False → Tier-2: is this individual chunk relevant to the query?
    """
    if strict:
        task = ("Does the 'Retrieved Context' contain the specific information "
                "found in the 'Ground Truth Info'?")
    else:
        task = ("Does the 'Retrieved Context' contain information relevant and "
                "useful for answering the Query, even if it only covers part of "
                "the answer?")

    prompt = f"""
Query: {query}
Ground Truth Info: {ground_truth}
Retrieved Context: {fact}

Task: {task}
Respond with ONLY 'YES' or 'NO'.
"""
    try:
        response = llm_grader.invoke(prompt).content.strip().upper()
        return "YES" in response
    except Exception as e:
        print(f"  [!] LLM Grader Error: {e}")
        return False


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_metrics(tp, fp, fn, tn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0)
    accuracy  = ((tp + tn) / (tp + tn + fp + fn)
                 if (tp + tn + fp + fn) > 0 else 0)
    return precision, recall, f1, accuracy


# ── Plots ──────────────────────────────────────────────────────────────────────

def plot_for_grader(grader_name, tp, fp, fn, tn,
                    precision, recall, f1, accuracy):
    safe = (grader_name
            .replace(" ", "_").replace("(", "").replace(")", "")
            .replace("—", "").replace("-", "").lower())
    safe = "_".join(safe.split())

    # Confusion matrix
    plt.figure(figsize=(6, 5))
    cm = np.array([[tn, fp], [fn, tp]])
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Negative (Ignored)", "Positive (Kept)"],
        yticklabels=["Negative (Irrelevant)", "Positive (Relevant)"],
    )
    plt.title(f"CRAG — {grader_name}\nConfusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    fname_cm = f"confusion_matrix_{safe}.png"
    plt.savefig(fname_cm, dpi=300)
    plt.close()
    print(f"  └─ Saved {fname_cm}")

    # Metrics bar chart
    plt.figure(figsize=(8, 5))
    metrics_labels = ["Precision", "Recall", "F1 Score", "Accuracy"]
    scores         = [precision, recall, f1, accuracy]
    ax             = sns.barplot(x=metrics_labels, y=scores, palette="viridis")
    plt.ylim(0, 1.15)
    plt.title(f"CRAG — {grader_name}\nPerformance Metrics  [vault: {VAULT_SCHEMA}]")
    plt.ylabel("Score (0.0 to 1.0)")
    for i, v in enumerate(scores):
        ax.text(i, v + 0.02, f"{v:.2f}", ha='center', fontweight='bold')
    plt.tight_layout()
    fname_mc = f"metrics_chart_{safe}.png"
    plt.savefig(fname_mc, dpi=300)
    plt.close()
    print(f"  └─ Saved {fname_mc}")


# ── Core evaluation loop ───────────────────────────────────────────────────────

# ── Core evaluation loop ───────────────────────────────────────────────────────
def evaluate_with_grader(test_cases, grader_fn, grader_name):
    tp, fp, fn, tn = 0, 0, 0, 0
    total = len(test_cases)

    print(f"\n{'━'*70}")
    print(f"  GRADER: {grader_name}  |  Vault: {VAULT_SCHEMA}")
    print(f"{'━'*70}")

    for i, case in enumerate(test_cases):
        query = case["question"]

        # Prefer canonical ground_truth; fallback to first context if missing/empty.
        gt = case.get("ground_truth") or (
            case["contexts"][0] if case.get("contexts") else ""
        )

        if not gt:
            print(f"\n  Test {i+1}/{total}: '{query[:60]}...'")
            print("  └─ Skipped: no ground_truth or contexts available.")
            print("-" * 50)
            continue

        print(f"\n  Test {i+1}/{total}: '{query[:60]}...'")

        pipeline    = run_logic_engine(query)
        final_facts = pipeline["facts"]

        print(f"  Pipeline status: {pipeline['status']}  |  facts: {len(final_facts)}")

        # Empty pipeline → definite miss
        if not final_facts:
            fn += 1
            tn += TOTAL_DOCS - 1
            print("  └─ Empty → FN")
            print("-" * 50)
            continue

        # ── Tier 1: combined check ─────────────────────────────────────────────
        combined_ok = grade_with_llm(
            query, gt, "\n".join(final_facts), strict=True
        )

        if not combined_ok:
            fn += 1
            fp += len(final_facts)
            tn += max(0, (TOTAL_DOCS - 1) - len(final_facts))
            print(f"  └─ Combined check FAILED → FN + {len(final_facts)} FPs")
            print("-" * 50)
            continue

        # ── Tier 2: per-chunk grading ──────────────────────────────────────────
        print("  └─ Combined check PASSED. Grading individually...")
        for j, fact in enumerate(final_facts):
            relevant = grader_fn(query, gt, fact)
            if relevant:
                tp += 1
                print(f"     Fact {j+1} → TP")
            else:
                fp += 1
                print(f"     Fact {j+1} → FP")

        tn += max(0, (TOTAL_DOCS - 1) - len(final_facts))
        print("-" * 50)

    precision, recall, f1, accuracy = compute_metrics(tp, fp, fn, tn)

    print(f"\n  Raw counts → TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"  Precision={precision:.4f}  Recall={recall:.4f}  "
          f"F1={f1:.4f}  Accuracy={accuracy:.4f}")

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall,
        "f1": f1, "accuracy": accuracy,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def run_ml_evaluation():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: {DATASET_FILE} not found!")
        return

    with open(DATASET_FILE, "r") as f:
        all_cases = json.load(f)

    test_cases = all_cases[:10]

    result = evaluate_with_grader(test_cases, grade_with_llm, GRADER_LABEL)

    print("\n" + "━" * 70)
    print(f"  EVALUATION RESULTS — {GRADER_LABEL}  [vault: {VAULT_SCHEMA}]")
    print("━" * 70)
    print(f"  {'Metric':<20} {'Score':>10}")
    print("  " + "-" * 30)
    print(f"  {'Accuracy':<20} {result['accuracy']:>10.4f}")
    print(f"  {'Precision':<20} {result['precision']:>10.4f}")
    print(f"  {'Recall':<20} {result['recall']:>10.4f}")
    print(f"  {'F1 Score':<20} {result['f1']:>10.4f}")
    print("━" * 70)

    if VAULT_SCHEMA == "legacy":
        print()
        print("  To improve these metrics, re-ingest with the new pipeline:")
        print("    rm -rf ./vector_vault && python database.py")

    print("\nGenerating visualizations...")
    plot_for_grader(
        GRADER_LABEL,
        result["tp"], result["fp"], result["fn"], result["tn"],
        result["precision"], result["recall"], result["f1"], result["accuracy"],
    )
    print("\nAll visualizations saved.")

    # Return results keyed by grader label for api.py consumption
    return {GRADER_LABEL: result}


if __name__ == "__main__":
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run_ml_evaluation()