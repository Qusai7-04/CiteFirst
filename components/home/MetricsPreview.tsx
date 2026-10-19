"use client";
import Link from "next/link";

export default function MetricsPreview() {
  return (
    <section style={{ padding: "60px 24px", textAlign: "center" }}>
      <h2 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>
        Evaluation status
      </h2>
      <p style={{ color: "var(--text-muted)", maxWidth: 680, margin: "0 auto 24px" }}>
        CiteFirst reports retrieval metrics only for questions with verified source evidence.
        The original generated questions are candidates for review, not a measured benchmark.
      </p>
      <Link href="/analytics" style={{ color: "var(--accent)", fontWeight: 700 }}>
        See dataset readiness and evaluation results
      </Link>
    </section>
  );
}
