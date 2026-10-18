"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { ArrowRight, Sparkles } from "lucide-react";

export default function HeroSection() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = () => {
    if (query.trim()) router.push(`/chat?q=${encodeURIComponent(query)}`);
  };

  return (
    <section style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "0 24px", position: "relative" }}>
      {/* Glow orbs */}
      <div style={{ position: "absolute", top: "25%", left: "20%", width: 400, height: 400, background: "var(--glow-1)", borderRadius: "50%", filter: "blur(80px)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: "25%", right: "20%", width: 300, height: 300, background: "var(--glow-2)", borderRadius: "50%", filter: "blur(80px)", pointerEvents: "none" }} />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ textAlign: "center", maxWidth: 860, zIndex: 1 }}
      >
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "8px 18px", background: "var(--accent-bg)", border: "1px solid var(--accent-border)", borderRadius: 999, color: "var(--accent)", fontSize: 13, marginBottom: 28 }}>
          <Sparkles style={{ width: 14, height: 14 }} />
          Corrective RAG • Hybrid Retrieval • 4-Phase Pipeline
        </div>

        <h1 style={{ fontSize: "clamp(3rem, 8vw, 5.5rem)", fontWeight: 900, lineHeight: 1.1, marginBottom: 24, letterSpacing: "-0.03em" }}>
          <span style={{ color: "var(--text-primary)" }}>CRAG</span>{" "}
          <span style={{ background: "linear-gradient(135deg,#14b8a6,#2dd4bf,#5eead4)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
            Intelligence
          </span>
        </h1>

        <p style={{ fontSize: "1.2rem", color: "var(--text-muted)", marginBottom: 40, maxWidth: 800, margin: "0 auto 40px", lineHeight: 1.7 }}>
          Hybrid Retrieval → BGE Rerank → Tri-State Grade → Combined Check → Generate Answer.<br />
          A self-correcting 4-phase pipeline with pre-flight relevance verification.
        </p>

        <div style={{ display: "flex", maxWidth: 640, margin: "0 auto 40px", gap: 12 }}>
          <input
            type="text" value={query} onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Ask anything about your documents..."
            style={{
              flex: 1, padding: "16px 24px", background: "var(--input-bg)", border: "1px solid var(--input-border)",
              borderRadius: 12, color: "var(--text-primary)", fontSize: 16, outline: "none",
            }}
          />
          <button onClick={handleSearch} style={{
            padding: "16px 28px", background: "var(--accent)", color: "#020617", fontWeight: 700,
            borderRadius: 12, border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 8, fontSize: 16, whiteSpace: "nowrap",
          }}>
            Ask <ArrowRight style={{ width: 20, height: 20 }} />
          </button>
        </div>

        <div style={{ display: "flex", flexWrap: "nowrap", justifyContent: "center", gap: 24, color: "var(--text-faint)", fontSize: 13, whiteSpace: "nowrap" }}>
          {[["30", "chunks fetched"], ["10", "reranked"], ["4-Phase", "pipeline"], ["98%", "accuracy"]].map(([val, label]) => (
            <div key={label} style={{ whiteSpace: "nowrap" }}>
              <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>{val}</span> {label}
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
