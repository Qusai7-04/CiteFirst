"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { VaultDocument } from "@/types/api";

export function useVault() {
  const [documents, setDocuments] = useState<VaultDocument[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<{ documents: VaultDocument[] }>("/api/vault/list");
      setDocuments(res.documents || []);
    } catch {
      // Backend not available — use empty list
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => { if (!cancelled) void fetchDocuments(); });
    return () => { cancelled = true; };
  }, [fetchDocuments]);

  const uploadDocument = async (file: File) => {
    await api.upload("/api/vault/upload", file);
    await fetchDocuments();
  };

  const deleteDocument = async (filename: string) => {
    await api.delete(`/api/vault/delete/${encodeURIComponent(filename)}`);
    setDocuments((prev) => prev.filter((d) => d.filename !== filename));
  };

  return { documents, loading, uploadDocument, deleteDocument, refetch: fetchDocuments };
}
