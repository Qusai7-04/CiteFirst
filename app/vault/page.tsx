"use client";
import VaultManager from "@/components/vault/VaultManager";

export default function VaultPage() {
  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>Document Vault</h1>
        <p style={{ color: "var(--text-muted)" }}>Upload, index, and manage documents for your RAG pipeline.</p>
      </div>
      <VaultManager />
    </div>
  );
}
