"use client";
import type { Source } from "@/types/chat";
import { getApiUrl } from "@/lib/api";

interface Props { source: Source; }

const gradeStyles: Record<string, { bg: string; color: string }> = {
  correct:   { bg: "rgba(34,197,94,0.12)", color: "#4ade80" },
  ambiguous: { bg: "rgba(234,179,8,0.12)", color: "#facc15" },
  incorrect: { bg: "rgba(239,68,68,0.12)", color: "#f87171" },
};

export default function SourceCard({ source }: Props) {
  const gs = source.evidenceStatus === "partial" ? gradeStyles.ambiguous : gradeStyles.correct;
  const label = source.evidenceStatus === "partial" ? "Partial evidence" :
    source.evidenceStatus === "evidence" ? "Evidence" : "Source";
  const page = source.pageNumber;
  const href = getApiUrl(`/api/vault/document/${encodeURIComponent(source.filename)}` +
    (page != null ? `#page=${page}` : ""));
  return (
    <div style={{
      background: "var(--bg-surface)", border: "1px solid var(--card-border)",
      borderRadius: 10, padding: "10px 14px", maxWidth: 260, fontSize: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ color: "var(--text-muted)", fontSize: 11, wordBreak: "break-all", overflowWrap: "anywhere", marginRight: "10px" }}>
          {source.filename}{page != null ? ` · PDF page ${page}` : " · page unavailable"}
        </span>
        <a href={href} target="_blank" rel="noopener noreferrer" aria-label={`Open ${source.filename}${page != null ? ` at PDF page ${page}` : ""}`} style={{
          background: gs.bg, color: gs.color,
          padding: "2px 8px", borderRadius: 999, fontWeight: 600, fontSize: 10, alignSelf: "flex-start",
          textDecoration: "none"
        }}>
          {label}
        </a>
      </div>
      <div style={{ color: "var(--text-faint)", lineHeight: 1.5, fontSize: 11 }}>
        {source.text.slice(0, 100)}…
      </div>
      <a href={href} target="_blank" rel="noopener noreferrer"
        style={{ display: "inline-block", marginTop: 8, color: "var(--accent)" }}>
        Open source PDF{page != null ? ` at page ${page}` : ""}
      </a>
      {source.score > 0 && (
        <div style={{ color: "var(--text-faint)", marginTop: 4, fontSize: 10 }}>
          score: {source.score.toFixed(3)}
        </div>
      )}
    </div>
  );
}
