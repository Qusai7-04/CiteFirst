"use client";
import PipelineVisualizer from "@/components/pipeline/PipelineVisualizer";

export default function PipelinePage() {
  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Pipeline Visualizer</h1>
        <p style={{ color: "var(--text-muted)" }}>Live view of the CRAG pipeline stages for each query.</p>
      </div>
      <PipelineVisualizer />
    </div>
  );
}
