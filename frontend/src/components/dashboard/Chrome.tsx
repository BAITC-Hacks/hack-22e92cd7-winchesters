"use client";

// Page furniture for the dashboard: nav, dark header with the stats bar, footer.

import { useEffect, useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/#apply", label: "Applicant Portal" },
  { href: "/teach", label: "Teaching Challenge" },
  { href: "/dashboard", label: "Admissions Dashboard", current: true },
];

export function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      setProgress(scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
  return (
    <div
      className="fixed top-0 left-0 h-[3px] bg-[#c1f11d] z-[200] transition-all duration-150"
      style={{ width: `${progress}%` }}
    />
  );
}

export function DashboardNav() {
  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        backgroundColor: "#c1f11d",
        padding: "18px 60px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <img src="/assets/InVision U Dark.png" alt="inVision U" style={{ width: "169.33px", height: "27.86px" }} />
      <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
        {NAV_LINKS.map((link, i) => (
          <div key={link.label} style={{ display: "flex", alignItems: "center" }}>
            {i > 0 && <div style={{ width: "1px", height: "40px", backgroundColor: "#141414" }} />}
            <a
              href={link.href}
              style={{
                padding: "14px 22px",
                borderRadius: "10px",
                textDecoration: "none",
                fontWeight: link.current ? 700 : 500,
                color: "#141414",
                fontSize: "18px",
                whiteSpace: "nowrap",
                transition: "background-color 0.2s",
                backgroundColor: link.current ? "#deff70" : "transparent",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.backgroundColor = "#deff70";
              }}
              onMouseLeave={(e) => {
                if (!link.current) {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                }
              }}
            >
              {link.label}
            </a>
          </div>
        ))}
      </div>
    </nav>
  );
}

export interface StatButton {
  key: string;
  label: string;
  count: number;
}

export function DashboardHeader({
  stats,
  active,
  onSelect,
}: {
  stats: StatButton[];
  active: string;
  onSelect: (key: string) => void;
}) {
  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "12px 40px 0", position: "relative" }}>
      <div style={{ backgroundColor: "#141414", borderRadius: "24px", overflow: "hidden", position: "relative", padding: "36px 40px 56px" }}>
        <img src="/assets/Dots.png" alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.3, pointerEvents: "none" }} />
        <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ fontSize: "34px", fontWeight: 700, color: "#c1f11d", marginBottom: "4px" }}>Admissions Dashboard</h1>
            <p style={{ fontSize: "16px", color: "#fff" }}>AI-Assisted Screening &middot; Human-in-the-Loop</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "15px", color: "#fff" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#c1f11d", display: "inline-block" }} />
            System active
          </div>
        </div>
      </div>

      {/* Stats bar — overlapping header */}
      <div style={{ position: "relative", zIndex: 2, marginTop: "-34px", display: "flex", gap: "8px", padding: "14px 16px", backgroundColor: "#fff", borderRadius: "20px", border: "2px solid #d7d7d7" }}>
        {stats.map((stat) => (
          <button
            key={stat.key}
            onClick={() => onSelect(stat.key)}
            style={{
              flex: 1,
              padding: "16px 18px",
              borderRadius: "12px",
              border: "none",
              backgroundColor: active === stat.key ? "#c1f11d" : "#eae9e9",
              cursor: "pointer",
              textAlign: "left",
              transition: "all 0.2s ease",
            }}
          >
            <p style={{ fontSize: "28px", fontWeight: 700, color: "#141414", lineHeight: 1, marginBottom: "4px" }}>{stat.count}</p>
            <p style={{ fontSize: "14px", color: "#141414" }}>{stat.label}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

export function DashboardFooter() {
  return (
    <footer style={{ position: "relative", overflow: "hidden", padding: 0, marginTop: "40px" }}>
      <img src="/assets/Footer BG.png" alt="" style={{ width: "100%", display: "block" }} />
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", padding: "0 40px 40px" }}>
        <div style={{ display: "flex", justifyContent: "center", gap: "32px", marginBottom: "24px" }}>
          {[{ href: "/", label: "Home" }, { href: "/#apply", label: "Apply" }, { href: "/teach", label: "Teaching Challenge" }, { href: "/dashboard", label: "Dashboard" }].map((link) => (
            <a key={link.label} href={link.href} style={{ fontSize: "14px", color: "rgba(255,255,255,0.7)", textDecoration: "none", transition: "color 0.2s" }}
              onMouseEnter={(e: React.MouseEvent<HTMLAnchorElement>) => (e.currentTarget.style.color = "#c1f11d")}
              onMouseLeave={(e: React.MouseEvent<HTMLAnchorElement>) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
            >{link.label}</a>
          ))}
        </div>
        <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "center" }}>Powered by inDrive &middot; Built for Decentrathon 5.0</p>
      </div>
    </footer>
  );
}
