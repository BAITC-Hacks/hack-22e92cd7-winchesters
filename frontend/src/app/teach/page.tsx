"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

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
  const { user } = useAuth();
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
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    api.feynman.topics().then(setTopics).catch(() => {});
    // Auto-fill candidate ID from application form, or generate one
    if (typeof window !== "undefined") {
      const savedId = window.localStorage.getItem("invisionu_candidate_id");
      const savedName = window.localStorage.getItem("invisionu_candidate_name");
      if (savedId) setCandidateId(savedId);
      else if (savedName) setCandidateId(savedName);
      else setCandidateId(`guest-${Date.now()}`);
    }
  }, []);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Scroll only within the chat container, not the page
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
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
    if (!selectedTopic) return;
    setError(null);
    setSending(true);
    try {
      const res = await api.feynman.start(candidateId.trim(), selectedTopic);
      setSessionId(res.session_id);
      setMessages([{ role: "assistant", content: res.first_message }]);
      setMessageCount(1);
      setPhase("teaching");
      // Scroll to top so user sees the chat, not the footer
      window.scrollTo({ top: 0, behavior: "instant" });
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
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scoring failed");
      setPhase("teaching");
    }
  }

  function handleReset() {
    setPhase("setup");
    window.scrollTo({ top: 0, behavior: "instant" });
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
    <div style={{ minHeight: "100vh", backgroundColor: "#ffffff" }}>
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
          {/* Hero area — two-column with How it works inside left */}
          <div
            style={{
              backgroundColor: "#ffffff",
              padding: "48px 60px 40px",
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: "40px",
              maxWidth: "1400px",
              margin: "0 auto",
            }}
          >
            {/* Left column */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <h1 style={{ fontSize: "clamp(40px, 5vw, 64px)", fontWeight: 800, color: "#141414", margin: 0, lineHeight: 1.15 }}>
                Feynman Teaching{" "}
                <span style={{ position: "relative", display: "inline-block" }}>
                  <span
                    style={{
                      position: "absolute",
                      left: "-6px",
                      right: "-6px",
                      top: "-2px",
                      bottom: "-2px",
                      backgroundColor: "#c1f11d",
                      zIndex: 0,
                      borderRadius: "4px",
                    }}
                  />
                  <span style={{ position: "relative", zIndex: 1 }}>Challenge</span>
                </span>
              </h1>
              <p style={{ fontSize: "20px", color: "#555", marginTop: "20px", lineHeight: 1.6, maxWidth: "720px" }}>
                <span style={{ whiteSpace: "nowrap" }}>Prove you understand a concept by teaching it to Arman — a curious</span><br />10-year-old AI student. The better Arman understands, the higher your score.
              </p>

              {/* How it works — inside left column */}
              <div
                style={{
                  backgroundColor: "#ffffff",
                  border: "2px solid #d7d7d7",
                  borderRadius: "16px",
                  padding: "16px",
                  marginTop: "24px",
                }}
              >
                <h3 style={{ fontWeight: 600, color: "#141414", marginBottom: "16px", fontSize: "20px" }}>How it works</h3>
                <div style={{ display: "flex", gap: "8px" }}>
                  {[
                    "Pick a topic and teach it to Arman in a chat",
                    "After 4-8 exchanges, finish the session",
                    "Arman takes a quiz. Your score = his understanding",
                  ].map((text, i) => (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        backgroundColor: "#141414",
                        borderRadius: "10px",
                        padding: "16px 14px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      <span
                        style={{
                          backgroundColor: "#c1f11d",
                          color: "#141414",
                          fontWeight: 700,
                          fontSize: "20px",
                          width: "36px",
                          height: "36px",
                          borderRadius: "8px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </span>
                      <span style={{ fontSize: "16px", color: "#ffffff", lineHeight: 1.4 }}>{text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {/* Right column — teacher photo */}
            <div style={{ flexShrink: 0 }}>
              <img
                src="/assets/Photo of the Teacher.png"
                alt="Teacher"
                style={{ width: "clamp(300px, 30vw, 500px)", height: "auto", objectFit: "cover", borderRadius: "20px" }}
              />
            </div>
          </div>

          <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "0 40px" }}>
            {/* Topics section */}
            <div style={{ marginBottom: "56px", position: "relative" }}>
              {/* Dark header strip */}
              <div
                style={{
                  backgroundColor: "#141414",
                  borderRadius: "24px 24px 0 0",
                  padding: "22px 24px 50px",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <img src="/assets/Dots.png" alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.3, pointerEvents: "none" }} />
                <h2 style={{ position: "relative", zIndex: 1, fontSize: "clamp(24px, 2.5vw, 34px)", fontWeight: 700, color: "#c1f11d", margin: 0, textAlign: "center" }}>
                  Choose a topic to teach
                </h2>
              </div>

              {/* White card with topics — flush with dark strip edges */}
              <div
                style={{
                  backgroundColor: "#ffffff",
                  border: "2px solid #d7d7d7",
                  borderRadius: "0 0 24px 24px",
                  padding: "20px",
                  position: "relative",
                  zIndex: 1,
                }}
              >
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px", marginBottom: "16px" }}>
                  {topics.map((t, idx) => {
                    const isSelected = selectedTopic === t.id;
                    return (
                      <button
                        key={t.id}
                        onClick={() => setSelectedTopic(t.id)}
                        style={{
                          textAlign: "center",
                          borderRadius: "16px",
                          padding: "20px",
                          height: "100px",
                          cursor: "pointer",
                          transition: "transform 0.2s, box-shadow 0.2s",
                          backgroundColor: isSelected ? "#c1f11d" : "#eae9e9",
                          border: "none",
                          display: "flex",
                          gap: "12px",
                          alignItems: "center",
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.transform = "translateY(-2px)";
                            e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.1)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = "translateY(0)";
                          e.currentTarget.style.boxShadow = "none";
                        }}
                      >
                        <span
                          style={{
                            fontSize: "30px",
                            fontWeight: 700,
                            color: isSelected ? "#141414" : "#999",
                            lineHeight: 1,
                            flexShrink: 0,
                          }}
                        >
                          {idx + 1}
                        </span>
                        <div style={{ minWidth: 0, textAlign: "left" }}>
                          <p style={{ fontSize: "18px", fontWeight: 700, color: "#141414", margin: 0 }}>{t.title}</p>
                          <p style={{ fontSize: "16px", color: isSelected ? "#333" : "#666", margin: "4px 0 0 0" }}>{t.description}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {error && (
                  <div style={{ borderRadius: "14px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", padding: "14px 20px", fontSize: "16px", color: "#b91c1c", marginBottom: "20px" }}>
                    {error}
                  </div>
                )}

                <button
                  onClick={handleStart}
                  disabled={!selectedTopic || sending}
                  style={{
                    width: "100%",
                    borderRadius: "20px",
                    backgroundColor: "#141414",
                    color: "#c1f11d",
                    padding: "20px",
                    fontSize: "22px",
                    fontWeight: 600,
                    border: "none",
                    cursor: !selectedTopic || sending ? "not-allowed" : "pointer",
                    opacity: !selectedTopic || sending ? 0.5 : 1,
                    transition: "transform 0.2s, box-shadow 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    if (selectedTopic && !sending) {
                      e.currentTarget.style.transform = "scale(1.02)";
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
          </div>
        </>
      )}

      {/* ── Teaching Phase ──────────────────────────────────── */}
      {phase === "teaching" && (
        <div style={{ position: "relative", overflow: "visible" }}>
          {/* Brush background — full viewport width */}
          <div style={{ position: "absolute", top: "40px", left: "50%", transform: "translateX(-50%)", width: "99vw", height: "130%", overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
            <img src="/assets/Brush Background.png" alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
          <div style={{ position: "relative", zIndex: 1, maxWidth: "1400px", margin: "0 auto", padding: "32px 40px 56px" }}>

          {/* Header */}
          <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 700, color: "#141414", margin: 0 }}>
                Teaching:{" "}
                <span style={{ position: "relative", display: "inline" }}>
                  <span style={{ position: "absolute", left: "-6px", right: "-6px", top: "-2px", bottom: "-2px", backgroundColor: "#c1f11d", zIndex: 0, borderRadius: "4px" }} />
                  <span style={{ position: "relative", zIndex: 1 }}>{topicObj?.title}</span>
                </span>
              </h2>
              <p style={{ fontSize: "16px", color: "#888", margin: "6px 0 0 0" }}>
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
              position: "relative",
              zIndex: 1,
              backgroundColor: "#ffffff",
              borderRadius: "20px",
              border: "2px solid #d7d7d7",
              overflow: "hidden",
            }}
          >
            <div ref={chatContainerRef} style={{ height: "500px", overflowY: "auto", padding: "30px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {messages.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                    }}
                  >
                    {m.role === "assistant" ? (
                      <div style={{ maxWidth: "70%" }}>
                        <div style={{ backgroundColor: "#c1f11d", display: "inline-flex", padding: "0 10px", marginBottom: "6px", borderRadius: "4px" }}>
                          <span style={{ fontSize: "14px", fontWeight: 600, color: "#141414", lineHeight: "28px" }}>Arman (10 y.o.)</span>
                        </div>
                        <div style={{ backgroundColor: "#f0f4ee", borderRadius: "20px 20px 20px 0", padding: "18px 22px", fontSize: "16px", lineHeight: 1.5, color: "#141414" }}>
                          {m.content}
                        </div>
                      </div>
                    ) : (
                      <div style={{ maxWidth: "70%", backgroundColor: "#c1f11d", borderRadius: "20px 20px 0 20px", padding: "18px 22px", fontSize: "16px", lineHeight: 1.5, color: "#141414", boxShadow: "0 0 0 1.5px rgba(219,222,223,0.44)" }}>
                        {m.content}
                      </div>
                    )}
                  </div>
                ))}
                {sending && (
                  <div style={{ display: "flex", justifyContent: "flex-start" }}>
                    <div style={{ maxWidth: "70%" }}>
                      <div style={{ backgroundColor: "#c1f11d", display: "inline-flex", padding: "0 10px", marginBottom: "6px", borderRadius: "4px" }}>
                        <span style={{ fontSize: "14px", fontWeight: 600, color: "#141414", lineHeight: "28px" }}>Arman (10 y.o.)</span>
                      </div>
                      <div style={{ backgroundColor: "#f0f4ee", borderRadius: "20px 20px 20px 0", padding: "18px 22px", fontSize: "16px", color: "#999", animation: "pulse 1.5s ease-in-out infinite" }}>
                        Arman is thinking...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Separator */}
            <div style={{ height: "2px", backgroundColor: "#d7d7d7" }} />

            {/* Input */}
            <div style={{ padding: "16px 24px", display: "flex", alignItems: "center" }}>
              <div style={{ flex: 1, backgroundColor: "#eae9e9", borderRadius: "20px", display: "flex", alignItems: "center", padding: "0 6px 0 20px", height: "56px" }}>
                <input
                  style={{
                    flex: 1,
                    border: "none",
                    backgroundColor: "transparent",
                    padding: "0",
                    fontSize: "16px",
                    outline: "none",
                    color: "#141414",
                  }}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  placeholder={mustFinish ? "Session complete — scoring..." : "Teach Arman..."}
                  disabled={sending || mustFinish}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || sending || mustFinish}
                  style={{
                    borderRadius: "10px",
                    backgroundColor: "#141414",
                    color: "#c1f11d",
                    padding: "10px 24px",
                    fontSize: "16px",
                    fontWeight: 600,
                    border: "none",
                    cursor: !input.trim() || sending ? "not-allowed" : "pointer",
                    opacity: !input.trim() || sending ? 0.5 : 1,
                    height: "44px",
                    whiteSpace: "nowrap",
                  }}
                >
                  Send
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div style={{ borderRadius: "14px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", padding: "14px 20px", fontSize: "16px", color: "#b91c1c", marginTop: "20px" }}>
              {error}
            </div>
          )}
          </div>
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
      <footer style={{ position: "relative", overflow: "hidden", padding: 0 }}>
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
