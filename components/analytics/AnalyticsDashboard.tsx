"use client";
import { useState } from "react";
import { useEvaluation } from "@/hooks/useEvaluation";
import { Loader2, Play, CheckCircle } from "lucide-react";

function MetricGauge({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 12, padding: "20px", textAlign: "center", boxShadow: "var(--card-shadow)" }}>
      <div style={{ fontSize: "2.2rem", fontWeight: 800, color: "var(--accent)" }}>{(value * 100).toFixed(1)}%</div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function ConfusionMatrix({ matrix, label }: { matrix: { tp: number; fp: number; fn: number; tn: number }; label: string }) {
  const cells = [
    { l: "TP", v: matrix.tp, c: "#22c55e" }, { l: "FP", v: matrix.fp, c: "#ef4444" },
    { l: "FN", v: matrix.fn, c: "#f97316" }, { l: "TN", v: matrix.tn, c: "#3b82f6" },
  ];
  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 12, padding: "20px", boxShadow: "var(--card-shadow)" }}>
      <h3 style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>{label} Confusion Matrix</h3>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {cells.map((c) => (
          <div key={c.l} style={{ background: "var(--bg-surface)", borderRadius: 8, padding: 12, textAlign: "center" }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: c.c }}>{c.v}</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{c.l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const { status, result, error, runEvaluation } = useEvaluation();
  const [localError, setLocalError] = useState("");

  const run = async () => {
    setLocalError("");
    try {
      await runEvaluation();
    } catch (e: unknown) {
      setLocalError("Backend not reachable. Start the API server first.");
      console.error(e);
    }
  };

  const isLoading = status === "pending" || status === "running";
  const data = result as Record<string, unknown> | null;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button onClick={run} disabled={isLoading} style={{
          display: "flex", alignItems: "center", gap: 8, padding: "12px 24px",
          background: status === "completed" ? "#22c55e" : "var(--accent)",
          color: "#020617", fontWeight: 700, borderRadius: 10, border: "none", cursor: "pointer",
          opacity: isLoading ? 0.7 : 1, transition: "all 0.2s",
        }}>
          {isLoading ? <Loader2 style={{ width: 18, height: 18, animation: "spin 1s linear infinite" }} />
            : status === "completed" ? <CheckCircle style={{ width: 18, height: 18 }} />
            : <Play style={{ width: 18, height: 18 }} />}
          {isLoading ? "Running Evaluation..." : status === "completed" ? "Evaluation Complete" : "Run Evaluation"}
        </button>

        {isLoading && (
          <div style={{ fontSize: 13, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "pulse 1s infinite" }} />
            Processing golden dataset with LLM grader (llama-3.1-8b-instant)...
          </div>
        )}
      </div>

      {(error || localError) && (
        <div style={{ padding: "12px 16px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, color: "#f87171", marginBottom: 24, fontSize: 14 }}>
          {error || localError}
        </div>
      )}

      {status === "idle" && (
        <div style={{ textAlign: "center", padding: "80px 0", color: "var(--text-faint)" }}>
          <div style={{ fontSize: "3rem", marginBottom: 12 }}>📊</div>
          <p style={{ fontSize: "1.1rem", color: "var(--text-muted)" }}>Click &quot;Run Evaluation&quot; to generate metrics from your golden dataset.</p>
          <p style={{ fontSize: "0.85rem", color: "var(--text-faint)", marginTop: 8 }}>Uses LLM grader (llama-3.1-8b-instant) with two-tier evaluation.</p>
        </div>
      )}

      {status === "completed" && data && (
        <>
          {/* Top-level metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16, marginBottom: 32 }}>
            <MetricGauge label="Precision" value={(data.precision as number) || 0} />
            <MetricGauge label="Recall" value={(data.recall as number) || 0} />
            <MetricGauge label="F1 Score" value={(data.f1 as number) || 0} />
            <MetricGauge label="Accuracy" value={(data.accuracy as number) || 0} />
          </div>

          {/* Confusion matrix and chart images */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 32 }}>
            {data.llm_confusion ? (
              <ConfusionMatrix matrix={data.llm_confusion as { tp: number; fp: number; fn: number; tn: number }} label="LLM Grader" />
            ) : null}

            {/* Pipeline info card */}
            <div style={{ background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 12, padding: "20px", boxShadow: "var(--card-shadow)" }}>
              <h3 style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>Pipeline Configuration</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {[
                  { l: "Grader", v: "BGE Reranker" },
                  { l: "LLM", v: "llama-3.3-70b" },
                  { l: "Embedding", v: "BGE-Small" },
                  { l: "Vault Schema", v: "New (Child/Parent)" },
                  { l: "Retrieval", v: "Hybrid (Dense+BM25)" },
                  { l: "Max Chunks", v: "2" },
                ].map((item) => (
                  <div key={item.l} style={{ background: "var(--bg-surface)", borderRadius: 8, padding: "8px 12px" }}>
                    <div style={{ fontSize: 10, color: "var(--text-faint)", textTransform: "uppercase" }}>{item.l}</div>
                    <div style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 600, marginTop: 2 }}>{item.v}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Real Chart Images from Backend */}
            <div style={{ background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 12, padding: "20px", boxShadow: "var(--card-shadow)", gridColumn: "1 / -1" }}>
              <h3 style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>Generated Evaluation Charts</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <img 
                  src="http://localhost:8000/static/metrics_chart_llm_llama3.18binstant.png" 
                  alt="LLM Metrics Chart" 
                  style={{ width: "100%", height: "auto", borderRadius: 8, border: "1px solid var(--card-border)" }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
                <img 
                  src="http://localhost:8000/static/confusion_matrix_llm_llama3.18binstant.png" 
                  alt="LLM Confusion Matrix" 
                  style={{ width: "100%", height: "auto", borderRadius: 8, border: "1px solid var(--card-border)" }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
            </div>
          </div>

          {/* Completed message if evaluation ran with real backend */}
          {data.message && (
            <div style={{ padding: "12px 16px", background: "var(--accent-bg)", border: "1px solid var(--accent-border)", borderRadius: 10, color: "var(--accent)", fontSize: 14, marginBottom: 24 }}>
              ✅ {data.message as string}
            </div>
          )}
        </>
      )}
    </div>
  );
}
