"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { homeFor, saveSession } from "@/lib/session";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("+7 ");

  function formatPhone(value: string) {
    // Strip everything except digits
    const digits = value.replace(/\D/g, "");
    // Always start with 7
    const d = digits.startsWith("7") ? digits : "7" + digits;
    // Format: +7 XXX XXX-XX-XX
    let formatted = "+7";
    if (d.length > 1) formatted += " " + d.slice(1, 4);
    if (d.length > 4) formatted += " " + d.slice(4, 7);
    if (d.length > 7) formatted += "-" + d.slice(7, 9);
    if (d.length > 9) formatted += "-" + d.slice(9, 11);
    return formatted;
  }
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register") {
      if (password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
    }
    setLoading(true);

    try {
      let res;
      if (mode === "register") {
        res = await api.auth.register(email, password, fullName);
      } else {
        res = await api.auth.login(email, password);
      }

      saveSession(res.token, res.user);

      // Back to the page that sent the user here, if it is theirs to see;
      // useAuth on that page sends anyone else to their own home.
      const next = new URLSearchParams(window.location.search).get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : homeFor(res.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#ffffff", display: "flex", flexDirection: "column" }}>
      {/* Nav */}
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
          {[
            { href: "/", label: "Home" },
            { href: "/#apply", label: "Applicant Portal" },
            { href: "/teach", label: "Teaching Challenge" },
            { href: "/dashboard", label: "Admissions Dashboard" },
          ].map((link, i) => (
            <div key={link.label} style={{ display: "flex", alignItems: "center" }}>
              {i > 0 && <div style={{ width: "1px", height: "40px", backgroundColor: "#141414" }} />}
              <a
                href={link.href}
                style={{ padding: "14px 22px", borderRadius: "10px", textDecoration: "none", fontWeight: 500, color: "#141414", fontSize: "18px", whiteSpace: "nowrap", transition: "background-color 0.2s" }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#deff70")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                {link.label}
              </a>
            </div>
          ))}
        </div>
      </nav>

      {/* Main content */}
      <div style={{ flex: 1, position: "relative", display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 20px 0" }}>
        {/* Heading */}
        <h1 style={{ fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 700, color: "#141414", marginBottom: "16px" }}>
          {mode === "login" ? "Sign In" : "Sign Up"}
        </h1>

        {/* Form card */}
        <form
          onSubmit={handleSubmit}
          style={{
            position: "relative",
            zIndex: 1,
            width: "100%",
            maxWidth: "460px",
            backgroundColor: "#ffffff",
            border: "2px solid #d7d7d7",
            borderRadius: "15px",
            padding: "24px",
          }}
        >
          {error && (
            <div style={{ backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "10px", padding: "12px 16px", fontSize: "14px", color: "#b91c1c", marginBottom: "14px" }}>
              {error}
            </div>
          )}

          {mode === "register" && (
            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#141414", marginBottom: "6px", lineHeight: "28px" }}>
                Full Name
              </label>
              <div style={{ backgroundColor: "#eae9e9", borderRadius: "10px", padding: "8px 14px" }}>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full Name"
                  required
                  style={{ width: "100%", border: "none", backgroundColor: "transparent", fontSize: "14px", outline: "none", color: "#141414", lineHeight: "28px", boxSizing: "border-box" }}
                />
              </div>
            </div>
          )}

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#141414", marginBottom: "6px", lineHeight: "28px" }}>
              Email
            </label>
            <div style={{ backgroundColor: "#eae9e9", borderRadius: "10px", padding: "8px 14px" }}>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                style={{ width: "100%", border: "none", backgroundColor: "transparent", fontSize: "14px", outline: "none", color: "#141414", lineHeight: "28px", boxSizing: "border-box" }}
              />
            </div>
          </div>

          {/* Phone — register only */}
          {mode === "register" && (
            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#141414", marginBottom: "6px", lineHeight: "28px" }}>
                Mobile phone number
              </label>
              <div style={{ backgroundColor: "#eae9e9", borderRadius: "10px", padding: "8px 14px", display: "flex", alignItems: "center", gap: "10px" }}>
                <img src="/assets/Kazakhstan.png" alt="KZ" style={{ width: "40px", height: "20px", borderRadius: "3px", objectFit: "cover" }} />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(formatPhone(e.target.value))}
                  placeholder="+7 777 777-77-77"
                  style={{ flex: 1, border: "none", backgroundColor: "transparent", fontSize: "14px", outline: "none", color: "#141414", lineHeight: "28px", boxSizing: "border-box" }}
                />
              </div>
            </div>
          )}

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#141414", marginBottom: "6px", lineHeight: "28px" }}>
              Password
            </label>
            <div style={{ backgroundColor: "#eae9e9", borderRadius: "10px", padding: "8px 14px" }}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                style={{ width: "100%", border: "none", backgroundColor: "transparent", fontSize: "14px", outline: "none", color: "#141414", lineHeight: "28px", boxSizing: "border-box" }}
              />
            </div>
          </div>

          {/* Confirm password — register only */}
          {mode === "register" && (
            <div style={{ marginBottom: "14px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "#141414", marginBottom: "6px", lineHeight: "28px" }}>
                Confirm Password
              </label>
              <div style={{ backgroundColor: "#eae9e9", borderRadius: "10px", padding: "8px 14px" }}>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm Password"
                  required
                  style={{ width: "100%", border: "none", backgroundColor: "transparent", fontSize: "14px", outline: "none", color: "#141414", lineHeight: "28px", boxSizing: "border-box" }}
                />
              </div>
            </div>
          )}

          {/* Consent checkbox — register only */}
          {mode === "register" && (
            <div style={{ marginBottom: "14px", display: "flex", alignItems: "center", gap: "12px" }}>
              <div
                onClick={() => setConsent(!consent)}
                style={{
                  width: "24px", height: "24px", borderRadius: "4px",
                  border: consent ? "none" : "2px solid #676767",
                  backgroundColor: consent ? "#c1f11d" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: "pointer", flexShrink: 0,
                }}
              >
                {consent && <span style={{ color: "#141414", fontSize: "14px", fontWeight: 700 }}>{"\u2713"}</span>}
              </div>
              <span style={{ fontSize: "14px", color: "#676767", lineHeight: 1.4 }}>
                I consent to the processing of my data and agree to the Privacy Policy
              </span>
            </div>
          )}

          {/* Separator */}
          <div style={{ width: "100%", height: "2px", backgroundColor: "#f4f3f3", marginBottom: "14px" }} />

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "11px",
              backgroundColor: "#c1f11d",
              color: "#141414",
              fontSize: "16px",
              fontWeight: 600,
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
              lineHeight: "34px",
            }}
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Sign Up"}
          </button>
        </form>

        {/* Links */}
        <div style={{ position: "relative", zIndex: 1, marginTop: "24px", fontSize: "16px", color: "#676767", lineHeight: "34px", textAlign: "center" }}>
          {mode === "login" ? (
            <>
              Don&apos;t have an account?{" "}
              <span
                style={{ textDecoration: "underline", cursor: "pointer", color: "#141414" }}
                onClick={() => { setMode("register"); setError(null); }}
              >
                Sign Up
              </span>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <span
                style={{ textDecoration: "underline", cursor: "pointer", color: "#141414" }}
                onClick={() => { setMode("login"); setError(null); }}
              >
                Sign In
              </span>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer style={{ position: "relative", overflow: "hidden", padding: 0, marginTop: "60px" }}>
        <img src="/assets/Footer BG.png" alt="" style={{ width: "100%", display: "block" }} />
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", padding: "0 40px 40px" }}>
          <div style={{ display: "flex", justifyContent: "center", gap: "32px", marginBottom: "24px" }}>
            {[{ href: "/", label: "Home" }, { href: "/#apply", label: "Apply" }, { href: "/teach", label: "Teaching Challenge" }, { href: "/dashboard", label: "Dashboard" }].map((link) => (
              <a key={link.label} href={link.href} style={{ fontSize: "14px", color: "rgba(255,255,255,0.7)", textDecoration: "none", transition: "color 0.2s" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#c1f11d")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.7)")}
              >{link.label}</a>
            ))}
          </div>
          <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "center" }}>Powered by inDrive &middot; Built for Decentrathon 5.0</p>
        </div>
      </footer>
    </div>
  );
}
