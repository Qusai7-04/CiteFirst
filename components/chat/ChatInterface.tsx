"use client";
import { useState, useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Send, Loader2, Paperclip, MessageSquare, Plus, Download, Copy, Trash2, FileText } from "lucide-react";
import type { Message } from "@/types/chat";
import { useQuery } from "@/hooks/useQuery";
import { useChatHistory } from "@/hooks/useChatHistory";
import { api } from "@/lib/api";
import ChatBubble from "./ChatBubble";
import SourceCard from "./SourceCard";
import PipelineStepsBubble from "./PipelineStepsBubble";

export default function ChatInterface() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get("q") || "";
  const isNewChat = searchParams.get("new") === "true";
  

  
  const {
    sessions,
    hydrated,
    activeSessionId,
    activeSession,
    setActiveSessionId,
    createSession,
    updateSession,
    deleteSession
  } = useChatHistory();

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeDocument, setActiveDocument] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const sidebarOpen = true;

  const bottomRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const hasRun = useRef(false);
  const { sendQueryStream, currentStep } = useQuery();

  useEffect(() => {
    if (!isNewChat) return;
    queueMicrotask(() => {
      setActiveSessionId(null);
      setActiveDocument(null);
      setMessages([]);
      router.replace("/chat");
    });
  }, [isNewChat, router, setActiveSessionId]);

  // Load session data when switching sessions
  useEffect(() => {
    if (isNewChat) return;
    let cancelled = false;
    const session = sessions.find(s => s.id === activeSessionId);
    queueMicrotask(() => {
      if (cancelled) return;
      setMessages(session?.messages || []);
      setActiveDocument(session?.documentFilter || null);
    });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSessionId, isNewChat]);

  // Save messages to history when they change
  useEffect(() => {
    if (activeSessionId && messages.length > 0) {
      updateSession(activeSessionId, { messages, documentFilter: activeDocument || undefined });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, activeDocument]);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: loading ? "auto" : "smooth" });
    }
  }, [messages, loading]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const data = await api.upload<{ filename: string; size?: number; indexed?: boolean; warning?: string }>(
        "/api/vault/upload",
        file
      );
      if (data?.filename) {
        setActiveDocument(data.filename);

        // If no active session, create one
        if (!activeSessionId) {
          createSession(data.filename);
        } else {
          updateSession(activeSessionId, { documentFilter: data.filename, title: `Chat about ${data.filename}` });
        }
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleCopyChat = () => {
    const text = messages.map(m => `[${m.role.toUpperCase()}] ${m.content}`).join("\n\n");
    navigator.clipboard.writeText(text);
    alert("Chat copied to clipboard!");
  };

  const handleExportPDF = async () => {
    if (!chatContainerRef.current) return;
    const element = chatContainerRef.current;
    
    const html2pdf = (await import("html2pdf.js")).default;

    html2pdf().set({
      margin: 10,
      filename: `citefirst_chat_export_${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }).from(element).save();
  };

  const handleSubmit = async (query: string, forceSessionId?: string) => {
    const q = (query || input).trim();
    if (!q || loading) return;
    setInput("");
    setLoading(true);

    let currentSessionId = forceSessionId || activeSessionId;
    if (!currentSessionId) {
      currentSessionId = createSession(activeDocument || undefined);
    }

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: q, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const raw = await sendQueryStream(q, activeDocument || undefined);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: raw.answer,
        timestamp: new Date(),
        sources: (raw.facts || []).map((fact, i) => ({
          filename: raw.evidence?.[i]?.source || raw.sources?.[i] || raw.sources?.[0] || "Unknown source",
          score: 0,
          evidenceStatus: raw.status === "partial_match" ? "partial" as const : "evidence" as const,
          pageNumber: raw.evidence?.[i]?.page_number ?? null,
          evidenceId: raw.evidence?.[i]?.id ?? null,
          text: typeof fact === "string" ? fact : String(fact),
        })),
        pipeline: {
          status: raw.status,
          chunksKept: raw.facts?.length || 0,
          queryUsed: raw.query_used,
        },
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "⚠️ Backend not reachable. Start the FastAPI server: `uvicorn api:app --reload`",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Handle initial query from home page
  useEffect(() => {
    if (initialQuery && !hasRun.current) {
      hasRun.current = true;
      const sessionId = createSession();
      setActiveSessionId(sessionId);
      // Wait for state to settle then submit
      setTimeout(() => {
        handleSubmit(initialQuery, sessionId);
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const handleEdit = (id: string, newContent: string) => {
    // Truncate history at the edited message, replace it, then submit
    const idx = messages.findIndex(m => m.id === id);
    if (idx === -1) return;
    const newMessages = messages.slice(0, idx); // remove the old user message and all subsequent
    setMessages(newMessages);
    setTimeout(() => handleSubmit(newContent), 50);
  };

  const handleRegenerate = (id: string) => {
    // Truncate history up to the user message that caused this response
    const idx = messages.findIndex(m => m.id === id);
    if (idx <= 0) return; // Need a user message before it
    
    // Find previous user message
    let userMsgIdx = -1;
    for (let i = idx - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        userMsgIdx = i;
        break;
      }
    }
    
    if (userMsgIdx !== -1) {
      const userMsg = messages[userMsgIdx];
      const newMessages = messages.slice(0, userMsgIdx); // truncate
      setMessages(newMessages);
      setTimeout(() => handleSubmit(userMsg.content), 50);
    }
  };

  const stepLabels: Record<string, string> = {
    fetching: "Hybrid retrieval (Dense + BM25 + RRF)…",
    reranking: "BGE Reranker scoring top chunks…",
    grading: "Tri-state grading (Correct / Ambiguous / Incorrect)…",
    resolving: "Pre-flight combined relevance check…",
    generating: "Generating citation-grounded answer…",
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 64px)", width: "100%" }}>
      {/* Sidebar for History */}
      {sidebarOpen && (
        <div style={{ 
          width: 260, 
          borderRight: "1px solid var(--border)", 
          background: "var(--sidebar-bg)",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ padding: 16 }}>
            <button 
              onClick={() => {
                setActiveSessionId(null);
                setActiveDocument(null);
                setMessages([]);
              }}
              style={{
                width: "100%", padding: "10px", background: "var(--accent)", color: "#020617",
                borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                fontWeight: 500, border: "none", cursor: "pointer"
              }}
            >
              <Plus size={18} /> New Chat
            </button>
          </div>
          
          <div style={{ flex: 1, overflowY: "auto" }}>
            {hydrated ? sessions.map(session => (
              <div 
                key={session.id}
                style={{
                  padding: "12px 16px",
                  cursor: "pointer",
                  background: activeSessionId === session.id ? "var(--accent-bg)" : "transparent",
                  borderLeft: activeSessionId === session.id ? "3px solid var(--accent)" : "3px solid transparent",
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  transition: "background 0.2s"
                }}
                onClick={() => setActiveSessionId(session.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12, overflow: "hidden" }}>
                  <MessageSquare size={16} color="var(--text-muted)" />
                  <div style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", fontSize: 14 }}>
                    {session.title}
                  </div>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-faint)" }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )) : null}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
        
        {/* Top actions */}
        {messages.length > 0 && (
          <div style={{ padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)", zIndex: 10, background: "var(--card)" }}>
            <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: 16, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "60%" }}>
              {activeSession?.title || messages[0]?.content || "Chat"}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={handleCopyChat} title="Copy Chat" style={{
                background: "transparent", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 12px",
                display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: "var(--text-secondary)", fontSize: 13, fontWeight: 500, transition: "all 0.2s"
              }}>
                <Copy size={14} /> Copy
              </button>
              <button onClick={handleExportPDF} title="Download PDF" style={{
                background: "transparent", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 12px",
                display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: "var(--text-secondary)", fontSize: 13, fontWeight: 500, transition: "all 0.2s"
              }}>
                <Download size={14} /> Download
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div ref={chatContainerRef} style={{ flex: 1, overflowY: "auto", padding: "24px 24px 8px", margin: "0 auto", width: "100%", maxWidth: 900 }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", paddingTop: 100, color: "var(--text-muted)" }}>
              <div style={{ fontSize: "4rem", marginBottom: 16 }}>🧠</div>
              <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-faint)", marginBottom: 8 }}>Ask CiteFirst</h2>
              {activeDocument ? (
                <p style={{ color: "var(--accent)" }}>Active Document: {activeDocument}</p>
              ) : (
                <p style={{ fontSize: "0.9rem" }}>Upload a document to chat specifically about it, or ask a general query.</p>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id}>
              <ChatBubble 
                message={msg} 
                onEdit={(_id, newContent) => handleEdit(msg.id, newContent)}
                onRegenerate={() => handleRegenerate(msg.id)}
              />
              {msg.role === "assistant" && msg.pipeline && <PipelineStepsBubble pipeline={msg.pipeline} />}
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div style={{ marginLeft: 48, marginBottom: 16, display: "flex", flexWrap: "wrap", gap: 8, pageBreakInside: "avoid" }}>
                  {msg.sources.map((src, i) => <SourceCard key={i} source={src} />)}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", marginBottom: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--accent-bg)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Loader2 style={{ width: 18, height: 18, color: "var(--accent)", animation: "spin 1s linear infinite" }} />
              </div>
              <div style={{ background: "var(--card)", borderRadius: 12, padding: "10px 16px", color: "var(--text-muted)", fontSize: 14, border: "1px solid var(--card-border)" }}>
                {stepLabels[currentStep] || "Running pipeline: Fetch → Rerank → Grade..."}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: "16px 24px 24px", borderTop: "1px solid var(--border)", margin: "0 auto", width: "100%", maxWidth: 900 }}>
          {activeDocument && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, fontSize: 12, color: "var(--accent)" }}>
              <FileText size={14} /> Chatting about: <strong style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 300 }}>{activeDocument}</strong>
              <button 
                onClick={() => setActiveDocument(null)}
                style={{ background: "none", border: "none", color: "var(--text-faint)", cursor: "pointer", marginLeft: 8 }}
              >
                (Clear)
              </button>
            </div>
          )}
          
          <div style={{ display: "flex", gap: 12 }}>
            <label style={{
              width: 50, height: 50, borderRadius: 12, background: "var(--input-bg)", border: "1px solid var(--input-border)",
              cursor: uploading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center",
              color: "var(--text-secondary)", flexShrink: 0
            }}>
              {uploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
              <input type="file" accept=".pdf" style={{ display: "none" }} onChange={handleFileUpload} disabled={uploading} />
            </label>

            <input
              type="text" value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit(input)}
              placeholder={activeDocument ? `Ask about ${activeDocument}…` : "Ask your documents anything, or upload a PDF to filter answers to it…"}
              disabled={loading || uploading}
              style={{
                flex: 1, padding: "14px 20px", background: "var(--input-bg)", border: "1px solid var(--input-border)",
                borderRadius: 12, color: "var(--text-primary)", fontSize: 15, outline: "none",
                opacity: 1
              }}
            />
            <button
              onClick={() => handleSubmit(input)} disabled={loading || !input.trim()}
              style={{
                width: 50, height: 50, borderRadius: 12, background: "var(--accent)", border: "none",
                cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                opacity: loading || !input.trim() ? 0.5 : 1, transition: "opacity 0.2s", flexShrink: 0
              }}
            >
              <Send style={{ width: 18, height: 18, color: "#020617" }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
