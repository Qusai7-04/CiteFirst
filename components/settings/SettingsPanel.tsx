"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { Settings } from "@/types/api";
import { DEFAULT_SETTINGS } from "@/lib/constants";
import { Save, RotateCcw, Loader2, CheckCircle } from "lucide-react";

function SliderField({ label, value, min, max, step, unit, onChange }: {
  label: string; value: number; min: number; max: number; step: number; unit?: string; onChange: (v: number) => void;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 14, color: "var(--accent)", fontWeight: 700 }}>{value}{unit || ""}</span>
      </div>
      <div style={{ position: "relative", height: 8, background: "var(--border)", borderRadius: 4 }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${pct}%`, background: "var(--accent)", borderRadius: 4, transition: "width 0.15s" }} />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{ position: "absolute", inset: 0, width: "100%", opacity: 0, cursor: "pointer", height: "100%" }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-faint)", marginTop: 4 }}>
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  );
}

export default function SettingsPanel() {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loadingSettings, setLoadingSettings] = useState(true);

  // Load current settings from API on mount
  useEffect(() => {
    api.get<Settings>("/api/settings")
      .then((data) => setSettings(data))
      .catch(() => {/* Use defaults */})
      .finally(() => setLoadingSettings(false));
  }, []);

  const set = (key: keyof Settings) => (v: number) => setSettings((s) => ({ ...s, [key]: v }));

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/api/settings", settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      alert("Backend not reachable.");
    } finally {
      setSaving(false);
    }
  };

  const sections = [
    {
      title: "Retrieval",
      fields: [
        { key: "FETCH_K" as const, label: "Fetch K (Chunks to retrieve)", min: 5, max: 50, step: 1 },
        { key: "PROCESS_K" as const, label: "Process K (Chunks after reranking)", min: 1, max: 20, step: 1 },
        { key: "CHUNK_WORD_LIMIT" as const, label: "Chunk Word Limit", min: 50, max: 600, step: 10 },
        { key: "DISTANCE_THRESHOLD" as const, label: "Distance Threshold (Pre-filter)", min: 0.1, max: 1.0, step: 0.01 },
      ]
    },
    {
      title: "Grading Thresholds",
      fields: [
        { key: "CORRECT_THRESHOLD" as const, label: "Correct Threshold (sigmoid)", min: 0, max: 1, step: 0.01 },
        { key: "AMBIGUOUS_THRESHOLD" as const, label: "Ambiguous Threshold (sigmoid)", min: 0, max: 1, step: 0.01 },
        { key: "BENDY_THRESHOLD" as const, label: "Bendy Mode Threshold", min: 0, max: 1, step: 0.01 },
      ]
    },
    {
      title: "Pipeline Caps",
      fields: [
        { key: "MAX_VERIFIED_CHUNKS" as const, label: "Max Verified Chunks", min: 1, max: 10, step: 1 },
        { key: "SOFTMAX_MASS_CUTOFF" as const, label: "Softmax Mass Cutoff", min: 0.5, max: 1.0, step: 0.01 },
        { key: "TOTAL_DOCS" as const, label: "Legacy document count (unused by retrieval evaluation)", min: 1, max: 200, step: 1 },
      ]
    },
  ];

  if (loadingSettings) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Loader2 style={{ width: 32, height: 32, color: "var(--accent)", animation: "spin 1s linear infinite" }} />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1000 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 24, marginBottom: 32 }}>
        {sections.map((sec) => (
          <div key={sec.title} style={{ background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 14, padding: 24, boxShadow: "var(--card-shadow)" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 24, paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>{sec.title}</h2>
            {sec.fields.map((f) => (
              <SliderField key={f.key} label={f.label} value={settings[f.key]} min={f.min} max={f.max} step={f.step} onChange={set(f.key)} />
            ))}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <button onClick={save} disabled={saving} style={{
          display: "flex", alignItems: "center", gap: 8, padding: "12px 24px",
          background: saved ? "#22c55e" : "var(--accent)", color: "#020617", fontWeight: 700,
          borderRadius: 10, border: "none", cursor: "pointer", transition: "all 0.2s",
        }}>
          {saving ? <Loader2 style={{ width: 16, height: 16, animation: "spin 1s linear infinite" }} />
            : saved ? <CheckCircle style={{ width: 16, height: 16 }} />
            : <Save style={{ width: 16, height: 16 }} />}
          {saved ? "Saved!" : saving ? "Saving..." : "Save Settings"}
        </button>
        <button onClick={() => setSettings(DEFAULT_SETTINGS)} style={{
          display: "flex", alignItems: "center", gap: 8, padding: "12px 20px",
          background: "transparent", color: "var(--text-muted)", border: "1px solid var(--border)",
          borderRadius: 10, cursor: "pointer", transition: "all 0.2s",
        }}>
          <RotateCcw style={{ width: 16, height: 16 }} /> Reset Defaults
        </button>
      </div>
    </div>
  );
}
