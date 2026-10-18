"use client";
import { Suspense } from "react";
import ChatInterface from "@/components/chat/ChatInterface";

export default function ChatPage() {
  return (
    <Suspense fallback={<div style={{ padding: 40, color: "var(--text-muted)" }}>Loading chat...</div>}>
      <ChatInterface />
    </Suspense>
  );
}
