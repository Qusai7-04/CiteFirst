"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2 } from "lucide-react";

/* Questions pulled from the actual golden_dataset.json */
const SUGGESTIONS = [
  "What is the criterion for turbulent flow?",
  "Why does Amazon use the 99.9th percentile in SLAs?",
  "How does phenotypic plasticity affect CSC tumors?",
  "Explain Moon-based platform observation angles vs satellites",
];

export default function LiveDemoSection() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const go = (q: string) => {
    setLoading(true);
    router.push(`/chat?q=${encodeURIComponent(q)}`);
  };

  return (
    <section style={{ padding: "80px 24px", textAlign: "center" }}>
      <p style={{ color: "var(--accent)", fontFamily: "var(--font-mono, monospace)", fontSize: 12, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12 }}>Try It Live</p>
      <h2 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 12 }}>Ask CiteFirst a Question</h2>
      <p style={{ color: "var(--text-muted)", marginBottom: 36, fontSize: "1.05rem" }}>
        Connected to your real pipeline — queries go through Fetch → Rerank → Grade → Generate
      </p>

      <div style={{ display: "flex", maxWidth: 640, margin: "0 auto 24px", gap: 12 }}>
        <input
          type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && query.trim() && go(query)}
          placeholder="Type your question..."
          style={{ flex: 1, padding: "14px 20px", background: "var(--input-bg)", border: "1px solid var(--input-border)", borderRadius: 10, color: "var(--text-primary)", fontSize: 15, outline: "none" }}
        />
        <button
          onClick={() => query.trim() && go(query)} disabled={loading}
          style={{ padding: "14px 24px", background: "var(--accent)", color: "#020617", fontWeight: 700, borderRadius: 10, border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
        >
          {loading ? <Loader2 style={{ width: 18, height: 18 }} /> : <ArrowRight style={{ width: 18, height: 18 }} />}
        </button>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 10 }}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s} onClick={() => go(s)}
            style={{ padding: "8px 16px", background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 999, color: "var(--text-faint)", fontSize: 13, cursor: "pointer", transition: "all 0.2s" }}
          >
            {s}
          </button>
        ))}
      </div>
    </section>
  );
}
