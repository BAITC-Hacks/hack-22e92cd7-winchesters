"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import type {
  Education,
  Extracurricular,
  Project,
  Essay,
  Application,
} from "@/lib/types";

/* ── Shared helpers ────────────────────────────────────────────────── */

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xl font-semibold text-gray-900 border-b border-gray-200 pb-3 mb-5">
      {children}
    </h2>
  );
}

function Label({
  htmlFor,
  children,
  required,
}: {
  htmlFor: string;
  children: React.ReactNode;
  required?: boolean;
}) {
  return (
    <label htmlFor={htmlFor} className="block text-base font-medium text-gray-700 mb-1.5">
      {children}
      {required && <span className="text-red-500 ml-0.5">*</span>}
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-[#c1f11d] focus:ring-1 focus:ring-[#c1f11d] outline-none transition";
const btnSecondary =
  "rounded-lg border border-gray-300 px-4 py-2 text-base font-medium text-gray-700 hover:bg-gray-50 transition";

const SCHOOL_TYPES = [
  { value: "public", label: "Public school" },
  { value: "village", label: "Village school" },
  { value: "lyceum", label: "Lyceum" },
  { value: "gymnasium", label: "Gymnasium" },
  { value: "specialized", label: "Specialized school" },
  { value: "private", label: "Private school" },
  { value: "international", label: "International school" },
];

const ESSAY_PROMPTS = [
  "Describe a challenge you overcame and what it taught you about leadership.",
  "Tell us about a time you made a meaningful impact in your community.",
  "What drives your passion for learning, and how has it shaped your goals?",
  "Describe a failure and what you learned from it.",
];


const PROGRAMS = [
  { num: "F", title: "Foundation Year", tag: "Foundation", href: "https://www.invisionu.education/foundation" },
  { num: 1, title: "Digital Media and Marketing", tag: "Media", href: "https://cdn.prod.website-files.com/6798ba0f2cbf12d58d36f439/695bc86bf627f6d7ca996221_Admission%20manuals%20for%20undergraduate%20program%20Digital%20Media%20and%20Marketing.pdf" },
  { num: 2, title: "Public Policy and Development", tag: "Policy", href: "https://cdn.prod.website-files.com/6798ba0f2cbf12d58d36f439/695bc86b8344d1d7f9fad54c_Admission%20manuals%20for%20undergraduate%20program%20Public%20Policy%20and%20Development.pdf" },
  { num: 3, title: "Sociology: Leadership and Innovation", tag: "Sociology", href: "https://cdn.prod.website-files.com/6798ba0f2cbf12d58d36f439/695bc86b3ef597081d662926_Admission%20manuals%20for%20undergraduate%20program%20Sociology%20Leadership%20and%20Innovation.pdf" },
  { num: 4, title: "Innovative IT Product Design and Development", tag: "IT & Design", href: "https://cdn.prod.website-files.com/6798ba0f2cbf12d58d36f439/695bc86bb255c70ba5396d18_Admission%20manuals%20for%20undergraduate%20program%20Innovative%20IT%20Product%20Design%20%20and%20Development.pdf" },
  { num: 5, title: "Creative Engineering", tag: "Engineering", href: "https://cdn.prod.website-files.com/6798ba0f2cbf12d58d36f439/695bc86b61a2bc0375400381_Admission%20manuals%20for%20undergraduate%20program%20Creative%20Engineering.pdf" },
];


/* ── Main page ─────────────────────────────────────────────────────── */

export default function LandingPage() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Multi-step form
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedProgram, setSelectedProgram] = useState("Creative Engineering");
  const [videoLink, setVideoLink] = useState("");

  // Personal
  const [name, setName] = useState("");
  const [age, setAge] = useState(17);

  // Education
  const [schoolType, setSchoolType] = useState("public");
  const [gpa, setGpa] = useState("");
  const [achievements, setAchievements] = useState<string[]>([""]);
  const [yearsOfStudy, setYearsOfStudy] = useState(11);

  // Extracurriculars
  const [extracurriculars, setExtracurriculars] = useState<
    { activity: string; duration_months: string; role: string }[]
  >([{ activity: "", duration_months: "", role: "" }]);

  // Projects
  const [projects, setProjects] = useState<
    { name: string; role: string; impact: string }[]
  >([{ name: "", role: "", impact: "" }]);

  // Languages & skills
  const [languages, setLanguages] = useState("");
  const [skills, setSkills] = useState("");

  // Essay
  const [essayPrompt, setEssayPrompt] = useState(ESSAY_PROMPTS[0]);
  const [essayText, setEssayText] = useState("");

  // Optional
  const [recommendation, setRecommendation] = useState("");

  /* ── Dynamic list helpers ──────────────────────────────────────── */

  function addAchievement() {
    setAchievements([...achievements, ""]);
  }
  function updateAchievement(i: number, v: string) {
    const copy = [...achievements];
    copy[i] = v;
    setAchievements(copy);
  }
  function removeAchievement(i: number) {
    setAchievements(achievements.filter((_, idx) => idx !== i));
  }

  function addExtracurricular() {
    setExtracurriculars([
      ...extracurriculars,
      { activity: "", duration_months: "", role: "" },
    ]);
  }
  function updateEC(i: number, field: string, v: string) {
    const copy = [...extracurriculars];
    copy[i] = { ...copy[i], [field]: v };
    setExtracurriculars(copy);
  }
  function removeEC(i: number) {
    setExtracurriculars(extracurriculars.filter((_, idx) => idx !== i));
  }

  function addProject() {
    setProjects([...projects, { name: "", role: "", impact: "" }]);
  }
  function updateProject(i: number, field: string, v: string) {
    const copy = [...projects];
    copy[i] = { ...copy[i], [field]: v };
    setProjects(copy);
  }
  function removeProject(i: number) {
    setProjects(projects.filter((_, idx) => idx !== i));
  }

  /* ── Submit ────────────────────────────────────────────────────── */

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const education: Education = {
        school_type: schoolType,
        gpa: parseFloat(gpa) || 0,
        academic_achievements: achievements.filter((a) => a.trim()),
        years_of_study: yearsOfStudy,
      };

      const ecList: Extracurricular[] = extracurriculars
        .filter((ec) => ec.activity.trim())
        .map((ec) => ({
          activity: ec.activity,
          duration_months: parseInt(ec.duration_months) || 0,
          role: ec.role,
        }));

      const projList: Project[] = projects
        .filter((p) => p.name.trim())
        .map((p) => ({
          name: p.name,
          role: p.role,
          impact: p.impact,
        }));

      const application: Application = {
        education,
        extracurriculars: ecList,
        projects: projList,
        languages: languages
          .split(",")
          .map((l) => l.trim())
          .filter(Boolean),
        skills: skills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };

      const essay: Essay = {
        prompt: essayPrompt,
        text: essayText,
        word_count: essayText.split(/\s+/).filter(Boolean).length,
      };

      const created = await api.candidates.create({
        name,
        age,
        application,
        essay,
        interview_transcript: "",
        recommendation_summary: recommendation,
      });

      // Store the new candidate ID so Teaching Challenge can link the score
      if (typeof window !== "undefined") {
        window.localStorage.setItem("invisionu_candidate_id", created.id);
        window.localStorage.setItem("invisionu_candidate_name", name);
      }

      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  const wordCount = essayText.split(/\s+/).filter(Boolean).length;

  /* ── Scroll reveal ──────────────────────────────────────────── */
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add("visible");
      }),
      { threshold: 0.1 }
    );
    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  /* ── Scroll progress bar ────────────────────────────────────── */
  const progressRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function onScroll() {
      if (!progressRef.current) return;
      const pct = window.scrollY / (document.body.scrollHeight - window.innerHeight);
      progressRef.current.style.width = `${Math.min(pct * 100, 100)}%`;
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  /* ── Success screen ────────────────────────────────────────────── */

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Application Submitted!</h1>
          <p className="text-gray-600" style={{ marginBottom: "8px" }}>
            Your application has been received. Now for the final step — let&apos;s see how you explain things!
          </p>
          <p className="text-gray-500 text-sm" style={{ marginBottom: "24px" }}>
            The Teaching Challenge helps us understand your communication skills, patience, and ability to simplify complex ideas.
          </p>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            <a
              href="/teach"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#141414",
                color: "#c1f11d",
                borderRadius: "12px",
                padding: "14px 32px",
                fontSize: "16px",
                fontWeight: 600,
                textDecoration: "none",
                transition: "transform 0.2s, box-shadow 0.2s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "scale(1.03)"; (e.currentTarget as HTMLElement).style.boxShadow = "0 0 20px rgba(193,241,29,0.3)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = "scale(1)"; (e.currentTarget as HTMLElement).style.boxShadow = "none"; }}
            >
              Start Teaching Challenge
            </a>
            <button
              onClick={() => {
                setSuccess(false);
                setName("");
                setAge(17);
                setGpa("");
                setAchievements([""]);
                setExtracurriculars([{ activity: "", duration_months: "", role: "" }]);
                setProjects([{ name: "", role: "", impact: "" }]);
                setLanguages("");
                setSkills("");
                setEssayText("");
                setRecommendation("");
                setVideoLink("");
                setCurrentStep(0);
              }}
              style={{ backgroundColor: "#eae9e9", color: "#141414", borderRadius: "12px", padding: "14px 24px", fontSize: "14px", fontWeight: 500, border: "none", cursor: "pointer" }}
            >
              Submit Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ── Render ────────────────────────────────────────────────────── */

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#ffffff" }}>
      {/* Scroll progress bar */}
      <div
        ref={progressRef}
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "3px",
          backgroundColor: "#c1f11d",
          zIndex: 9999,
          width: "0%",
          transition: "width 0.1s linear",
        }}
      />

      {/* ══════ NAV ══════ */}
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

      {/* ══════ HERO ══════ */}
      <section style={{ background: "linear-gradient(180deg, #ffffff 0%, #f8f8f4 50%, #f0f4e8 100%)", position: "relative", overflow: "hidden" }}>
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            padding: "80px 60px 0",
          }}
        >
          {/* Heading — 2 lines */}
          <h1
            className="reveal reveal-up"
            style={{
              fontSize: "clamp(40px, 4.5vw, 76px)",
              fontWeight: 700,
              color: "#141414",
              lineHeight: 1.08,
              marginBottom: "40px",
            }}
          >
            <span style={{ whiteSpace: "nowrap" }}>Empowering those who are</span><br />
            <span>ready to{" "}</span>
            <span style={{ position: "relative", display: "inline", whiteSpace: "nowrap" }}>
              <span style={{ position: "relative", zIndex: 1 }}>change the world.</span>
              <span
                style={{
                  position: "absolute",
                  top: "-4px",
                  bottom: "-4px",
                  left: "-8px",
                  right: "-8px",
                  backgroundColor: "#c1f11d",
                  zIndex: 0,
                  borderRadius: "4px",
                  transformOrigin: "left",
                  animation: "highlightSlide 0.8s ease-out 0.5s both",
                }}
              />
            </span>
          </h1>

          {/* Subtitle */}
          <p
            className="reveal reveal-up delay-1"
            style={{
              maxWidth: "800px",
              fontSize: "clamp(18px, 2vw, 24px)",
              color: "#555",
              lineHeight: 1.6,
              marginBottom: "40px",
            }}
          >
            Join a global network of future leaders at <strong style={{ color: "#141414" }}>inVision U</strong> — where ideas meet action, and education drives real change.
          </p>

          {/* Buttons — left aligned */}
          <div
            className="reveal reveal-up delay-2"
            style={{
              display: "flex",
              justifyContent: "flex-start",
              gap: "12px",
              marginBottom: "32px",
            }}
          >
              <a
                href="#apply"
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "#141414",
                  color: "#ffffff",
                  borderRadius: "12px",
                  padding: "18px 40px",
                  fontSize: "20px",
                  fontWeight: 500,
                  textDecoration: "none",
                  overflow: "hidden",
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "scale(1.04)";
                  (e.currentTarget as HTMLElement).style.boxShadow =
                    "0 0 30px rgba(193, 241, 29, 0.3), 0 8px 25px rgba(0,0,0,0.2)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = "scale(1)";
                  (e.currentTarget as HTMLElement).style.boxShadow = "none";
                }}
              >
                <img
                  src="/assets/Brush Grey.png"
                  alt=""
                  style={{
                    position: "absolute",
                    inset: 0,
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    opacity: 0.35,
                    pointerEvents: "none",
                  }}
                />
                <span style={{ position: "relative", zIndex: 1 }}>Start your journey</span>
              </a>
              <a
                href="#about"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  backgroundColor: "#eae9e9",
                  color: "#141414",
                  borderRadius: "12px",
                  padding: "18px 40px",
                  fontSize: "20px",
                  fontWeight: 500,
                  textDecoration: "none",
                  transition: "background-color 0.2s, transform 0.2s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "#ddd";
                  (e.currentTarget as HTMLElement).style.transform = "scale(1.03)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "#eae9e9";
                  (e.currentTarget as HTMLElement).style.transform = "scale(1)";
                }}
              >
                Explore programs
              </a>
            </div>

          {/* Powered by */}
          <div
            className="reveal reveal-up delay-2"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              opacity: 0.4,
              marginBottom: "40px",
            }}
          >
            <span style={{ fontSize: "16px", color: "#141414" }}>Powered by</span>
            <img
              src="/assets/InDrive LOGO.svg"
              alt="inDrive"
              style={{ width: "100px", height: "auto" }}
            />
          </div>
        </div>

        {/* Brush Lime — full width */}
        <img
          src="/assets/Brush Lime.png"
          alt=""
          style={{ width: "100%", display: "block" }}
        />
      </section>

      {/* ══════ MARQUEE ══════ */}
      <section style={{ backgroundColor: "#141414" }}>
        <div style={{ overflow: "hidden", padding: "20px 0" }}>
          <div
            className="animate-marquee-left"
            style={{ alignItems: "center", gap: "60px", width: "max-content" }}
          >
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} style={{ display: "contents" }}>
                <img src="/assets/InVision U white.png" alt="inVision U" style={{ width: "169.33px", height: "27.86px", flexShrink: 0 }} />
                <img src="/assets/InDrive.png" alt="iD" style={{ width: "48px", height: "48px", flexShrink: 0 }} />
                <span style={{ fontWeight: 600, color: "#ffffff", fontSize: "clamp(24px, 3vw, 39px)", whiteSpace: "nowrap", flexShrink: 0 }}>Grow with us</span>
                <img src="/assets/InDrive.png" alt="iD" style={{ width: "48px", height: "48px", flexShrink: 0 }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════ PROGRAMS ══════ */}
      <section id="about" style={{ backgroundColor: "#fafafa", padding: "60px 0" }}>
        <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "0 30px" }}>
          {/* Dark banner with title + fanned cards */}
          <div
            className="reveal reveal-up"
            style={{
              position: "relative",
              borderRadius: "24px",
              backgroundColor: "#141414",
              overflow: "visible",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              minHeight: "420px",
              border: "1px solid rgba(193, 241, 29, 0.1)",
            }}
          >
            {/* Dots background */}
            <img
              src="/assets/Dots.png"
              alt=""
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.5, pointerEvents: "none", borderRadius: "24px" }}
            />
            {/* Title */}
            <p style={{ position: "relative", zIndex: 1, fontWeight: 700, color: "#ffffff", fontSize: "clamp(32px, 4vw, 56px)", lineHeight: 1.15, maxWidth: "520px", padding: "56px" }}>
              Explore your academic path and find what fits you
            </p>
            {/* Fanned cards — animate on scroll, spread on hover */}
            <div
              className="card-fan"
              style={{
                position: "relative",
                width: "480px",
                height: "340px",
                flexShrink: 0,
                marginRight: "50px",
              }}
            >
              {PROGRAMS.map((prog, i) => {
                const rotations = [-12, -8, -4, 0, 4, 8];
                const stackedLeft = [40, 52, 64, 76, 88, 100];
                const stackedTop = [35, 28, 21, 14, 7, 0];
                return (
                  <a
                    key={prog.num}
                    href={prog.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="card-fan-item"
                    style={{
                      position: "absolute",
                      width: "250px",
                      height: "310px",
                      left: `${stackedLeft[i]}px`,
                      top: `${stackedTop[i]}px`,
                      transform: `rotate(${rotations[i]}deg)`,
                      zIndex: i + 1,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      padding: "24px 22px 32px",
                      borderRadius: "24px",
                      border: "1.3px solid #525252",
                      background: prog.num === "F"
                        ? "linear-gradient(180deg, #1a2a0a 0%, #0a1505 100%)"
                        : "linear-gradient(180deg, rgba(37,37,37,1) 0%, rgba(15,15,15,1) 100%)",
                      textDecoration: "none",
                      transition: "left 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), top 0.4s ease, box-shadow 0.3s, border-color 0.3s",
                      cursor: "pointer",
                    }}
                  >
                    <div>
                      <div style={{ width: "48px", height: "48px", backgroundColor: "#c1f11d", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "22px", color: "#141414", flexShrink: 0, boxShadow: "0 0 15px rgba(193,241,29,0.2)", marginBottom: "8px" }}>
                        {prog.num}
                      </div>
                      <div style={{ fontSize: "12px", fontWeight: 600, color: "rgba(193,241,29,0.6)", textTransform: "uppercase", letterSpacing: "1px" }}>
                        {prog.tag}
                      </div>
                    </div>
                    <div style={{ fontWeight: 500, color: "#ffffff", fontSize: "20px", lineHeight: 1.25 }}>
                      {prog.title}
                    </div>
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ══════ APPLICATION FORM ══════ */}
      <section id="apply" style={{ backgroundColor: "#f5f5f5", paddingBottom: "60px" }}>
        {/* Application header group — same style as dashboard */}
        <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "12px 40px 0", position: "relative" }}>
          {/* Dark banner with dots */}
          <div style={{ backgroundColor: "#141414", borderRadius: "24px", overflow: "hidden", position: "relative", padding: "36px 40px 70px", textAlign: "center" }}>
            <img src="/assets/Dots.png" alt="" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.3, pointerEvents: "none" }} />
            <h2 style={{ position: "relative", zIndex: 1, fontSize: "36px", fontWeight: 700, color: "#c1f11d", margin: 0, textTransform: "uppercase", letterSpacing: "2px" }}>Application</h2>
          </div>
          {/* Navigation bar — overlapping bottom of dark banner, full width */}
          <div style={{ position: "relative", zIndex: 2, marginTop: "-36px", padding: "0 20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "12px 16px", backgroundColor: "#ffffff", borderRadius: "20px", border: "2px solid #d7d7d7" }}>
              {["Personal Information", "Education", "Essay & Motivation", "Extracurriculars & Projects", "Review & Submit"].map((tab, i) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setCurrentStep(i)}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "10px 16px",
                    fontSize: "15px",
                    fontWeight: 700,
                    color: currentStep === i ? "#c1f11d" : "#141414",
                    backgroundColor: currentStep === i ? "#141414" : (currentStep > i ? "#e8f5d0" : "#eae9e9"),
                    border: "none",
                    borderRadius: "16px",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    whiteSpace: "nowrap",
                  }}
                  onMouseEnter={(e) => {
                    if (currentStep !== i) (e.currentTarget as HTMLElement).style.backgroundColor = "#ddd";
                  }}
                  onMouseLeave={(e) => {
                    if (currentStep !== i) (e.currentTarget as HTMLElement).style.backgroundColor = "#eae9e9";
                  }}
                >
                  <span style={{
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    width: "36px", height: "36px", borderRadius: "50%", flexShrink: 0,
                    backgroundColor: currentStep === i ? "#c1f11d" : (currentStep > i ? "#c1f11d" : "#141414"),
                    color: currentStep === i ? "#141414" : (currentStep > i ? "#141414" : "#fff"),
                    fontSize: currentStep > i ? "18px" : "16px", fontWeight: 700,
                  }}>{currentStep > i ? "\u2713" : i + 1}</span>
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Two-column layout */}
        <div style={{ maxWidth: "1200px", margin: "24px auto 0", padding: "0 40px", display: "flex", gap: "24px", alignItems: "flex-start" }}>

          {/* Main form area (~70%) */}
          <div style={{ flex: "1 1 70%", minWidth: 0 }}>
            <form onSubmit={handleSubmit}>
              {error && (
                <div style={{ borderRadius: "12px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", padding: "12px 16px", fontSize: "14px", color: "#b91c1c", marginBottom: "16px" }}>
                  {error}
                </div>
              )}

              {/* Step 1: Personal Information */}
              <div style={{ display: currentStep === 0 ? "block" : "none" }}>
                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px", marginBottom: "16px" }}>
                  <SectionTitle>Personal Information</SectionTitle>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                    <div>
                      <Label htmlFor="name" required>Full Name</Label>
                      <input
                        id="name"
                        className={inputClass}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Aigerim Tastanova"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="age">Age</Label>
                      <input
                        id="age"
                        type="number"
                        className={inputClass}
                        value={age}
                        onChange={(e) => setAge(parseInt(e.target.value) || 17)}
                        min={14}
                        max={25}
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="program" required>Program</Label>
                    <select
                      id="program"
                      className={inputClass}
                      value={selectedProgram}
                      onChange={(e) => setSelectedProgram(e.target.value)}
                    >
                      {PROGRAMS.map((p) => (
                        <option key={p.title} value={p.title}>{p.title}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Step 2: Education */}
              <div style={{ display: currentStep === 1 ? "block" : "none" }}>
                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px", marginBottom: "16px" }}>
                  <SectionTitle>Education</SectionTitle>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                    <div>
                      <Label htmlFor="schoolType" required>School Type</Label>
                      <select
                        id="schoolType"
                        className={inputClass}
                        value={schoolType}
                        onChange={(e) => setSchoolType(e.target.value)}
                      >
                        {SCHOOL_TYPES.map((st) => (
                          <option key={st.value} value={st.value}>{st.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="gpa" required>GPA (0-4.0)</Label>
                      <input
                        id="gpa"
                        type="number"
                        step="0.1"
                        min="0"
                        max="4.0"
                        className={inputClass}
                        value={gpa}
                        onChange={(e) => setGpa(e.target.value)}
                        placeholder="3.8"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="years">Years of Study</Label>
                      <input
                        id="years"
                        type="number"
                        className={inputClass}
                        value={yearsOfStudy}
                        onChange={(e) => setYearsOfStudy(parseInt(e.target.value) || 11)}
                        min={9}
                        max={13}
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: "20px" }}>
                    <Label htmlFor="ach-0">Academic Achievements</Label>
                    {achievements.map((ach, i) => (
                      <div key={i} style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
                        <input
                          id={`ach-${i}`}
                          className={inputClass}
                          value={ach}
                          onChange={(e) => updateAchievement(i, e.target.value)}
                          placeholder="e.g. National Math Olympiad - 2nd place"
                        />
                        {achievements.length > 1 && (
                          <button type="button" onClick={() => removeAchievement(i)} style={{ color: "#f87171", background: "none", border: "none", fontSize: "20px", cursor: "pointer", padding: "0 4px" }}>&times;</button>
                        )}
                      </div>
                    ))}
                    <button type="button" onClick={addAchievement} className={`${btnSecondary}`} style={{ marginTop: "4px" }}>
                      + Add Achievement
                    </button>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                    <div>
                      <Label htmlFor="languages" required>Languages (comma-separated)</Label>
                      <input
                        id="languages"
                        className={inputClass}
                        value={languages}
                        onChange={(e) => setLanguages(e.target.value)}
                        placeholder="Kazakh, Russian, English"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="skills">Skills (comma-separated)</Label>
                      <input
                        id="skills"
                        className={inputClass}
                        value={skills}
                        onChange={(e) => setSkills(e.target.value)}
                        placeholder="public speaking, mathematics, writing"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 3: Essay & Motivation */}
              <div style={{ display: currentStep === 2 ? "block" : "none" }}>
                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px", marginBottom: "16px" }}>
                  <SectionTitle>Essay &amp; Motivation</SectionTitle>
                  <div style={{ marginBottom: "20px" }}>
                    <Label htmlFor="essayPrompt" required>Essay Prompt</Label>
                    <select
                      id="essayPrompt"
                      className={inputClass}
                      value={essayPrompt}
                      onChange={(e) => setEssayPrompt(e.target.value)}
                    >
                      {ESSAY_PROMPTS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                  <div style={{ marginBottom: "20px" }}>
                    <Label htmlFor="essayText" required>Your Essay</Label>
                    <textarea
                      id="essayText"
                      className={inputClass}
                      style={{ minHeight: "220px", resize: "vertical" }}
                      value={essayText}
                      onChange={(e) => setEssayText(e.target.value)}
                      placeholder="Write your essay here. Be authentic — we value your real voice and story..."
                      required
                    />
                    <div style={{ marginTop: "6px", display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#999" }}>
                      <span>
                        {wordCount} word{wordCount !== 1 ? "s" : ""}
                        {wordCount > 0 && wordCount < 200 && (
                          <span style={{ color: "#d97706", marginLeft: "8px" }}>Aim for at least 200 words</span>
                        )}
                        {wordCount >= 200 && wordCount <= 1000 && (
                          <span style={{ color: "#059669", marginLeft: "8px" }}>Good length</span>
                        )}
                        {wordCount > 1000 && (
                          <span style={{ color: "#d97706", marginLeft: "8px" }}>Consider trimming to under 1000 words</span>
                        )}
                      </span>
                      <span>Recommended: 300-800 words</span>
                    </div>
                  </div>
                  <div style={{ marginBottom: "20px" }}>
                    <SectionTitle>Recommendation Letter (Optional)</SectionTitle>
                    <p style={{ fontSize: "14px", color: "#888", marginBottom: "8px" }}>
                      If you have a recommendation from a teacher or mentor, paste a summary here.
                    </p>
                    <textarea
                      id="recommendation"
                      className={inputClass}
                      style={{ minHeight: "120px", resize: "vertical" }}
                      value={recommendation}
                      onChange={(e) => setRecommendation(e.target.value)}
                      placeholder="Paste your recommendation summary here..."
                    />
                  </div>
                  <div>
                    <SectionTitle>Video Presentation (Optional)</SectionTitle>
                    <p style={{ fontSize: "14px", color: "#888", marginBottom: "16px", lineHeight: 1.6 }}>
                      Submit a link to your video presentation (up to 5 minutes).
                    </p>
                    <Label htmlFor="videoLink">Link to your video</Label>
                    <input
                      id="videoLink"
                      className={inputClass}
                      value={videoLink}
                      onChange={(e) => setVideoLink(e.target.value)}
                      placeholder="https://youtube.com/watch?v=... or Google Drive link"
                    />
                    <p style={{ fontSize: "12px", color: "#999", marginTop: "6px" }}>
                      Upload to YouTube (unlisted) or Google Drive and paste the link here.
                    </p>
                  </div>
                </div>
              </div>

              {/* Step 4: Extracurriculars & Projects */}
              <div style={{ display: currentStep === 3 ? "block" : "none" }}>
                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px", marginBottom: "16px" }}>
                  <SectionTitle>Extracurricular Activities</SectionTitle>
                  {extracurriculars.map((ec, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "5fr 3fr 3fr auto", gap: "12px", alignItems: "end", paddingBottom: "12px", borderBottom: i < extracurriculars.length - 1 ? "1px solid #f0f0f0" : "none", marginBottom: "12px" }}>
                      <div>
                        <Label htmlFor={`ec-act-${i}`}>Activity</Label>
                        <input
                          id={`ec-act-${i}`}
                          className={inputClass}
                          value={ec.activity}
                          onChange={(e) => updateEC(i, "activity", e.target.value)}
                          placeholder="Debate Club"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`ec-role-${i}`}>Role</Label>
                        <input
                          id={`ec-role-${i}`}
                          className={inputClass}
                          value={ec.role}
                          onChange={(e) => updateEC(i, "role", e.target.value)}
                          placeholder="president"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`ec-dur-${i}`}>Duration (months)</Label>
                        <input
                          id={`ec-dur-${i}`}
                          type="number"
                          className={inputClass}
                          value={ec.duration_months}
                          onChange={(e) => updateEC(i, "duration_months", e.target.value)}
                          placeholder="24"
                        />
                      </div>
                      <div style={{ display: "flex", alignItems: "center", paddingBottom: "2px" }}>
                        {extracurriculars.length > 1 && (
                          <button type="button" onClick={() => removeEC(i)} style={{ color: "#f87171", background: "none", border: "none", fontSize: "20px", cursor: "pointer" }}>&times;</button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button type="button" onClick={addExtracurricular} className={btnSecondary}>
                    + Add Activity
                  </button>
                </div>

                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px" }}>
                  <SectionTitle>Projects</SectionTitle>
                  {projects.map((proj, i) => (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "4fr 3fr 4fr auto", gap: "12px", alignItems: "end", paddingBottom: "12px", borderBottom: i < projects.length - 1 ? "1px solid #f0f0f0" : "none", marginBottom: "12px" }}>
                      <div>
                        <Label htmlFor={`proj-name-${i}`}>Project Name</Label>
                        <input
                          id={`proj-name-${i}`}
                          className={inputClass}
                          value={proj.name}
                          onChange={(e) => updateProject(i, "name", e.target.value)}
                          placeholder="Free tutoring program"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`proj-role-${i}`}>Your Role</Label>
                        <input
                          id={`proj-role-${i}`}
                          className={inputClass}
                          value={proj.role}
                          onChange={(e) => updateProject(i, "role", e.target.value)}
                          placeholder="founder"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`proj-imp-${i}`}>Impact</Label>
                        <input
                          id={`proj-imp-${i}`}
                          className={inputClass}
                          value={proj.impact}
                          onChange={(e) => updateProject(i, "impact", e.target.value)}
                          placeholder="Reached 150+ students"
                        />
                      </div>
                      <div style={{ display: "flex", alignItems: "center", paddingBottom: "2px" }}>
                        {projects.length > 1 && (
                          <button type="button" onClick={() => removeProject(i)} style={{ color: "#f87171", background: "none", border: "none", fontSize: "20px", cursor: "pointer" }}>&times;</button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button type="button" onClick={addProject} className={btnSecondary}>
                    + Add Project
                  </button>
                </div>
              </div>

              {/* Step 5: Review & Submit */}
              <div style={{ display: currentStep === 4 ? "block" : "none" }}>
                <div style={{ backgroundColor: "#ffffff", borderRadius: "16px", border: "1px solid #e5e5e5", padding: "32px" }}>
                  <SectionTitle>Review Your Application</SectionTitle>
                  <p style={{ fontSize: "14px", color: "#888", marginBottom: "24px" }}>
                    Please review all information before submitting. You can click any tab above to make changes.
                  </p>

                  {/* Personal */}
                  <div style={{ marginBottom: "24px" }}>
                    <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Personal Information</h3>
                    <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
                        <div><span style={{ color: "#999" }}>Name:</span> {name || "—"}</div>
                        <div><span style={{ color: "#999" }}>Age:</span> {age}</div>
                        <div><span style={{ color: "#999" }}>Program:</span> {selectedProgram}</div>
                      </div>
                    </div>
                  </div>

                  {/* Education */}
                  <div style={{ marginBottom: "24px" }}>
                    <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Education</h3>
                    <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                        <div><span style={{ color: "#999" }}>School Type:</span> {SCHOOL_TYPES.find(s => s.value === schoolType)?.label || schoolType}</div>
                        <div><span style={{ color: "#999" }}>GPA:</span> {gpa || "—"}</div>
                        <div><span style={{ color: "#999" }}>Years:</span> {yearsOfStudy}</div>
                      </div>
                      {achievements.filter(a => a.trim()).length > 0 && (
                        <div style={{ marginBottom: "8px" }}>
                          <span style={{ color: "#999" }}>Achievements:</span>
                          <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
                            {achievements.filter(a => a.trim()).map((a, i) => <li key={i}>{a}</li>)}
                          </ul>
                        </div>
                      )}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                        <div><span style={{ color: "#999" }}>Languages:</span> {languages || "—"}</div>
                        <div><span style={{ color: "#999" }}>Skills:</span> {skills || "—"}</div>
                      </div>
                    </div>
                  </div>

                  {/* Essay */}
                  <div style={{ marginBottom: "24px" }}>
                    <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Essay &amp; Motivation</h3>
                    <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                      <div style={{ marginBottom: "8px" }}><span style={{ color: "#999" }}>Prompt:</span> {essayPrompt}</div>
                      <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{essayText || "— No essay written yet —"}</div>
                      <div style={{ marginTop: "8px", fontSize: "12px", color: "#999" }}>{wordCount} words</div>
                      {recommendation && (
                        <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #e5e5e5" }}>
                          <span style={{ color: "#999" }}>Recommendation:</span>
                          <div style={{ whiteSpace: "pre-wrap", marginTop: "4px" }}>{recommendation}</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Extracurriculars */}
                  {extracurriculars.filter(ec => ec.activity.trim()).length > 0 && (
                    <div style={{ marginBottom: "24px" }}>
                      <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Extracurriculars</h3>
                      <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                        {extracurriculars.filter(ec => ec.activity.trim()).map((ec, i) => (
                          <div key={i} style={{ marginBottom: i < extracurriculars.filter(e => e.activity.trim()).length - 1 ? "8px" : 0 }}>
                            <strong>{ec.activity}</strong> — {ec.role || "N/A"} ({ec.duration_months || "?"} months)
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Projects */}
                  {projects.filter(p => p.name.trim()).length > 0 && (
                    <div style={{ marginBottom: "24px" }}>
                      <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Projects</h3>
                      <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                        {projects.filter(p => p.name.trim()).map((p, i) => (
                          <div key={i} style={{ marginBottom: i < projects.filter(pr => pr.name.trim()).length - 1 ? "8px" : 0 }}>
                            <strong>{p.name}</strong> — {p.role || "N/A"} | {p.impact || "No impact described"}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Video */}
                  <div style={{ marginBottom: "24px" }}>
                    <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#141414", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>Video Presentation</h3>
                    <div style={{ backgroundColor: "#f9f9f9", borderRadius: "12px", padding: "16px", fontSize: "14px", color: "#333" }}>
                      {videoLink ? (
                        <a href={videoLink} target="_blank" rel="noopener noreferrer" style={{ color: "#c1f11d", textDecoration: "underline" }}>{videoLink}</a>
                      ) : (
                        <span style={{ color: "#999" }}>No video link provided</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Navigation buttons */}
              <div style={{ marginTop: "32px", display: "flex", flexDirection: "column", gap: "12px" }}>
                {currentStep < 4 ? (
                  <button
                    type="button"
                    onClick={() => setCurrentStep(currentStep + 1)}
                    style={{
                      width: "100%",
                      backgroundColor: "#c1f11d",
                      color: "#141414",
                      border: "none",
                      borderRadius: "15px",
                      padding: "16px",
                      fontSize: "17px",
                      fontWeight: 600,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "#b0e010"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "#c1f11d"; }}
                  >
                    Next Step
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={submitting}
                    style={{
                      width: "100%",
                      backgroundColor: "#141414",
                      color: "#c1f11d",
                      border: "none",
                      borderRadius: "15px",
                      padding: "16px",
                      fontSize: "17px",
                      fontWeight: 600,
                      cursor: submitting ? "not-allowed" : "pointer",
                      opacity: submitting ? 0.5 : 1,
                      transition: "all 0.2s ease",
                    }}
                    onMouseEnter={(e) => { if (!submitting) (e.currentTarget as HTMLElement).style.backgroundColor = "#2a2a2a"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "#141414"; }}
                  >
                    {submitting ? "Submitting..." : "Submit Application"}
                  </button>
                )}
                {currentStep > 0 && (
                  <button
                    type="button"
                    onClick={() => setCurrentStep(currentStep - 1)}
                    style={{ background: "none", border: "none", color: "#666", fontSize: "15px", fontWeight: 500, cursor: "pointer", padding: "8px 0", textAlign: "center" }}
                  >
                    &larr; Previous Step
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Sidebar */}
          <div style={{ flex: "0 0 340px" }}>
            {/* Important Dates */}
            <div style={{ backgroundColor: "#ffffff", borderRadius: "18px", border: "1.5px solid #d7d7d7", padding: "28px", marginBottom: "14px" }}>
              <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#141414", margin: "0 0 16px 0" }}>Important Dates</h3>
              <div style={{ fontSize: "14px", color: "#555", lineHeight: 1.9 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Application Opens</span>
                  <span style={{ fontWeight: 600, color: "#141414" }}>Apr 1, 2026</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Early Decision</span>
                  <span style={{ fontWeight: 600, color: "#141414" }}>May 15, 2026</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Final Deadline</span>
                  <span style={{ fontWeight: 600, color: "#d97706" }}>Jun 30, 2026</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Results Announced</span>
                  <span style={{ fontWeight: 600, color: "#141414" }}>Jul 20, 2026</span>
                </div>
              </div>
            </div>

            {/* Required Documents */}
            <div style={{ backgroundColor: "#ffffff", borderRadius: "18px", border: "1.5px solid #d7d7d7", padding: "28px" }}>
              <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#141414", margin: "0 0 16px 0" }}>Required Documents</h3>
              {[
                { label: "Personal Information", done: !!name },
                { label: "GPA & Education", done: !!gpa },
                { label: "Essay (200+ words)", done: wordCount >= 200 },
                { label: "Video Presentation", done: !!videoLink.trim() },
                { label: "Achievements", done: achievements.some(a => a.trim()) },
                { label: "Languages", done: !!languages.trim() },
              ].map((item) => (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "10px", fontSize: "14px" }}>
                  <span style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "22px",
                    height: "22px",
                    borderRadius: "5px",
                    border: item.done ? "none" : "1.5px solid #ddd",
                    backgroundColor: item.done ? "#c1f11d" : "transparent",
                    fontSize: "12px",
                    color: "#141414",
                    flexShrink: 0,
                  }}>
                    {item.done && "\u2713"}
                  </span>
                  <span style={{ color: item.done ? "#141414" : "#999" }}>{item.label}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>

      {/* ══════ FOOTER ══════ */}
      <footer style={{ backgroundColor: "#141414", position: "relative", overflow: "hidden", padding: "60px 0 40px" }}>
        {/* Gradient logo as background decoration */}
        <img
          src="/assets/InVision U GRADIENT.svg"
          alt=""
          style={{
            position: "absolute",
            bottom: "-30px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "clamp(600px, 80vw, 1200px)",
            opacity: 0.08,
            pointerEvents: "none",
          }}
        />
        <div style={{ position: "relative", zIndex: 1, maxWidth: "1200px", margin: "0 auto", padding: "0 40px", textAlign: "center" }}>
          <img src="/assets/InVision U white.png" alt="inVision U" style={{ width: "169px", height: "auto", margin: "0 auto 16px" }} />
          <p style={{ fontSize: "14px", color: "#666", marginBottom: "24px" }}>
            AI-Assisted Evaluation System &mdash; All final admission decisions are made by the human admissions committee.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: "32px", marginBottom: "32px" }}>
            {[
              { href: "/#apply", label: "Apply" },
              { href: "/teach", label: "Teaching Challenge" },
              { href: "/dashboard", label: "Dashboard" },
            ].map((link) => (
              <a
                key={link.label}
                href={link.href}
                style={{ fontSize: "14px", color: "#888", textDecoration: "none", transition: "color 0.2s" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#c1f11d")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#888")}
              >
                {link.label}
              </a>
            ))}
          </div>
          <div style={{ borderTop: "1px solid #333", paddingTop: "20px", fontSize: "12px", color: "#555" }}>
            Powered by inDrive &middot; Built for Decentrathon 5.0
          </div>
        </div>
      </footer>
    </div>
  );
}
