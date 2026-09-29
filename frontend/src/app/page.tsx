"use client";

import Link from "next/link";
import { SiteNav } from "@/components/site/SiteNav";
import { SiteFooter } from "@/components/site/SiteFooter";
import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import type {
  Education,
  Extracurricular,
  Project,
  Essay,
  Application,
} from "@/lib/types";

/* ── Shared helpers ────────────────────────────────────────────────── */

function SectionTitle({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="mb-6">
      <h3 className="text-[clamp(20px,1.2vw,23.04px)] font-normal text-ink">{children}</h3>
      {hint && <p className="mt-1 text-sm text-ink-2">{hint}</p>}
    </div>
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
    <label htmlFor={htmlFor} className="mb-2 block text-[clamp(14.4px,0.79vw,14.4px)] font-semibold text-ink">
      {children}
      {required && <span className="ml-0.5 text-danger" aria-hidden>*</span>}
    </label>
  );
}

function FieldIcon({ src }: { src: string }) {
  return <img src={src} alt="" className="pointer-events-none absolute left-5 top-1/2 size-6 -translate-y-1/2" />;
}

function Hint({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <p className={`mt-1.5 text-xs text-ink-3 ${className}`}>{children}</p>;
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-line text-lg text-ink-2 transition-colors hover:border-danger hover:text-danger"
    >
      &times;
    </button>
  );
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6 space-y-4">
      <h4 className="text-[clamp(17px,1.2vw,23.04px)] text-ink">{title}</h4>
      {children}
    </section>
  );
}

/** One answer shown the way it was typed: a read-only field. Empty answers show a dash. */
function ReviewField({ label, icon, children }: { label: string; icon?: string; children: React.ReactNode }) {
  const empty = children === "" || children === false || children === null || children === undefined;
  return (
    <div>
      <p className="mb-2 text-sm font-semibold text-ink">{label}</p>
      <div className="relative flex min-h-11 items-center gap-4 break-words rounded-[16px] bg-field px-5 py-3 text-sm text-ink-muted">
        {icon && <img src={icon} alt="" className="size-5 shrink-0" />}
        <span className="min-w-0">{empty ? "–" : children}</span>
      </div>
    </div>
  );
}

const STEPS = ["Personal Information", "Education", "Essay & Motivation", "Extracurriculars & Projects", "Review & Submit"];

// One white card holds the whole step; its sections are separated by a hairline.
const cardClass = "";
const inputClass =
  "w-full rounded-[16px] border border-transparent bg-field px-5 py-3 text-[clamp(14.4px,0.79vw,14.4px)] text-ink outline-none transition placeholder:text-ink-muted hover:border-line focus:border-ink focus:bg-white focus:ring-4 focus:ring-accent/40 aria-[invalid=true]:border-danger aria-[invalid=true]:focus:ring-danger/15";
