"use client";
import { useEvaluation } from "@/hooks/useEvaluation";

type Metric = { mean: number; count: number };
type Summary = {
  baseline_status: string;
  dataset_sha256: string;
  index_tag: string | null;
  counts: {
    present?: number;
    eligible_retrieval?: number;
    scored?: number;
    failed?: number;
    excluded?: number;
    unavailable_cutoffs?: Record<string, number>;
  };
  metrics: Record<string, Metric>;
  config: { mode: string; limit: number | null; chunk_candidate_limit: number };
};

const statusLabels: Record<string, string> = {
  blocked_no_verified_labels: "Baseline blocked: annotate evidence first",
  retrieval_failed: "Retrieval failed: check the local index and model",
  partial_results: "Partial results: some retrieval queries failed",
  pilot_only: "Pilot retrieval measurement (18-query pilot; non-definitive)",
  not_run_audit_only: "Dataset audit only",
};

export default function AnalyticsDashboard() {
  const { status, result, error, runEvaluation } = useEvaluation();
  const data = result as Summary | null;
  const busy = status === "pending" || status === "running";

  return (
    <div style={{ color: "var(--text-secondary)" }}>
      <button onClick={() => void runEvaluation().catch(() => {})} disabled={busy} style={{
        padding: "12px 24px", background: "var(--accent)", color: "#020617",
        fontWeight: 700, border: 0, borderRadius: 10, cursor: "pointer",
        opacity: busy ? 0.7 : 1,
      }}>
        {busy ? "Checking dataset and retrieval..." : "Run retrieval evaluation"}
      </button>
      <p style={{ marginTop: 16 }}>
        Hybrid document retrieval before CRAG. No LLM grader or API key is used.
        Only human-verified paper evidence is scored.
      </p>
      {error && <p role="alert" style={{ color: "#f87171" }}>{error}</p>}
      {status === "completed" && data && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>
            {statusLabels[data.baseline_status] ?? data.baseline_status}
          </h2>
          <p style={{ marginTop: 8 }}>
            Dataset {data.dataset_sha256?.slice(0, 12)} · {data.counts?.present ?? 0} records ·
            {" "}{data.counts?.eligible_retrieval ?? 0} eligible ·
            {" "}{data.counts?.scored ?? 0} scored ·
            {" "}{data.counts?.failed ?? 0} failed ·
            {" "}{data.counts?.excluded ?? 0} excluded
          </p>
          <p style={{ marginTop: 8 }}>
            Paper ranks are the first distinct sources among the top {data.config?.chunk_candidate_limit ?? 10} returned chunks.
            Fewer than K papers count as missing ranks. Index: {data.index_tag ?? "not recorded"}.
          </p>
          {data.counts?.unavailable_cutoffs && Object.values(data.counts.unavailable_cutoffs).some((v) => v > 0) && (
            <p style={{ marginTop: 8, color: "var(--text-muted)", fontSize: 13 }}>
              Unavailable cutoffs (insufficient distinct papers):{" "}
              {Object.entries(data.counts.unavailable_cutoffs)
                .filter(([, count]) => count > 0)
                .map(([k, count]) => `${k} (${count} queries unavailable)`)
                .join(", ")}
            </p>
          )}
          {Object.keys(data.metrics ?? {}).length > 0 && (
            <table style={{ marginTop: 20, borderSpacing: 12, textAlign: "left" }}>
              <thead><tr><th>Metric</th><th>Macro mean</th><th>Queries</th></tr></thead>
              <tbody>{Object.entries(data.metrics).map(([name, value]) => (
                <tr key={name}><td>{name}</td><td>{(value.mean * 100).toFixed(1)}%</td>
                  <td>{value.count}</td></tr>
              ))}</tbody>
            </table>
          )}
          <p style={{ marginTop: 16 }}>
            Details and annotation gaps are written to the backend evaluation_results folder.
            Answer quality, citations, faithfulness, and abstention need separate human review.
          </p>
        </div>
      )}
    </div>
  );
}
