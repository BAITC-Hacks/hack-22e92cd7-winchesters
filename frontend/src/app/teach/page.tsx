"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";

type Topic = { id: string; title: string; description: string };
type Message = { role: "user" | "assistant"; content: string };
type QuizAnswer = {
  question: string;
  answer: string;
  confident: boolean;
};

type Score = {
  clarity: number;
  patience: number;
  empathy: number;
  adaptability: number;
  quiz_transfer_score: number;
  overall_score: number;
  summary: string;
  message_count: number;
  quiz_answers?: QuizAnswer[];
};

type Phase = "setup" | "teaching" | "scoring" | "results";

function ScoreDimension({ label, score }: { label: string; score: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
      <span style={{ fontSize: "16px", color: "#a0a0a0", width: "148px", flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: "12px", backgroundColor: "#333", borderRadius: "9999px", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            borderRadius: "9999px",
            backgroundColor: "#c1f11d",
            transition: "width 0.5s ease",
            width: `${Math.min(score, 100)}%`,
          }}
        />
      </div>
      <span style={{ fontSize: "16px", fontFamily: "monospace", fontWeight: 600, width: "36px", textAlign: "right", color: "#c1f11d" }}>{score}</span>
    </div>
  );
}

export default function TeachPage() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string>("");
  const [candidateId, setCandidateId] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [canFinish, setCanFinish] = useState(false);
  const [mustFinish, setMustFinish] = useState(false);
  const [remaining, setRemaining] = useState(8);
  const [messageCount, setMessageCount] = useState(0);
  const [score, setScore] = useState<Score | null>(null);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    api.feynman.topics().then(setTopics).catch(() => {});
    // Auto-fill candidate ID from application form
    if (typeof window !== "undefined") {
      const savedId = window.localStorage.getItem("invisionu_candidate_id");
      const savedName = window.localStorage.getItem("invisionu_candidate_name");
      if (savedId) setCandidateId(savedId);
      else if (savedName) setCandidateId(savedName);
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Scroll progress bar tracking
  useEffect(() => {
    function handleScroll() {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight > 0) {
        setScrollProgress((scrollTop / docHeight) * 100);
      }
    }
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  async function handleStart() {
    if (!candidateId.trim() || !selectedTopic) return;
    setError(null);
    setSending(true);
    try {
      const res = await api.feynman.start(candidateId.trim(), selectedTopic);
      setSessionId(res.session_id);
      setMessages([{ role: "assistant", content: res.first_message }]);
      setMessageCount(1);
      setPhase("teaching");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start session");
    } finally {
      setSending(false);
    }
  }

  async function handleSend() {
    if (!input.trim() || !sessionId || sending) return;
    const msg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setSending(true);
    try {
      const res = await api.feynman.chat(sessionId, msg);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      setMessageCount(res.message_count);
      setCanFinish(res.can_finish);
      setMustFinish(res.must_finish);
      setRemaining(res.remaining);
      // Auto-finish if max exchanges reached
      if (res.must_finish) {
        setTimeout(() => handleFinish(), 1500);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  }

  async function handleFinish() {
    if (!sessionId) return;
    setPhase("scoring");
    try {
      const res = await api.feynman.finish(sessionId);
      setScore(res);
      setPhase("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scoring failed");
      setPhase("teaching");
    }
  }

  function handleReset() {
    setPhase("setup");
    setSessionId(null);
    setMessages([]);
    setInput("");
    setCanFinish(false);
    setMustFinish(false);
    setRemaining(8);
    setMessageCount(0);
    setScore(null);
    setError(null);
  }

  const topicObj = topics.find((t) => t.id === selectedTopic);

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>
      {/* Scroll progress bar */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "3px",
          width: `${scrollProgress}%`,
          backgroundColor: "#c1f11d",
          zIndex: 200,
          transition: "width 0.1s linear",
        }}
      />

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
        <img
          src="/assets/InVision U Dark.png"
          alt="inVision U"
          style={{ width: "169.33px", height: "27.86px" }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
          {[
            { href: "/", label: "Home" },
            { href: "/#apply", label: "Applicant Portal" },
            { href: "/teach", label: "Teaching Challenge" },
            { href: "/dashboard", label: "Admissions Dashboard" },
          ].map((link, i) => (
            <div key={link.label} style={{ display: "flex", alignItems: "center" }}>
              {i > 0 && (
                <div style={{ width: "1px", height: "40px", backgroundColor: "#141414" }} />
              )}
              <a
                href={link.href}
                style={{
                  padding: "14px 22px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 500,
                  color: "#141414",
                  fontSize: "18px",
                  whiteSpace: "nowrap",
                  transition: "background-color 0.2s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "#deff70";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                }}
              >
                {link.label}
              </a>
            </div>
          ))}
        </div>
      </nav>

      {/* ── Setup Phase ────────────────────────────────────── */}
      {phase === "setup" && (
        <>
          {/* Header with brush background */}
          <div
            style={{
              backgroundColor: "#c1f11d",
              padding: "56px 32px 64px",
              textAlign: "center",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <img
              src="/assets/Brush BG.png"
              alt=""
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                opacity: 0.15,
                pointerEvents: "none",
              }}
            />
            <h1 style={{ position: "relative", zIndex: 1, fontSize: "42px", fontWeight: 800, color: "#141414", marginBottom: "10px" }}>
              Feynman Teaching Challenge
            </h1>
            <p style={{ position: "relative", zIndex: 1, fontSize: "18px", color: "#333", maxWidth: "580px", margin: "0 auto" }}>
              Prove you understand a concept by teaching it to Arman — a curious 10-year-old AI student.
              The better Arman understands, the higher your score.
            </p>
          </div>

          <div style={{ maxWidth: "900px", margin: "0 auto", padding: "0 32px" }}>
            {/* How it works */}
            <div
              style={{
                background: "linear-gradient(180deg, #252525 0%, #0F0F0F 100%)",
                border: "1px solid #525252",
                borderRadius: "24px",
                padding: "36px 40px",
                marginTop: "-32px",
                position: "relative",
                zIndex: 10,
              }}
            >
              <h3 style={{ fontWeight: 600, color: "#ffffff", marginBottom: "20px", fontSize: "18px" }}>How it works</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "24px" }}>
                {[
                  "Pick a topic and teach it to Arman in a chat",
                  "After 4-8 exchanges, finish the session",
                  "Arman takes a quiz. Your score = his understanding",
                ].map((text, i) => (
                  <div key={i} style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                    <span
                      style={{
                        backgroundColor: "#c1f11d",
                        color: "#141414",
                        fontWeight: 700,
                        fontSize: "15px",
                        width: "30px",
                        height: "30px",
                        borderRadius: "10px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      {i + 1}
                    </span>
                    <span style={{ fontSize: "16px", color: "#ccc" }}>{text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Form */}
            <div style={{ marginTop: "40px", paddingBottom: "56px" }}>
              {/* Candidate identifier */}
              <div style={{ marginBottom: "28px" }}>
                <label style={{ display: "block", fontSize: "18px", fontWeight: 500, color: "#333", marginBottom: "10px" }}>
                  {candidateId.startsWith("c-") ? "Candidate ID (linked from your application)" : "Your Name"} <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <input
                  style={{
                    width: "100%",
                    borderRadius: "14px",
                    border: "1px solid #d1d5db",
                    padding: "18px 22px",
                    fontSize: "18px",
                    outline: "none",
                    transition: "border-color 0.2s, box-shadow 0.2s",
                    boxSizing: "border-box",
                  }}
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                  placeholder="Enter your full name"
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#c1f11d";
                    e.currentTarget.style.boxShadow = "0 0 0 3px rgba(193,241,29,0.3)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "#d1d5db";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                />
              </div>

              {/* Topic selection */}
              <div style={{ marginBottom: "28px" }}>
                <label style={{ display: "block", fontSize: "16px", fontWeight: 500, color: "#333", marginBottom: "14px" }}>
                  Choose a topic to teach <span style={{ color: "#ef4444" }}>*</span>
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "14px" }}>
                  {topics.map((t, idx) => {
                    const isSelected = selectedTopic === t.id;
                    return (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTopic(t.id)}
                        style={{
                          textAlign: "left",
                          borderRadius: "18px",
                          padding: "20px 22px",
                          cursor: "pointer",
                          transition: "transform 0.2s, box-shadow 0.2s, border-color 0.2s",
                          background: isSelected
                            ? "linear-gradient(180deg, #2a2a2a 0%, #141414 100%)"
                            : "linear-gradient(180deg, #252525 0%, #0F0F0F 100%)",
                          border: isSelected
                            ? "2px solid #c1f11d"
                            : "1px solid #525252",
                          display: "flex",
                          gap: "14px",
                          alignItems: "flex-start",
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = "rgba(193,241,29,0.5)";
                            e.currentTarget.style.boxShadow = "0 0 20px rgba(193,241,29,0.15)";
                            e.currentTarget.style.transform = "translateY(-2px)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = "#525252";
                            e.currentTarget.style.boxShadow = "none";
                            e.currentTarget.style.transform = "translateY(0)";
                          }
                        }}
                      >
                        <span
                          style={{
                            backgroundColor: isSelected ? "#c1f11d" : "#333",
                            color: isSelected ? "#141414" : "#999",
                            fontWeight: 700,
                            fontSize: "14px",
                            width: "34px",
                            height: "34px",
                            borderRadius: "10px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            flexShrink: 0,
                            transition: "background-color 0.2s, color 0.2s",
                          }}
                        >
                          {idx + 1}
                        </span>
                        <div>
                          <p style={{ fontSize: "16px", fontWeight: 600, color: "#fff", margin: 0 }}>{t.title}</p>
                          <p style={{ fontSize: "14px", color: "#888", margin: "4px 0 0 0" }}>{t.description}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {error && (
                <div style={{ borderRadius: "14px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", padding: "14px 20px", fontSize: "16px", color: "#b91c1c", marginBottom: "20px" }}>
                  {error}
                </div>
              )}

              <button
                onClick={handleStart}
                disabled={!candidateId.trim() || !selectedTopic || sending}
                style={{
                  width: "100%",
                  borderRadius: "14px",
                  backgroundColor: "#141414",
                  color: "#c1f11d",
                  padding: "16px 24px",
                  fontSize: "17px",
                  fontWeight: 600,
                  border: "none",
                  cursor: !candidateId.trim() || !selectedTopic || sending ? "not-allowed" : "pointer",
                  opacity: !candidateId.trim() || !selectedTopic || sending ? 0.5 : 1,
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  if (candidateId.trim() && selectedTopic && !sending) {
                    e.currentTarget.style.transform = "scale(1.03)";
                    e.currentTarget.style.boxShadow = "0 0 24px rgba(193,241,29,0.3)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                {sending ? "Starting..." : "Start Teaching Session"}
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── Teaching Phase ──────────────────────────────────── */}
      {phase === "teaching" && (
        <div style={{ maxWidth: "900px", margin: "0 auto", padding: "32px 32px 56px" }}>
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
            <div>
              <h2 style={{ fontSize: "24px", fontWeight: 700, color: "#141414", margin: 0 }}>
                Teaching: {topicObj?.title}
              </h2>
              <p style={{ fontSize: "14px", color: "#888", margin: "4px 0 0 0" }}>
                {messageCount} exchange{messageCount !== 1 ? "s" : ""}
                {!canFinish && ` — need ${4 - messageCount} more to finish`}
                {canFinish && !mustFinish && ` — ${remaining} remaining`}
                {mustFinish && " — session complete, scoring..."}
              </p>
            </div>
            {canFinish && (
              <button
                onClick={handleFinish}
                style={{
                  borderRadius: "14px",
                  backgroundColor: "#c1f11d",
                  color: "#141414",
                  padding: "14px 24px",
                  fontSize: "16px",
                  fontWeight: 600,
                  border: "none",
                  cursor: "pointer",
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "scale(1.03)";
                  e.currentTarget.style.boxShadow = "0 0 24px rgba(193,241,29,0.4)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                Finish &amp; Get Score
              </button>
            )}
          </div>

          {/* Chat */}
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "22px",
              border: "1px solid #e5e7eb",
              overflow: "hidden",
            }}
          >
            <div style={{ height: "460px", overflowY: "auto", padding: "24px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {messages.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                    }}
                  >
                    <div
                      style={{
                        maxWidth: "80%",
                        borderRadius: "20px",
                        padding: "14px 20px",
                        fontSize: "16px",
                        lineHeight: "1.5",
                        ...(m.role === "user"
                          ? {
                              backgroundColor: "#141414",
                              color: "#ffffff",
                              borderBottomRightRadius: "6px",
                            }
                          : {
                              backgroundColor: "#f5f5f5",
                              color: "#1a1a1a",
                              borderBottomLeftRadius: "6px",
                            }),
                      }}
                    >
                      {m.role === "assistant" && (
                        <p style={{ fontSize: "12px", fontWeight: 600, color: "#c1f11d", marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#c1f11d", display: "inline-block" }} />
                          Arman (10 y.o.)
                        </p>
                      )}
                      {m.content}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div style={{ display: "flex", justifyContent: "flex-start" }}>
                    <div
                      style={{
                        backgroundColor: "#f5f5f5",
                        borderRadius: "20px",
                        borderBottomLeftRadius: "6px",
                        padding: "14px 20px",
                        fontSize: "16px",
                        color: "#999",
                        animation: "pulse 1.5s ease-in-out infinite",
                      }}
                    >
                      <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#c1f11d", display: "inline-block" }} />
                        Arman is thinking...
                      </span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            </div>

            {/* Input */}
            <div style={{ borderTop: "1px solid #e5e7eb", padding: "16px 20px", display: "flex", gap: "14px" }}>
              <input
                style={{
                  flex: 1,
                  borderRadius: "14px",
                  border: "1px solid #d1d5db",
                  padding: "14px 18px",
                  fontSize: "16px",
                  outline: "none",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder={mustFinish ? "Session complete — scoring..." : "Teach Arman..."}
                disabled={sending || mustFinish}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#c1f11d";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(193,241,29,0.3)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "#d1d5db";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || sending || mustFinish}
                style={{
                  borderRadius: "14px",
                  backgroundColor: "#c1f11d",
                  color: "#141414",
                  padding: "14px 24px",
                  fontSize: "16px",
                  fontWeight: 600,
                  border: "none",
                  cursor: !input.trim() || sending ? "not-allowed" : "pointer",
                  opacity: !input.trim() || sending ? 0.5 : 1,
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  if (input.trim() && !sending) {
                    e.currentTarget.style.transform = "scale(1.03)";
                    e.currentTarget.style.boxShadow = "0 0 16px rgba(193,241,29,0.4)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                Send
              </button>
            </div>
          </div>

          {error && (
            <div style={{ borderRadius: "14px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", padding: "14px 20px", fontSize: "16px", color: "#b91c1c", marginTop: "20px" }}>
              {error}
            </div>
          )}
        </div>
      )}

      {/* ── Scoring Phase ──────────────────────────────────── */}
      {phase === "scoring" && (
        <div
          style={{
            backgroundColor: "#141414",
            minHeight: "calc(100vh - 60px)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            gap: "24px",
          }}
        >
          <div
            style={{
              width: "60px",
              height: "60px",
              border: "4px solid #333",
              borderTopColor: "#c1f11d",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <h2 style={{ fontSize: "24px", fontWeight: 700, color: "#ffffff", margin: 0 }}>Evaluating your teaching...</h2>
          <p style={{ fontSize: "16px", color: "#888" }}>
            Arman is taking a quiz, and our evaluator is scoring your session.
          </p>
        </div>
      )}

      {/* ── Results Phase ──────────────────────────────────── */}
      {phase === "results" && score && (
        <div style={{ maxWidth: "900px", margin: "0 auto", padding: "48px 32px 68px" }}>
          {/* Overall score */}
          <div style={{ textAlign: "center", marginBottom: "40px" }}>
            <h2 style={{ fontSize: "34px", fontWeight: 700, color: "#141414", marginBottom: "20px" }}>Teaching Score</h2>
            <div
              style={{
                display: "inline-flex",
                alignItems: "baseline",
                gap: "8px",
                backgroundColor: "#c1f11d",
                borderRadius: "24px",
                padding: "20px 44px",
              }}
            >
              <span style={{ fontSize: "56px", fontWeight: 800, color: "#141414" }}>{score.overall_score}</span>
              <span style={{ fontSize: "20px", fontWeight: 500, color: "#333" }}>/ 100</span>
            </div>
          </div>

          {/* Dimensions */}
          <div
            style={{
              background: "linear-gradient(180deg, #252525 0%, #0F0F0F 100%)",
              border: "1px solid #525252",
              borderRadius: "24px",
              padding: "36px 40px",
              marginBottom: "24px",
            }}
          >
            <h3 style={{ fontWeight: 600, color: "#ffffff", marginBottom: "24px", fontSize: "18px" }}>Evaluation Breakdown</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <ScoreDimension label="Clarity" score={score.clarity} />
              <ScoreDimension label="Patience" score={score.patience} />
              <ScoreDimension label="Empathy" score={score.empathy} />
              <ScoreDimension label="Adaptability" score={score.adaptability} />
            </div>
            <div style={{ borderTop: "1px solid #333", marginTop: "20px", paddingTop: "16px" }}>
              <ScoreDimension label="Quiz Transfer" score={score.quiz_transfer_score} />
              <p style={{ fontSize: "14px", color: "#666", marginTop: "8px", marginLeft: "162px" }}>
                How well Arman answered quiz questions based on your teaching
              </p>
            </div>
          </div>

          {/* Quiz Results — transparency */}
          {score.quiz_answers && score.quiz_answers.length > 0 && (
            <div
              style={{
                background: "linear-gradient(180deg, #252525 0%, #0F0F0F 100%)",
                border: "1px solid #525252",
                borderRadius: "24px",
                padding: "32px 36px",
                marginBottom: "24px",
              }}
            >
              <h3 style={{ fontWeight: 600, color: "#fff", marginBottom: "20px", fontSize: "18px" }}>
                Quiz Results — What Arman Learned
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {score.quiz_answers.map((qa, i) => (
                  <div key={i} style={{ padding: "16px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "12px" }}>
                    <p style={{ fontSize: "14px", color: "#999", marginBottom: "6px" }}>
                      Q{i + 1}: {qa.question}
                    </p>
                    <p style={{ fontSize: "16px", color: "#fff", margin: 0 }}>
                      <span style={{ color: "#c1f11d", marginRight: "8px" }}>Arman:</span>
                      {qa.answer}
                    </p>
                    <span style={{
                      display: "inline-block",
                      marginTop: "6px",
                      fontSize: "12px",
                      padding: "2px 10px",
                      borderRadius: "10px",
                      backgroundColor: qa.confident ? "rgba(193,241,29,0.15)" : "rgba(255,100,100,0.15)",
                      color: qa.confident ? "#c1f11d" : "#ff6b6b",
                    }}>
                      {qa.confident ? "Confident" : "Not sure"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div
            style={{
              background: "linear-gradient(180deg, #252525 0%, #0F0F0F 100%)",
              border: "1px solid #525252",
              borderLeft: "4px solid #c1f11d",
              borderRadius: "24px",
              padding: "32px 36px",
              marginBottom: "40px",
            }}
          >
            <h3 style={{ fontWeight: 600, color: "#c1f11d", marginBottom: "12px", fontSize: "17px" }}>Evaluator Summary</h3>
            <p style={{ fontSize: "16px", color: "#ccc", lineHeight: "1.6", margin: 0 }}>{score.summary}</p>
          </div>

          {/* Actions */}
          <div style={{ display: "flex", justifyContent: "center", gap: "14px" }}>
            <button
              onClick={handleReset}
              style={{
                borderRadius: "14px",
                backgroundColor: "#141414",
                color: "#c1f11d",
                padding: "16px 34px",
                fontSize: "16px",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                transition: "transform 0.2s, box-shadow 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.03)";
                e.currentTarget.style.boxShadow = "0 0 24px rgba(193,241,29,0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              Try Another Topic
            </button>
            <a
              href="/dashboard"
              style={{
                borderRadius: "14px",
                backgroundColor: "#eae9e9",
                color: "#333",
                padding: "16px 34px",
                fontSize: "16px",
                fontWeight: 600,
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                transition: "transform 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.03)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
              }}
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      )}

      {/* Keyframe animations */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>

      {/* Footer */}
      <footer style={{ backgroundColor: "#141414", position: "relative", overflow: "hidden", padding: "60px 0 40px" }}>
        <img src="/assets/InVision U GRADIENT.svg" alt="" style={{ position: "absolute", bottom: "-30px", left: "50%", transform: "translateX(-50%)", width: "clamp(600px, 80vw, 1200px)", opacity: 0.08, pointerEvents: "none" }} />
        <div style={{ position: "relative", zIndex: 1, maxWidth: "1200px", margin: "0 auto", padding: "0 40px", textAlign: "center" }}>
          <img src="/assets/InVision U white.png" alt="inVision U" style={{ width: "169px", height: "auto", margin: "0 auto 16px" }} />
          <p style={{ fontSize: "14px", color: "#666", marginBottom: "24px" }}>AI-Assisted Evaluation System &mdash; All final admission decisions are made by the human admissions committee.</p>
          <div style={{ display: "flex", justifyContent: "center", gap: "32px", marginBottom: "32px" }}>
            {[{ href: "/", label: "Home" }, { href: "/#apply", label: "Apply" }, { href: "/teach", label: "Teaching Challenge" }, { href: "/dashboard", label: "Dashboard" }].map((link) => (
              <a key={link.label} href={link.href} style={{ fontSize: "14px", color: "#888", textDecoration: "none", transition: "color 0.2s" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#c1f11d")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#888")}
              >{link.label}</a>
            ))}
          </div>
          <div style={{ borderTop: "1px solid #333", paddingTop: "20px", fontSize: "12px", color: "#555" }}>Powered by inDrive &middot; Built for Decentrathon 5.0</div>
        </div>
      </footer>
    </div>
  );
}
