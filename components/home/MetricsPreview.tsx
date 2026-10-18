"use client";
import { useRef } from "react";
import { motion, useInView } from "motion/react";

const METRICS = [
  { label: "Precision", value: "65%", color: "var(--accent)" },
  { label: "Recall", value: "81%", color: "#A78BFA" },
  { label: "F1 Score", value: "0.72", color: "#60A5FA" },
  { label: "Accuracy", value: "98%", color: "#EC4899" },
];

export default function MetricsPreview() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section ref={ref} style={{ padding: "60px 24px" }}>
      <h2 style={{ textAlign: "center", fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Pipeline Metrics</h2>
      <p style={{ textAlign: "center", fontSize: "0.95rem", color: "var(--text-muted)", marginBottom: 40 }}>
        Evaluated with LLM grader (llama-3.1-8b-instant) on golden dataset • Two-tier verification.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 16, maxWidth: 900, margin: "0 auto" }}>
        {METRICS.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ delay: i * 0.1 }}
            style={{ background: "var(--card)", borderRadius: 12, padding: "24px 16px", border: "1px solid var(--card-border)", textAlign: "center", boxShadow: "var(--card-shadow)" }}
          >
            <div style={{ fontSize: "2rem", fontWeight: 800, color: m.color }}>{m.value}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 4 }}>{m.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
