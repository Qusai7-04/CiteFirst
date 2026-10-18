"use client";
import AnalyticsDashboard from "@/components/analytics/AnalyticsDashboard";

export default function AnalyticsPage() {
  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Analytics Dashboard</h1>
        <p style={{ color: "var(--text-muted)" }}>Evaluation metrics, confusion matrices, and grader comparison.</p>
      </div>
      <AnalyticsDashboard />
    </div>
  );
}
