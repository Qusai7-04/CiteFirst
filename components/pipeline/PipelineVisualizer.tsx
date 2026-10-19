"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Search, Layers, Filter, Shield, MessageSquare, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { streamQuery, type SSEEvent } from "@/lib/api";
import { STATUS_COLORS } from "@/lib/constants";

const PIPELINE_STAGES = [
  { id: "fetching", label: "Phase 1: Hybrid Retrieval", icon: Search, desc: "Dense + BM25 + RRF fusion from ChromaDB" },
  { id: "reranking", label: "Phase 2: BGE Reranker → Top 10", icon: Layers, desc: "BGE cross-encoder scores and reranks chunks" },
  { id: "grading", label: "Tri-State Grading", icon: Filter, desc: "Correct (≥0.55) / Ambiguous (≥0.25) / Incorrect" },
  { id: "resolving", label: "Phase 3: Pre-Flight Check", icon: Shield, desc: "Combined relevance verification" },
  { id: "generating", label: "Phase 4: Generate Answer", icon: MessageSquare, desc: "Synthesize verified context into cited answer" },
];

type StageStatus = "idle" | "active" | "done" | "skip";

export default function PipelineVisualizer() {
  const [statuses, setStatuses] = useState<Record<string, StageStatus>>({});
  const [running, setRunning] = useState(false);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [pipelineStatus, setPipelineStatus] = useState("");

  const runPipeline = async () => {
    if (!query.trim() || running) return;
    setRunning(true);
    setAnswer("");
    setPipelineStatus("");
    const s: Record<string, StageStatus> = {};
    setStatuses({});

    try {
      const result = await streamQuery(query, (event: SSEEvent) => {
        if (event.step === "done") {
          for (const stage of PIPELINE_STAGES) {
            if (s[stage.id] === "active") s[stage.id] = "done";
          }
          setStatuses({ ...s });
          return;
        }

        const idx = PIPELINE_STAGES.findIndex((st) => st.id === event.step);
        if (idx >= 0) {
          for (const stage of PIPELINE_STAGES) {
            if (s[stage.id] === "active") s[stage.id] = "done";
          }
          s[PIPELINE_STAGES[idx].id] = "active";
          setStatuses({ ...s });
        }
      });

      setAnswer(result.answer);
      setPipelineStatus(result.status);
    } catch {
      setAnswer("⚠️ Backend not reachable. Start the API server first.");
    } finally {
      setRunning(false);
    }
  };

  const statusIcon = (st: StageStatus) => {
    if (st === "done") return <CheckCircle style={{ width: 18, height: 18, color: "#22c55e" }} />;
    if (st === "active") return <Clock style={{ width: 18, height: 18, color: "var(--accent)", animation: "pulse 1s infinite" }} />;
    if (st === "skip") return <AlertCircle style={{ width: 18, height: 18, color: "var(--text-muted)" }} />;
    return <div style={{ width: 18, height: 18, borderRadius: "50%", background: "var(--border)" }} />;
  };

  const statusBadgeColor: Record<string, string> = {
    success: "#22c55e",
    fallback_success: "#eab308",
    partial_match: "#f97316",
    failed: "#ef4444",
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 12, marginBottom: 32, maxWidth: 640 }}>
        <input
          type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runPipeline()}
          placeholder="Enter a query to run through the pipeline..."
          style={{
            flex: 1, padding: "12px 18px", background: "var(--input-bg)", border: "1px solid var(--input-border)",
            borderRadius: 10, color: "var(--text-primary)", fontSize: 14, outline: "none",
          }}
        />
        <button onClick={runPipeline} disabled={running || !query.trim()}
          style={{
            padding: "12px 24px", background: "var(--accent)", color: "#020617", fontWeight: 700,
            borderRadius: 10, border: "none", cursor: "pointer", opacity: running || !query.trim() ? 0.6 : 1,
            transition: "opacity 0.2s",
          }}>
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {PIPELINE_STAGES.map((stage, i) => {
          const st = statuses[stage.id] || "idle";
          return (
            <div key={stage.id} style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
              {/* Left connector */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 40 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: "50%",
                  background: st === "done" ? "rgba(34,197,94,0.15)" : st === "active" ? "var(--accent-bg)" : "var(--card)",
                  border: `2px solid ${st === "done" ? "#22c55e" : st === "active" ? "var(--accent)" : "var(--border)"}`,
                  display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.4s",
                }}>
                  <stage.icon style={{ width: 18, height: 18, color: st === "done" ? "#22c55e" : st === "active" ? "var(--accent)" : "var(--text-faint)" }} />
                </div>
                {i < PIPELINE_STAGES.length - 1 && (
                  <div style={{ width: 2, flex: 1, minHeight: 32, background: st === "done" ? "#22c55e" : "var(--border)", transition: "background 0.4s" }} />
                )}
              </div>
              {/* Card */}
              <AnimatePresence>
                <motion.div
                  initial={{ opacity: 0.6, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  style={{
                    flex: 1, marginLeft: 16, marginBottom: 12, background: "var(--card)",
                    border: `1px solid ${st === "active" ? "var(--accent)" : "var(--card-border)"}`,
                    borderRadius: 12, padding: "14px 18px", display: "flex", justifyContent: "space-between",
                    alignItems: "center", transition: "border-color 0.4s", boxShadow: "var(--card-shadow)",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: 14 }}>{stage.label}</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>{stage.desc}</div>
                  </div>
                  {statusIcon(st)}
                </motion.div>
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Answer section */}
      {answer && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginTop: 24, background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 14, padding: "20px 24px", boxShadow: "var(--card-shadow)" }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Shield style={{ width: 16, height: 16, color: "var(--accent)" }} />
            <span style={{ fontWeight: 700, color: "var(--text-primary)", fontSize: 14 }}>Pipeline Result</span>
            {pipelineStatus && (
              <span style={{
                fontSize: 11, padding: "2px 10px", borderRadius: 999, fontWeight: 600,
                background: `${statusBadgeColor[pipelineStatus] || "var(--text-muted)"}20`,
                color: statusBadgeColor[pipelineStatus] || "var(--text-muted)",
              }}>
                {STATUS_COLORS[pipelineStatus as keyof typeof STATUS_COLORS]?.label || pipelineStatus}
              </span>
            )}
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{answer}</p>
        </motion.div>
      )}
    </div>
  );
}
