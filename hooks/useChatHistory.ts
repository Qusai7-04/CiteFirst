"use client";
import { useState, useEffect } from "react";
import type { Message } from "@/types/chat";

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  documentFilter?: string;
  createdAt: number;
}

export const STORAGE_KEY = "citefirst_chat_sessions";
export const LEGACY_STORAGE_KEY = "crag_chat_sessions";

export function parseSessions(raw: string): ChatSession[] {
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((s: ChatSession) => ({
      ...s,
      messages: (s.messages || []).map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      })),
    }));
  } catch {
    return [];
  }
}

export function loadStoredSessions(storage: Pick<Storage, "getItem" | "setItem"> = localStorage): ChatSession[] {
  try {
    const current = storage.getItem(STORAGE_KEY);
    if (current) {
      const parsed = parseSessions(current);
      if (parsed.length > 0) return parsed;
    }
    const legacy = storage.getItem(LEGACY_STORAGE_KEY);
    if (legacy) {
      const parsed = parseSessions(legacy);
      if (parsed.length > 0) {
        try {
          storage.setItem(STORAGE_KEY, JSON.stringify(parsed));
        } catch {
          // ignore write errors during migration
        }
        return parsed;
      }
    }
  } catch {
    // storage unavailable
  }
  return [];
}

export function useChatHistory() {
  // Always start with empty/null — never read localStorage during SSR.
  // This prevents the server/client hydration mismatch.
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Load from localStorage only after mount (client-only)
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      const loaded = loadStoredSessions();
      setSessions(loaded);
      if (loaded.length > 0) setActiveSessionId(loaded[0].id);
      setHydrated(true);
    });
    return () => { cancelled = true; };
  }, []);

  // Persist to localStorage whenever sessions change (debounced to avoid streaming frame drops)
  useEffect(() => {
    if (!hydrated) return;
    const timer = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
      } catch {
        // quota exceeded or storage disabled
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [sessions, hydrated]);

  const createSession = (documentFilter?: string) => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: documentFilter ? `Chat about ${documentFilter}` : "New Chat",
      documentFilter,
      createdAt: Date.now(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    return newSession.id;
  };

  const updateSession = (id: string, updates: Partial<ChatSession>) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, ...updates } : s))
    );
  };

  const deleteSession = (id: string) => {
    setSessions((prev) => {
      const updated = prev.filter((s) => s.id !== id);
      if (activeSessionId === id) {
        setActiveSessionId(updated.length > 0 ? updated[0].id : null);
      }
      return updated;
    });
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return {
    sessions,
    hydrated,
    activeSessionId,
    activeSession,
    setActiveSessionId,
    createSession,
    updateSession,
    deleteSession,
  };
}
