"use client";
import { useEffect, useState } from "react";

interface Props {
  sections: { id: string; label: string }[];
}

export default function DotNavigation({ sections }: Props) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = sections.findIndex((s) => s.id === entry.target.id);
            if (idx !== -1) setActive(idx);
          }
        });
      },
      { threshold: 0.4 }
    );
    sections.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [sections]);

  return (
    <div style={{
      position: "fixed", right: 20, top: "50%", transform: "translateY(-50%)",
      zIndex: 50, display: "flex", flexDirection: "column", gap: 12
    }}>
      {sections.map((s, i) => (
        <button
          key={s.id}
          onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
          title={s.label}
          style={{
            width: 10, height: 10, borderRadius: "50%", border: "none", cursor: "pointer",
            background: i === active ? "var(--accent)" : "var(--border)",
            transform: i === active ? "scale(1.3)" : "scale(1)",
            transition: "all 0.3s",
          }}
        />
      ))}
    </div>
  );
}
