"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain } from "lucide-react";
import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/chat", label: "Chat" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/analytics", label: "Analytics" },
  { href: "/vault", label: "Vault" },
  { href: "/settings", label: "Settings" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">("checking");

  useEffect(() => {
    checkHealth().then((h) => {
      setApiStatus(h.status === "ok" ? "connected" : "disconnected");
    });
    const interval = setInterval(() => {
      checkHealth().then((h) => {
        setApiStatus(h.status === "ok" ? "connected" : "disconnected");
      });
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const dotColor = apiStatus === "connected" ? "#22c55e" : apiStatus === "disconnected" ? "#ef4444" : "#eab308";
  const statusText = apiStatus === "connected" ? "API Connected" : apiStatus === "disconnected" ? "API Offline" : "Checking...";

  return (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 50, height: 64,
      background: "var(--nav-bg)", backdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border)",
      display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px",
    }}>
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none" }}>
        <Brain style={{ width: 24, height: 24, color: "var(--accent)" }} />
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>CRAG</span>
      </Link>
      <div style={{ display: "flex", gap: 4 }}>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            style={{
              padding: "6px 14px", borderRadius: 8, fontSize: 14, fontWeight: 500,
              textDecoration: "none",
              background: pathname === item.href ? "var(--accent-bg)" : "transparent",
              color: pathname === item.href ? "var(--accent)" : "var(--text-muted)",
              transition: "all 0.2s",
            }}
          >
            {item.label}
          </Link>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* API status */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%", background: dotColor,
            animation: apiStatus === "connected" ? "pulse 2s infinite" : "none",
          }} />
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{statusText}</span>
        </div>
      </div>
    </nav>
  );
}
