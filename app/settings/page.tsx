"use client";
import SettingsPanel from "@/components/settings/SettingsPanel";

export default function SettingsPage() {
  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Pipeline Settings</h1>
        <p style={{ color: "var(--text-muted)" }}>Configure thresholds and parameters for Fetch, Grading, and Evaluation.</p>
      </div>
      <SettingsPanel />
    </div>
  );
}
