"use client";

import { useState, type ReactNode } from "react";

/** The white card with a grey header button used on the dashboard (settings, audit). */
export function CollapsiblePanel({
  icon,
  title,
  badge,
  children,
}: {
  icon: string;
  title: string;
  badge?: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ backgroundColor: "#fff", borderRadius: "24px", border: "2px solid #d7d7d7", padding: "14px", marginBottom: "14px" }}>
      <button
        className="w-full flex items-center text-left"
        style={{ backgroundColor: "#eae9e9", borderRadius: "14px", padding: "18px 20px", border: "none", cursor: "pointer", gap: "14px" }}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div style={{ width: "46px", height: "46px", backgroundColor: "#141414", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <img src={icon} alt="" style={{ width: "24px", height: "24px" }} />
        </div>
        <div className="flex items-center gap-3">
          <span style={{ fontSize: "18px", fontWeight: 600, color: "#141414" }}>{title}</span>
          {badge}
        </div>
        <span className="text-gray-400 text-sm">{open ? "−" : "+"}</span>
      </button>
      {open && <div style={{ padding: "20px 24px 24px", borderTop: "1px solid #ddd" }}>{children}</div>}
    </div>
  );
}
