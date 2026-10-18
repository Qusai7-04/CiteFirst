"use client";
import { useState, useCallback } from "react";
import { useVault } from "@/hooks/useVault";
import { Upload, Trash2, FileText, Loader2, HardDrive } from "lucide-react";
import { timeAgo } from "@/lib/utils";

export default function VaultManager() {
  const { documents, loading, uploadDocument, deleteDocument } = useVault();
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file);
      }
    } catch {
      alert("Upload failed. Ensure the backend is running.");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    handleFiles(e.dataTransfer.files);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        style={{
          border: `2px dashed ${dragging ? "var(--accent)" : "var(--border)"}`,
          borderRadius: 16, padding: "48px 24px", textAlign: "center", marginBottom: 32,
          background: dragging ? "var(--accent-bg)" : "var(--bg-surface)", transition: "all 0.25s",
        }}
      >
        <Upload style={{ width: 40, height: 40, color: "var(--border)", margin: "0 auto 12px" }} />
        <p style={{ color: "var(--text-muted)", marginBottom: 12 }}>Drag & drop PDF files here</p>
        <label style={{ cursor: "pointer" }}>
          <input type="file" accept=".pdf" multiple onChange={(e) => handleFiles(e.target.files)} style={{ display: "none" }} />
          <span style={{ padding: "10px 22px", background: "var(--accent)", color: "#020617", fontWeight: 700, borderRadius: 8, fontSize: 14 }}>
            {uploading ? "Uploading..." : "Browse Files"}
          </span>
        </label>
      </div>

      {/* Document list */}
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
          <Loader2 style={{ width: 32, height: 32, color: "var(--accent)", animation: "spin 1s linear infinite" }} />
        </div>
      )}

      {!loading && documents.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-faint)" }}>
          <HardDrive style={{ width: 48, height: 48, margin: "0 auto 12px", color: "var(--border)" }} />
          <p style={{ color: "var(--text-muted)" }}>No documents indexed. Upload files to start.</p>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 16 }}>
        {documents.map((doc) => (
          <div key={doc.id} style={{
            background: "var(--card)", border: "1px solid var(--card-border)", borderRadius: 12,
            padding: 18, display: "flex", justifyContent: "space-between", alignItems: "center",
            boxShadow: "var(--card-shadow)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--accent-bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <FileText style={{ width: 20, height: 20, color: "var(--accent)" }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: 14, wordBreak: "break-all", overflowWrap: "anywhere" }}>{doc.filename}</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{doc.chunks} chunks · {timeAgo(doc.indexedAt)}</div>
              </div>
            </div>
            <button onClick={() => deleteDocument(doc.filename)} style={{
              background: "transparent", border: "none", cursor: "pointer", color: "#ef4444", padding: 6,
            }}>
              <Trash2 style={{ width: 16, height: 16 }} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
