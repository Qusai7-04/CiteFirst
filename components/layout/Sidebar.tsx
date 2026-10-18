"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Home, MessageSquare, GitBranch, BarChart3, FolderOpen, Settings, Sun, Moon } from "lucide-react";
import { useEffect, useState } from "react";

const items = [
  { href: "/", label: "Home", icon: Home },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/pipeline", label: "Pipeline", icon: GitBranch },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/vault", label: "Vault", icon: FolderOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);

  return (
    <aside style={{
      position: "fixed", left: 0, top: 64, bottom: 0, width: 64,
      background: "var(--sidebar-bg)", borderRight: "1px solid var(--border)",
      display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 16, paddingBottom: 24, zIndex: 100,
    }}>
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href === "/chat" ? "/chat?new=true" : href}
            title={label}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              width: 48, height: 48, borderRadius: 10, marginBottom: 4, textDecoration: "none",
              background: active ? "var(--accent-bg)" : "transparent",
              color: active ? "var(--accent)" : "var(--text-muted)",
              transition: "all 0.2s",
            }}
          >
            <Icon style={{ width: 20, height: 20 }} />
            <span style={{ fontSize: 9, marginTop: 2 }}>{label}</span>
          </Link>
        );
      })}

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Theme toggle */}
      {mounted && (
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: 40, height: 40, borderRadius: 10, border: "1px solid var(--border)",
            background: "var(--accent-bg)", color: "var(--accent)",
            cursor: "pointer", marginBottom: 32, transition: "all 0.2s", zIndex: 101,
          }}
        >
          {theme === "dark" ? <Sun style={{ width: 18, height: 18 }} /> : <Moon style={{ width: 18, height: 18 }} />}
        </button>
      )}
    </aside>
  );
}
