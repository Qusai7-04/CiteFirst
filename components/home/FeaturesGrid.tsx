"use client";
import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { Zap, Shield, Target, RefreshCw, AlertTriangle, Database, BarChart, GitBranch } from "lucide-react";

const features = [
  { icon: Zap, title: "Cross-Encoder Reranking", desc: "MS MARCO cross-encoder reranks 30 chunks to top 10, boosting precision over pure vector similarity.", size: "span 2" },
  { icon: Target, title: "3-Tier Grading", desc: "Correct ≥4.5 / Ambiguous ≥0.5 / Incorrect <0.5", size: "" },
  { icon: Shield, title: "Ambiguous Resolution", desc: "Secondary LLM pass extracts best sentence and runs supplemental search before discarding.", size: "" },
  { icon: RefreshCw, title: "Fallback Query Rewriting", desc: "When no good context exists, query is automatically rewritten and pipeline retries.", size: "" },
  { icon: AlertTriangle, title: "Bendy Mode", desc: "Partial match returns top 2 results with relaxed threshold (1.5).", size: "" },
  { icon: Database, title: "ChromaDB Vector Store", desc: "All docs chunked, embedded with SentenceTransformers, stored in ChromaDB.", size: "" },
  { icon: BarChart, title: "Dual Grader Evaluation", desc: "LLM + Cosine Similarity graders evaluated side-by-side with full confusion matrices.", size: "span 2" },
  { icon: GitBranch, title: "4-Status Pipeline", desc: "success / fallback_success / partial_match / failed — each with color-coded badges.", size: "" },
];

export default function FeaturesGrid() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section ref={ref} style={{ padding: "80px 24px" }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6 }} style={{ textAlign: "center", marginBottom: 56 }}>
        <p style={{ color: "var(--accent)", fontFamily: "monospace", fontSize: 12, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12 }}>Capabilities</p>
        <h2 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 12 }}>Your Actual CRAG Features</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>Not generic AI buzzwords — real features from your <code style={{ color: "var(--accent)" }}>logic_engine.py</code></p>
      </motion.div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, maxWidth: 1100, margin: "0 auto" }}>
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.4, delay: i * 0.06 }}
            style={{ gridColumn: f.size || "span 1", background: "var(--card)", borderRadius: 14, padding: "22px", border: "1px solid var(--card-border)", boxShadow: "var(--card-shadow)" }}
          >
            <div style={{ width: 38, height: 38, borderRadius: 10, background: "var(--accent-bg)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
              <f.icon style={{ width: 18, height: 18, color: "var(--accent)" }} />
            </div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>{f.title}</h3>
            <p style={{ fontSize: "0.825rem", color: "var(--text-muted)", lineHeight: 1.6 }}>{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
