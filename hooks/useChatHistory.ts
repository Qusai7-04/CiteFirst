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

const STORAGE_KEY = "crag_chat_sessions";

function parseSessions(raw: string): ChatSession[] {
  try {
    const parsed = JSON.parse(raw);
    return parsed.map((s: ChatSession) => ({
      ...s,
      messages: s.messages.map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      })),
    }));
  } catch {
    return [];
  }
}

export function useChatHistory() {
  // Always start with empty/null — never read localStorage during SSR.
  // This prevents the server/client hydration mismatch.
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Load from localStorage only after mount (client-only)
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = parseSessions(stored);
      setSessions(parsed);
      if (parsed.length > 0) {
        setActiveSessionId(parsed[0].id);
      }
    }
    setHydrated(true);
  }, []);

  // Persist to localStorage whenever sessions change (after hydration)
  useEffect(() => {
    if (hydrated) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    }
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
