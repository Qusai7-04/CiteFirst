"use client";
import { useRouter } from "next/navigation";
import { ArrowRight, BookOpen } from "lucide-react";

export default function FooterSection() {
  const router = useRouter();
  return (
    <section style={{ padding: "80px 24px", borderTop: "1px solid var(--border)", textAlign: "center" }}>
      <h2 style={{ fontSize: "2.2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: 12 }}>Ready to Get Started?</h2>
      <p style={{ color: "var(--text-muted)", marginBottom: 36, fontSize: "1.05rem" }}>
        Upload your documents, ask questions, and see CRAG&apos;s self-correcting pipeline in action.
      </p>
      <div style={{ display: "flex", justifyContent: "center", gap: 16 }}>
        <button
          onClick={() => router.push("/chat")}
          style={{ padding: "14px 28px", background: "var(--accent)", color: "#020617", fontWeight: 700, borderRadius: 10, border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 8, fontSize: 15 }}
        >
          Start Chatting <ArrowRight style={{ width: 18, height: 18 }} />
        </button>
        <button
          onClick={() => router.push("/vault")}
          style={{ padding: "14px 28px", background: "transparent", color: "var(--text-muted)", border: "1px solid var(--border)", borderRadius: 10, cursor: "pointer", display: "flex", alignItems: "center", gap: 8, fontSize: 15 }}
        >
          <BookOpen style={{ width: 18, height: 18 }} /> Upload Documents
        </button>
      </div>
      <p style={{ marginTop: 48, color: "var(--text-faint)", fontSize: 13 }}>
        Built with Next.js 16 · FastAPI · ChromaDB · SentenceTransformers · cross-encoder/ms-marco-MiniLM-L-6-v2
      </p>
    </section>
  );
}
