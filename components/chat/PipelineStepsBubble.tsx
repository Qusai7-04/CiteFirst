"use client";
import type { PipelineInfo } from "@/types/chat";
import { STATUS_COLORS } from "@/lib/constants";

interface Props { pipeline: PipelineInfo; }

export default function PipelineStepsBubble({ pipeline }: Props) {
  const colors = STATUS_COLORS[pipeline.status as keyof typeof STATUS_COLORS] || STATUS_COLORS.failed;
  return (
    <div style={{ marginLeft: 48, marginBottom: 8, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
      <span style={{
        fontSize: 11, padding: "3px 10px", borderRadius: 999,
        background: "var(--accent-bg)", color: "var(--accent)",
      }}>
        {colors.label}
      </span>
      <span style={{ fontSize: 11, color: "var(--text-faint)" }}>{pipeline.chunksKept} chunks kept</span>
      {pipeline.queryUsed && pipeline.queryUsed !== "original" && (
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
          query: <em style={{ color: "var(--text-secondary)" }}>{pipeline.queryUsed.slice(0, 60)}</em>
        </span>
      )}
    </div>
  );
}
