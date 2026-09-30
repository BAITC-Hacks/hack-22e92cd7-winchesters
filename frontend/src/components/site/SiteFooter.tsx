"use client";

// The footer every page shares: the brand background image with the
// statement and the page links laid over its lower edge.

const LINKS = [
  { href: "/#apply", label: "Apply" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/dashboard", label: "Dashboard" },
];

export function SiteFooter({ marginTop = 0 }: { marginTop?: number }) {
  return (
    <footer style={{ position: "relative", overflow: "hidden", padding: 0, marginTop: `${marginTop}px` }}>
      <img src="/assets/Footer BG.png" alt="" style={{ width: "100%", display: "block" }} />
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", padding: "0 40px 40px" }}>
        <p style={{ fontSize: "clamp(12px,1.07vw,20.16px)", color: "#ffffff", textAlign: "center", marginBottom: "14px" }}>
          AI-Assisted Evaluation System — All final admission decisions are made by the human admissions committee.
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: "clamp(20px,1.84vw,35.28px)" }}>
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              style={{ fontSize: "clamp(12px,0.77vw,14.4px)", color: "rgba(255,255,255,0.7)", textDecoration: "none", transition: "color 0.2s" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#c1f11d")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
            >
              {link.label}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
