"use client";
import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { Search, Layers, Filter, Award, CheckCircle, MessageCircle } from "lucide-react";

const steps = [
  { icon: Search, title: "Phase 1: Hybrid Retrieval", desc: "Dense embedding + BM25 sparse search with Reciprocal Rank Fusion. Fetches 30 chunks from ChromaDB." },
  { icon: Layers, title: "Phase 2: BGE Reranker", desc: "Academic-grade BGE cross-encoder reranks and scores all chunks with sigmoid scoring." },
  { icon: Filter, title: "Tri-State Grading", desc: "Grade each chunk: Correct (≥0.55), Ambiguous (≥0.25), or Incorrect (<0.25) on sigmoid scale." },
  { icon: Award, title: "Ambiguous Resolution", desc: "Extract best sentence from ambiguous chunks, run supplemental search, rescue or discard." },
  { icon: CheckCircle, title: "Phase 3: Pre-Flight Check", desc: "Combined relevance check ensures the full context set answers the query. Cuts FP without hurting TP." },
  { icon: MessageCircle, title: "Phase 4: Adaptive Fallback", desc: "Rewrite query on failure, bendy mode for partial matches, controlled LLM generation." },
];

export default function PipelineSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section ref={ref} style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 24px" }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6 }} style={{ textAlign: "center", marginBottom: 60 }}>
        <p style={{ color: "var(--accent)", fontFamily: "monospace", fontSize: 12, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12 }}>How It Works</p>
        <h2 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 12 }}>The CRAG Pipeline</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "1.1rem", maxWidth: 520, margin: "0 auto" }}>Four phases of self-correcting retrieval, from hybrid fetch to verified answer.</p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 20, maxWidth: 1100, width: "100%" }}>
        {steps.map((step, i) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, y: 24 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            style={{ position: "relative", background: "var(--card)", borderRadius: 16, padding: "24px", border: "1px solid var(--card-border)", boxShadow: "var(--card-shadow)" }}
          >
            <div style={{ position: "absolute", top: -12, left: -12, width: 28, height: 28, background: "var(--bg)", border: "1px solid var(--border)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "var(--accent)" }}>
              {i + 1}
            </div>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: "linear-gradient(135deg,#14b8a6,#0d9488)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
              <step.icon style={{ width: 24, height: 24, color: "#fff" }} />
            </div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>{step.title}</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.6 }}>{step.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