/** A field with the Figma icon inside on the left. */
const iconInputClass = `${inputClass} pl-14`;
const btnSecondary =
  "rounded-full border border-line bg-white px-5 py-2.5 text-sm font-semibold text-ink transition-colors hover:border-ink";

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
  const { user, updateUser } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Multi-step form
  const [currentStep, setCurrentStep] = useState(0);
  const [sideTab, setSideTab] = useState<"dates" | "documents">("dates");
  const [selectedProgram, setSelectedProgram] = useState("Creative Engineering");
  const [videoLink, setVideoLink] = useState("");
  const [videoTranscript, setVideoTranscript] = useState("");

  // Personal
  const [name, setName] = useState("");

  // Auto-fill name from auth profile
  useEffect(() => {
    if (user?.full_name && !name) setName(user.full_name);
  }, [user, name]);
  const [age, setAge] = useState(17);

  // Education
  const [schoolType, setSchoolType] = useState("public");
  const [schoolName, setSchoolName] = useState("");
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

      if (!user) {
        setError("Please sign in or create an account to submit your application.");
        return;
      }
      if (user.role !== "applicant") {
        setError("Applications are submitted from an applicant account.");
        return;
      }

      // The server links the application to this account.
      const created = await api.candidates.create({
        name,
        age,
        application,
        essay,
        interview_transcript: "",
        recommendation_summary: recommendation,
        video_link: videoLink,
        video_transcript: videoTranscript,
      });

      updateUser({ candidate_id: created.id });

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
      <div className="flex min-h-screen flex-col bg-canvas">
        <SiteNav />
        <main className="flex flex-1 items-center justify-center px-4 py-16">
          <div className="w-full max-w-lg rounded-3xl border border-line bg-white p-8 text-center md:p-10">
            <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-accent">
              <svg className="size-7 text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <h1 className="mt-5 text-2xl font-bold text-ink">Application submitted</h1>
            <p className="mt-2 text-ink-2">Thank you. The admissions committee now has your application.</p>
            <ol className="mt-6 space-y-3 text-left text-sm">
              {[
                "The committee reads your application, with your own words as the evidence.",
                "You are invited to an interview about the experiences you described.",
                "The committee decides and sends you an offer of admission.",
              ].map((text, i) => (
                <li key={text} className="flex gap-3">
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-ink text-xs font-bold text-accent">{i + 1}</span>
                  <span className="pt-0.5 text-ink">{text}</span>
                </li>
              ))}
            </ol>
            <div className="mt-8 rounded-2xl bg-subtle p-4 text-left text-sm text-ink-2">
              <strong className="text-ink">Next: scenarios.</strong> Talk a real situation through with a conversation
              partner, in English, Russian or Kazakh. It takes about ten minutes.
            </div>
            <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/scenarios" className="whitespace-nowrap rounded-full bg-ink px-6 py-3 font-semibold text-accent transition-opacity hover:opacity-90">
                Start the scenarios
              </Link>
              <Link href="/" className="whitespace-nowrap rounded-full border border-line px-6 py-3 font-semibold text-ink transition-colors hover:border-ink">
                Back to home
              </Link>
            </div>
          </div>
        </main>
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

      <SiteNav signInNext="/#apply" />

      {/* ══════ HERO ══════ */}
      {/* Sizes follow the 1920px Figma frame and scale with the viewport. */}
      <section className="relative overflow-hidden bg-white">
        <img src="/assets/hero/BG.png" alt="" className="pointer-events-none absolute inset-0 h-full w-full object-cover object-right" />
        <div className="relative mx-auto flex max-w-[1728px] flex-col items-center gap-10 px-4 pt-12 md:px-[2.9vw] lg:min-h-[clamp(560px,36.5vw,701.28px)] lg:flex-row lg:items-end lg:justify-between lg:gap-[3.89vw] lg:pt-[2.23vw]">
          <div className="w-full lg:w-[27vw] lg:max-w-[517.68px] lg:shrink-0 lg:self-center lg:pb-[2.88vw]">
            <h1 className="max-w-[7.9em] text-[clamp(40px,3.26vw,62.64px)] font-semibold leading-[1.23] text-ink">
              Empowering those who are ready to <span className="box-decoration-clone bg-accent px-[0.1em] py-[0.02em]">change the world.</span>
            </h1>
            <p className="mt-[clamp(24px,2.23vw,43.2px)] text-justify text-[clamp(16px,0.97vw,18.72px)] leading-normal text-ink">
              Join a global network of future leaders at <strong className="font-bold">inVision U</strong> - where ideas meet action, and
              education drives real change.
            </p>
            <div className="mt-[clamp(24px,2.23vw,43.2px)] flex gap-[clamp(8px,0.49vw,9.36px)]">
              <a
                href="#apply"
                className="relative flex h-[clamp(52px,3.26vw,62.64px)] w-[clamp(140px,9.18vw,176.4px)] items-center justify-center overflow-hidden rounded-[20px] bg-ink text-[clamp(20px,1.49vw,28.8px)] text-white transition-transform hover:scale-[1.03]"
              >
                <img src="/assets/icons/grey-brush.svg" alt="" className="pointer-events-none absolute left-1/2 top-1/2 h-[150%] w-auto -translate-x-1/2 -translate-y-1/2" />
                <span className="relative">Start</span>
              </a>
              <a
                href="#about"
                className="flex h-[clamp(52px,3.26vw,62.64px)] flex-1 items-center justify-center rounded-[20px] bg-muted text-[clamp(20px,1.49vw,28.8px)] text-ink transition-colors hover:bg-line lg:w-[17.28vw] lg:max-w-[331.92px] lg:flex-none"
              >
                Learn More
              </a>
            </div>
          </div>
          <img
            src="/assets/hero/Girl.png"
            alt="An inVision U student"
            className="w-full max-w-[560px] lg:w-[36.65vw] lg:max-w-[703.44px]"
          />
        </div>
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
                <span style={{ fontWeight: 600, color: "#ffffff", fontSize: "clamp(24px,2.16vw,28.08px)", whiteSpace: "nowrap", flexShrink: 0 }}>Grow with us</span>
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
            className="reveal reveal-up max-lg:flex-col max-lg:pb-10"
            style={{
              position: "relative",
              borderRadius: "24px",
              backgroundColor: "#141414",
              overflow: "visible",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              minHeight: "320px",
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
            <p className="lg:whitespace-nowrap" style={{ position: "relative", zIndex: 1, fontWeight: 700, color: "#ffffff", fontSize: "clamp(24px,2.16vw,28.8px)", lineHeight: 1.2, maxWidth: "650px", padding: "40px" }}>
              Explore your academic path<br />and find what fits you
            </p>
            {/* Fanned cards — animate on scroll, spread on hover */}
            <div
              className="card-fan max-lg:!mr-0 max-lg:!w-[290px]"
              style={{
                position: "relative",
                width: "360px",
                height: "260px",
                flexShrink: 0,
                marginRight: "40px",
              }}
            >
              {PROGRAMS.map((prog, i) => {
                const rotations = [-12, -8, -4, 0, 4, 8];
                const stackedLeft = [30, 40, 50, 60, 70, 80];
                const stackedTop = [28, 22, 16, 10, 4, 0];
                return (
                  <a
                    key={prog.num}
                    href={prog.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="card-fan-item"
                    style={{
                      position: "absolute",
                      width: "190px",
                      height: "230px",
                      left: `${stackedLeft[i]}px`,
                      top: `${stackedTop[i]}px`,
                      transform: `rotate(${rotations[i]}deg)`,
                      zIndex: i + 1,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      padding: "18px 16px 24px",
                      borderRadius: "18px",
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
                    <div style={{ fontWeight: 500, color: "#ffffff", fontSize: "15px", lineHeight: 1.25 }}>
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
      <section id="apply" className="relative scroll-mt-16 overflow-hidden rounded-t-[clamp(24px,1.39vw,26.64px)] bg-ink pb-[clamp(48px,5.1vw,97.92px)] pt-[clamp(28px,1.8vw,34.56px)]">
        <img src="/assets/icons/app-glow.svg" alt="" className="pointer-events-none absolute left-[62.4%] top-[-67vw] w-[103.3%] max-w-none" />
        <div className="relative mx-auto max-w-[1728px] px-4 md:px-[4.2vw]">
          <h2 className="text-center text-[clamp(32px,2.78vw,53.28px)] font-bold uppercase leading-none text-accent">Application</h2>
          <ol className="mx-auto mb-[clamp(24px,1.87vw,36px)] mt-[clamp(14px,1.08vw,19.8px)] flex w-fit max-w-full items-center gap-[clamp(6px,0.38vw,7.2px)] overflow-x-auto rounded-[clamp(24px,1.39vw,26.64px)] border-2 border-line bg-white p-[clamp(10px,0.77vw,14.4px)]">
            {STEPS.map((step, i) => {
              const state = currentStep === i ? "current" : currentStep > i ? "done" : "todo";
              return (
                <li key={step} className="shrink-0">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(i)}
                    aria-current={state === "current" ? "step" : undefined}
                    className={`flex items-center gap-[clamp(8px,0.56vw,10.8px)] whitespace-nowrap rounded-[clamp(12px,0.63vw,12.24px)] px-[clamp(8px,0.69vw,12.96px)] py-[clamp(6px,0.41vw,7.92px)] text-[clamp(14px,1.03vw,19.44px)] font-bold transition-colors ${
                      state === "current" ? "bg-ink text-accent" : state === "done" ? "bg-accent-soft text-ink hover:bg-muted" : "bg-muted text-ink hover:bg-line"
                    }`}
                  >
                    <span
                      className={`flex size-[clamp(28px,1.8vw,34.56px)] shrink-0 items-center justify-center rounded-full font-bold ${
                        state === "todo" ? "bg-ink text-white" : "bg-accent text-ink"
                      }`}
                    >
                      {state === "done" ? "✓" : i + 1}
                    </span>
                    <span className={state === "current" ? "" : "hidden md:inline"}>{step}</span>
                  </button>
                </li>
              );
            })}
          </ol>

          <div className="grid items-start gap-6 lg:grid-cols-2">
            <form onSubmit={handleSubmit} className="min-w-0 rounded-[20px] border-[2.5px] border-line bg-white p-[clamp(20px,1.58vw,30.24px)]">
              {error && (
                <div role="alert" className="mb-4 rounded-xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
                  {error}
                </div>
              )}

              {/* Step 1: Personal Information */}
              <div hidden={currentStep !== 0}>
                <div className={cardClass}>
                  <SectionTitle>Personal Information</SectionTitle>
                  <div className="space-y-6">
                    <div>
                      <Label htmlFor="name" required>Full Name</Label>
                      <div className="relative">
                        <FieldIcon src="/assets/icons/user.svg" />
                        <input id="name" className={iconInputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="John Doe" autoComplete="name" required />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="age">Age</Label>
                      <div className="relative">
                        <FieldIcon src="/assets/icons/user.svg" />
                        <input id="age" type="number" className={iconInputClass} value={age} onChange={(e) => setAge(parseInt(e.target.value) || 17)} min={14} max={25} />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="program" required>Program</Label>
                      <div className="relative">
                        <FieldIcon src="/assets/icons/search.svg" />
                        <select id="program" className={iconInputClass} value={selectedProgram} onChange={(e) => setSelectedProgram(e.target.value)}>
                          {PROGRAMS.map((p) => (
                            <option key={p.title} value={p.title}>{p.title}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 2: Education */}
              <div hidden={currentStep !== 1}>
                <div className={cardClass}>
                  <SectionTitle hint="Used only to check fairness across groups. It never moves a score.">Education</SectionTitle>
                  <div className="grid gap-5 sm:grid-cols-3">
                    <div>
                      <Label htmlFor="schoolType" required>School type</Label>
                      <select id="schoolType" className={inputClass} value={schoolType} onChange={(e) => setSchoolType(e.target.value)}>
                        {SCHOOL_TYPES.map((st) => (
                          <option key={st.value} value={st.value}>{st.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="gpa" required>GPA (0–4.0)</Label>
                      <input id="gpa" type="number" step="0.1" min="0" max="4.0" className={inputClass} value={gpa} onChange={(e) => setGpa(e.target.value)} placeholder="e.g. 3.8" required />
                    </div>
                    <div>
                      <Label htmlFor="years">Years of study</Label>
                      <input id="years" type="number" className={inputClass} value={yearsOfStudy} onChange={(e) => setYearsOfStudy(parseInt(e.target.value) || 11)} min={9} max={13} />
                    </div>
                  </div>
                  <div className="mt-5">
                    <Label htmlFor="schoolName">School name</Label>
                    <input id="schoolName" className={inputClass} value={schoolName} onChange={(e) => setSchoolName(e.target.value)} placeholder="e.g. School-lyceum No. 12, Taraz" />
                  </div>
                  <div className="mt-5">
                    <Label htmlFor="ach-0">Academic achievements</Label>
                    <div className="space-y-2">
                      {achievements.map((ach, i) => (
                        <div key={i} className="flex gap-2">
                          <input id={`ach-${i}`} className={inputClass} value={ach} onChange={(e) => updateAchievement(i, e.target.value)} placeholder="e.g. Regional maths olympiad, 2nd place" />
                          {achievements.length > 1 && <RemoveButton label="Remove achievement" onClick={() => removeAchievement(i)} />}
                        </div>
                      ))}
                    </div>
                    <button type="button" onClick={addAchievement} className={`${btnSecondary} mt-3`}>
                      + Add achievement
                    </button>
                  </div>
                  <div className="mt-5 grid gap-5 sm:grid-cols-2">
                    <div>
                      <Label htmlFor="languages" required>Languages</Label>
                      <input id="languages" className={inputClass} value={languages} onChange={(e) => setLanguages(e.target.value)} placeholder="Kazakh, Russian, English" required />
                      <Hint>Separate with commas.</Hint>
                    </div>
                    <div>
                      <Label htmlFor="skills">Skills</Label>
                      <input id="skills" className={inputClass} value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="public speaking, mathematics, writing" />
                      <Hint>Separate with commas.</Hint>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 3: Essay & Motivation */}
              <div hidden={currentStep !== 2}>
                <div className={cardClass}>
                  <SectionTitle hint="Tell us what you did, why, and what came of it. Real situations matter more than polished words.">
                    Essay &amp; motivation
                  </SectionTitle>
                  <div>
                    <Label htmlFor="essayPrompt" required>Essay prompt</Label>
                    <select id="essayPrompt" className={inputClass} value={essayPrompt} onChange={(e) => setEssayPrompt(e.target.value)}>
                      {ESSAY_PROMPTS.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mt-5">
                    <Label htmlFor="essayText" required>Your essay</Label>
                    <textarea id="essayText" className={`${inputClass} min-h-[220px] resize-y leading-relaxed`} value={essayText} onChange={(e) => setEssayText(e.target.value)} placeholder="Write in your own voice. A specific story beats a general one." required />
                    <div className="mt-1.5 flex flex-wrap justify-between gap-2 text-xs text-ink-3">
                      <span>
                        {wordCount} word{wordCount !== 1 ? "s" : ""}
                        {wordCount > 0 && wordCount < 200 && <span className="ml-2 text-warn-ink">Aim for at least 200 words</span>}
                        {wordCount >= 200 && wordCount <= 1000 && <span className="ml-2 text-accent-ink">Good length</span>}
                        {wordCount > 1000 && <span className="ml-2 text-warn-ink">Consider trimming to under 1000 words</span>}
                      </span>
                      <span>Recommended: 300–800 words</span>
                    </div>
                  </div>
                </div>

                <div className={`${cardClass} mt-8 border-t-2 border-line pt-8`}>
                  <SectionTitle hint="Both are optional.">Recommendation &amp; video</SectionTitle>
                  <div>
                    <Label htmlFor="recommendation">Recommendation</Label>
                    <textarea id="recommendation" className={`${inputClass} min-h-[110px] resize-y`} value={recommendation} onChange={(e) => setRecommendation(e.target.value)} placeholder="A summary of a recommendation from a teacher or mentor" />
                  </div>
                  <div className="mt-5">
                    <Label htmlFor="videoLink">Link to your video presentation</Label>
                    <input id="videoLink" className={inputClass} value={videoLink} onChange={(e) => setVideoLink(e.target.value)} placeholder="YouTube (unlisted) or Google Drive link" />
                    <Hint>Up to 5 minutes. The committee watches it themselves.</Hint>
                  </div>
                  <div className="mt-5">
                    <Label htmlFor="videoTranscript">Video transcript</Label>
                    <textarea id="videoTranscript" className={`${inputClass} min-h-[110px] resize-y`} value={videoTranscript} onChange={(e) => setVideoTranscript(e.target.value)} placeholder="What you said in the video, if you have it written down" />
                    <Hint>Kept as supporting material for the interviewer. Your essay is what is assessed.</Hint>
                  </div>
                </div>
              </div>

              {/* Step 4: Extracurriculars & Projects */}
              <div hidden={currentStep !== 3}>
                <div className={cardClass}>
                  <SectionTitle hint="Clubs, work, volunteering, anything you kept doing.">Activities</SectionTitle>
                  <div className="space-y-4">
                    {extracurriculars.map((ec, i) => (
                      <div key={i} className="grid items-end gap-3 border-b border-line-soft pb-4 last:border-b-0 last:pb-0 md:grid-cols-[5fr_3fr_3fr_auto]">
                        <div>
                          <Label htmlFor={`ec-act-${i}`}>Activity</Label>
                          <input id={`ec-act-${i}`} className={inputClass} value={ec.activity} onChange={(e) => updateEC(i, "activity", e.target.value)} placeholder="e.g. Debate club" />
                        </div>
                        <div>
                          <Label htmlFor={`ec-role-${i}`}>Role</Label>
                          <input id={`ec-role-${i}`} className={inputClass} value={ec.role} onChange={(e) => updateEC(i, "role", e.target.value)} placeholder="e.g. Captain" />
                        </div>
                        <div>
                          <Label htmlFor={`ec-dur-${i}`}>Months</Label>
                          <input id={`ec-dur-${i}`} type="number" className={inputClass} value={ec.duration_months} onChange={(e) => updateEC(i, "duration_months", e.target.value)} placeholder="e.g. 24" />
                        </div>
                        {extracurriculars.length > 1 ? <RemoveButton label="Remove activity" onClick={() => removeEC(i)} /> : <span />}
                      </div>
                    ))}
                  </div>
                  <button type="button" onClick={addExtracurricular} className={`${btnSecondary} mt-4`}>
                    + Add activity
                  </button>
                </div>

                <div className={`${cardClass} mt-8 border-t-2 border-line pt-8`}>
                  <SectionTitle hint="Something you started or built, and what changed because of it.">Projects</SectionTitle>
                  <div className="space-y-4">
                    {projects.map((proj, i) => (
                      <div key={i} className="grid items-end gap-3 border-b border-line-soft pb-4 last:border-b-0 last:pb-0 md:grid-cols-[4fr_3fr_4fr_auto]">
                        <div>
                          <Label htmlFor={`proj-name-${i}`}>Project</Label>
                          <input id={`proj-name-${i}`} className={inputClass} value={proj.name} onChange={(e) => updateProject(i, "name", e.target.value)} placeholder="e.g. Free tutoring program" />
                        </div>
                        <div>
                          <Label htmlFor={`proj-role-${i}`}>Your role</Label>
                          <input id={`proj-role-${i}`} className={inputClass} value={proj.role} onChange={(e) => updateProject(i, "role", e.target.value)} placeholder="e.g. Founder" />
                        </div>
                        <div>
                          <Label htmlFor={`proj-imp-${i}`}>Impact</Label>
                          <input id={`proj-imp-${i}`} className={inputClass} value={proj.impact} onChange={(e) => updateProject(i, "impact", e.target.value)} placeholder="e.g. 40 students every week" />
                        </div>
                        {projects.length > 1 ? <RemoveButton label="Remove project" onClick={() => removeProject(i)} /> : <span />}
                      </div>
                    ))}
                  </div>
                  <button type="button" onClick={addProject} className={`${btnSecondary} mt-4`}>
                    + Add project
                  </button>
                </div>
              </div>

              {/* Step 5: Review & Submit */}
              <div hidden={currentStep !== 4}>
                <div className={cardClass}>
                  <SectionTitle>Review Your Application</SectionTitle>
                  <p className="-mt-3 mb-6 border-b-2 border-line pb-4 text-xs text-ink-muted">
                    Please review all information before submitting. You can click any tab above to make changes.
                  </p>
                  <ReviewSection title="Personal information">
                    <ReviewField label="Name" icon="/assets/icons/user.svg">{name}</ReviewField>
                    <ReviewField label="Age" icon="/assets/icons/user.svg">{age}</ReviewField>
                    <ReviewField label="Program" icon="/assets/icons/search.svg">{selectedProgram}</ReviewField>
                  </ReviewSection>
                  <ReviewSection title="Education">
                    <ReviewField label="School Type">{SCHOOL_TYPES.find((s) => s.value === schoolType)?.label || schoolType}</ReviewField>
                    <ReviewField label="GPA">{gpa}</ReviewField>
                    <ReviewField label="Languages">{languages}</ReviewField>
                    <ReviewField label="Skills">{skills}</ReviewField>
                    <ReviewField label="Years">{yearsOfStudy}</ReviewField>
                    {achievements.some((a) => a.trim()) && (
                      <ReviewField label="Achievements">{achievements.filter((a) => a.trim()).join("; ")}</ReviewField>
                    )}
                  </ReviewSection>
                  <ReviewSection title="Essay">
                    <ReviewField label={essayPrompt}>
                      {essayText && <span className="line-clamp-4 whitespace-pre-wrap">{essayText}</span>}
                    </ReviewField>
                    <p className="text-xs text-ink-muted">{wordCount} words{recommendation && " · recommendation added"}</p>
                    <ReviewField label="Video presentation">{videoLink}</ReviewField>
                  </ReviewSection>
                  {(extracurriculars.some((ec) => ec.activity.trim()) || projects.some((p) => p.name.trim())) && (
                    <ReviewSection title="Activities & projects">
                      {extracurriculars.filter((ec) => ec.activity.trim()).map((ec, i) => (
                        <ReviewField key={`ec-${i}`} label={ec.activity}>
                          {ec.role || "no role given"} · {ec.duration_months || "?"} months
                        </ReviewField>
                      ))}
                      {projects.filter((p) => p.name.trim()).map((p, i) => (
                        <ReviewField key={`p-${i}`} label={p.name}>
                          {p.role || "no role given"} · {p.impact || "no impact described"}
                        </ReviewField>
                      ))}
                    </ReviewSection>
                  )}
                </div>
              </div>

              {/* Navigation. Distinct keys: reusing one DOM button would let the
                  click that reaches the last step also submit the form. */}
              <div className="mt-8 flex items-center gap-3 border-t-2 border-line pt-8">
                {currentStep > 0 && (
                  <button type="button" onClick={() => setCurrentStep(currentStep - 1)} className="rounded-[15px] bg-muted px-6 py-3 text-[clamp(14.4px,0.79vw,14.4px)] font-semibold text-ink transition-colors hover:bg-line">
                    Back
                  </button>
                )}
                {currentStep < 4 ? (
                  <button key="next" type="button" onClick={() => setCurrentStep(currentStep + 1)} className="flex-1 rounded-[15px] bg-accent py-3 text-[clamp(14.4px,0.79vw,14.4px)] font-semibold text-ink transition-colors hover:bg-accent-strong">
                    Next Step
                  </button>
                ) : (
                  <button key="submit" type="submit" disabled={submitting} className="flex-1 rounded-[15px] bg-ink py-3 text-[clamp(14.4px,0.79vw,14.4px)] font-semibold text-accent transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">
                    {submitting ? "Submitting…" : "Submit Application"}
                  </button>
                )}
              </div>
            </form>

            {/* Sidebar: below the form on small screens, beside it on large ones */}
            <aside className="rounded-[20px] border-[2.5px] border-line bg-white p-[clamp(20px,1.58vw,30.24px)] lg:sticky lg:top-24">
              <div role="tablist" aria-label="Application info" className="mb-7 grid grid-cols-2 gap-3 rounded-[16px] bg-field p-[11px]">
                {(
                  [
                    ["dates", "Important Dates"],
                    ["documents", "Required Documents"],
                  ] as const
                ).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={sideTab === key}
                    onClick={() => setSideTab(key)}
                    className={`whitespace-nowrap rounded-[14px] px-2 py-3 text-[clamp(14px,0.84vw,15.84px)] font-semibold transition-colors ${sideTab === key ? "bg-accent text-ink" : "text-ink-muted hover:text-ink"}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {sideTab === "dates" ? (
                // Fall 2026 intake, quoted from invisionu.education/undergraduate.
                <dl className="space-y-5 border-b-2 border-line pb-7 text-[clamp(14.4px,0.79vw,14.4px)]">
                  {[
                    ["Early admission closes", "Dec 24, 2025"],
                    ["Regular admission opens", "Mar 12, 2026"],
                    ["Final deadline", "Jul 15, 2026"],
                    ["Classes start", "Sep 2026"],
                  ].map(([label, date]) => (
                    <div key={label} className="flex justify-between gap-4">
                      <dt className="text-ink-muted">{label}</dt>
                      <dd className={`text-right font-bold ${label === "Final deadline" ? "text-deadline" : "text-ink"}`}>{date}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <ul className="space-y-4 border-b-2 border-line pb-7">
                  {[
                    { label: "Personal information", done: !!name },
                    { label: "GPA & education", done: !!gpa },
                    { label: "Languages", done: !!languages.trim() },
                    { label: "Essay (200+ words)", done: wordCount >= 200 },
                    { label: "Achievements", done: achievements.some((a) => a.trim()), optional: true },
                    { label: "Video presentation", done: !!videoLink.trim(), optional: true },
                  ].map((item) => (
                    <li key={item.label} className="flex items-start gap-3 text-[clamp(14.4px,0.79vw,14.4px)]">
                      <span
                        aria-hidden
                        className={`mt-px flex size-5 shrink-0 items-center justify-center rounded-[4px] ${
                          item.done ? "bg-accent text-ink" : "border-2 border-ink-muted"
                        }`}
                      >
                        {item.done && (
                          <svg className="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M5 12l5 5 9-10" />
                          </svg>
                        )}
                      </span>
                      <span className={item.done ? "text-ink" : "text-ink-2"}>
                        {item.label}
                        {item.optional && <span className="text-ink-3"> · optional</span>}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </aside>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
