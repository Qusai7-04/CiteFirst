"use client";
import type { Message } from "@/types/chat";
import { Brain, User, Copy, Edit3, RefreshCw, Check } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props { 
  message: Message; 
  onEdit?: (messageId: string, newContent: string) => void;
  onRegenerate?: (messageId: string) => void;
}

export default function ChatBubble({ message, onEdit, onRegenerate }: Props) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
    if (editContent !== message.content && onEdit) {
      onEdit(message.id, editContent);
    }
  };

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 16, flexDirection: isUser ? "row-reverse" : "row" }}>
      <div style={{
        width: 36, height: 36, borderRadius: "50%",
        background: isUser ? "var(--user-accent)" : "var(--accent-bg)",
        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        marginTop: 4
      }}>
        {isUser
          ? <User style={{ width: 18, height: 18, color: "var(--user-icon)" }} />
          : <Brain style={{ width: 18, height: 18, color: "var(--accent)" }} />}
      </div>
      <div style={{
        maxWidth: "80%",
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
      }}>
        <div style={{
          background: isUser ? "var(--user-accent)" : "var(--card)",
          border: `1px solid ${isUser ? "var(--user-border)" : "var(--card-border)"}`,
          borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
          padding: "12px 16px", fontSize: 14, color: "var(--text-primary)", lineHeight: 1.65,
          wordBreak: "break-word", 
        }}>
          {isEditing ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <textarea 
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                style={{
                  width: "100%", minWidth: 400, minHeight: 160, padding: 12,
                  background: "var(--bg-surface)", color: "var(--text-primary)",
                  border: "1px solid var(--border)", borderRadius: 8,
                  fontFamily: "inherit", resize: "vertical"
                }}
              />
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button onClick={() => setIsEditing(false)} style={{
                  padding: "4px 12px", borderRadius: 6, border: "1px solid var(--border)", background: "transparent", cursor: "pointer", color: "var(--text-primary)"
                }}>Cancel</button>
                <button onClick={handleSaveEdit} style={{
                  padding: "4px 12px", borderRadius: 6, border: "none", background: "var(--accent)", color: "#fff", cursor: "pointer"
                }}>Save & Resubmit</button>
              </div>
            </div>
          ) : (
            <div className="markdown-prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
        
        {/* Actions inside a small toolbar below bubble */}
        {!isEditing && (
          <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 6, padding: "0 4px" }}>
            <span style={{ fontSize: 11, color: "var(--text-faint)" }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={handleCopy} title="Copy" style={{
                background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", padding: 0
              }}>
                {copied ? <Check style={{ width: 14, height: 14, color: "#10b981" }} /> : <Copy style={{ width: 14, height: 14 }} />}
              </button>
              
              {isUser && onEdit && (
                <button onClick={() => setIsEditing(true)} title="Edit Message" style={{
                  background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", padding: 0
                }}>
                  <Edit3 style={{ width: 14, height: 14 }} />
                </button>
              )}

              {!isUser && onRegenerate && (
                <button onClick={() => onRegenerate(message.id)} title="Regenerate" style={{
                  background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", padding: 0
                }}>
                  <RefreshCw style={{ width: 14, height: 14 }} />
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
