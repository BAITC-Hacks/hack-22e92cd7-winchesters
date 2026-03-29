"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
    <h2 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2 mb-4">
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
    <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-700 mb-1">
      {children}
      {required && <span className="text-red-500 ml-0.5">*</span>}
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition";
const btnSecondary =
  "rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition";

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

const DIMENSIONS = [
  {
    title: "Academic Strength",
    desc: "GPA, achievements, skills breadth, and multilingual ability.",
    weight: "15%",
  },
  {
    title: "Leadership Potential",
    desc: "Roles in activities, projects initiated, demonstrated initiative.",
    weight: "25%",
  },
  {
    title: "Motivation & Values",
    desc: "Essay authenticity, personal drive, alignment with InVision U mission.",
    weight: "25%",
  },
  {
    title: "Growth Trajectory",
    desc: "How far you've come matters more than where you started.",
    weight: "20%",
  },
  {
    title: "Communication",
    desc: "Essay quality, sentence structure, clarity of expression.",
    weight: "15%",
  },
];

/* ── Main page ─────────────────────────────────────────────────────── */

export default function LandingPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

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

      await api.candidates.create({
        name,
        age,
        application,
        essay,
        interview_transcript: "",
        recommendation_summary: recommendation,
      });

      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  const wordCount = essayText.split(/\s+/).filter(Boolean).length;

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
          <p className="text-gray-600">
            Your application has been received. Our AI-assisted evaluation system will analyze your
            profile across 5 dimensions. The admissions committee will make the final decision.
          </p>
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
            }}
            className="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition"
          >
            Submit Another Application
          </button>
        </div>
      </div>
    );
  }

  /* ── Render ────────────────────────────────────────────────────── */

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-indigo-700">InVision U</span>
          <div className="flex items-center gap-4">
            <a href="#apply" className="text-sm text-gray-600 hover:text-indigo-600 font-medium transition">
              Apply
            </a>
            <a
              href="/dashboard"
              className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 transition"
            >
              Admissions Dashboard
            </a>
          </div>
        </div>
      </nav>

      {/* ── Hero Section ─────────────────────────────────────────── */}
      <section className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 text-white">
        <div className="max-w-5xl mx-auto px-4 py-20 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4 leading-tight">
            Your journey starts here
          </h1>
          <p className="text-lg sm:text-xl text-indigo-200 max-w-2xl mx-auto mb-8">
            InVision U uses AI-assisted evaluation to find students with exceptional
            potential — not just exceptional privilege. We measure how far you&apos;ve come,
            not just where you are.
          </p>
          <a
            href="#apply"
            className="inline-block rounded-xl bg-white text-indigo-700 px-8 py-3 text-base font-semibold hover:bg-indigo-50 transition shadow-lg"
          >
            Start Your Application
          </a>
        </div>
      </section>

      {/* ── How We Evaluate ──────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          How We Evaluate Candidates
        </h2>
        <p className="text-center text-gray-500 mb-10 max-w-xl mx-auto">
          Every application is scored across 5 dimensions by our AI system. The admissions
          committee makes all final decisions — AI only provides recommendations.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {DIMENSIONS.map((d) => (
            <div
              key={d.title}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">{d.title}</h3>
                <span className="text-xs font-mono text-indigo-500 bg-indigo-50 rounded-full px-2 py-0.5">
                  {d.weight}
                </span>
              </div>
              <p className="text-sm text-gray-500">{d.desc}</p>
            </div>
          ))}
          <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-5">
            <h3 className="font-semibold text-indigo-800 mb-2">AI Essay Check</h3>
            <p className="text-sm text-indigo-600">
              Statistical stylometry + AI analysis to ensure essay authenticity.
              We value your real voice.
            </p>
          </div>
        </div>
      </section>

      {/* ── Application Form ─────────────────────────────────────── */}
      <section id="apply" className="bg-gray-100 border-t border-gray-200">
        <div className="max-w-3xl mx-auto px-4 py-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            Application Form
          </h2>
          <p className="text-center text-gray-500 mb-8">
            Fill out all required fields. Be authentic — we value your real story.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Personal Info */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Personal Information</SectionTitle>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
            </div>

            {/* Education */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Education</SectionTitle>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
              <div>
                <Label htmlFor="ach-0">Academic Achievements</Label>
                {achievements.map((ach, i) => (
                  <div key={i} className="flex gap-2 mb-2">
                    <input
                      id={`ach-${i}`}
                      className={inputClass}
                      value={ach}
                      onChange={(e) => updateAchievement(i, e.target.value)}
                      placeholder="e.g. National Math Olympiad - 2nd place"
                    />
                    {achievements.length > 1 && (
                      <button type="button" onClick={() => removeAchievement(i)} className="text-red-400 hover:text-red-600 text-xl px-1">&times;</button>
                    )}
                  </div>
                ))}
                <button type="button" onClick={addAchievement} className={`${btnSecondary} mt-1`}>
                  + Add Achievement
                </button>
              </div>
            </div>

            {/* Extracurriculars */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Extracurricular Activities</SectionTitle>
              {extracurriculars.map((ec, i) => (
                <div key={i} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pb-3 border-b border-gray-100 last:border-0">
                  <div className="sm:col-span-5">
                    <Label htmlFor={`ec-act-${i}`}>Activity</Label>
                    <input
                      id={`ec-act-${i}`}
                      className={inputClass}
                      value={ec.activity}
                      onChange={(e) => updateEC(i, "activity", e.target.value)}
                      placeholder="Debate Club"
                    />
                  </div>
                  <div className="sm:col-span-3">
                    <Label htmlFor={`ec-role-${i}`}>Role</Label>
                    <input
                      id={`ec-role-${i}`}
                      className={inputClass}
                      value={ec.role}
                      onChange={(e) => updateEC(i, "role", e.target.value)}
                      placeholder="president"
                    />
                  </div>
                  <div className="sm:col-span-3">
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
                  <div className="sm:col-span-1 flex justify-center">
                    {extracurriculars.length > 1 && (
                      <button type="button" onClick={() => removeEC(i)} className="text-red-400 hover:text-red-600 text-xl">&times;</button>
                    )}
                  </div>
                </div>
              ))}
              <button type="button" onClick={addExtracurricular} className={btnSecondary}>
                + Add Activity
              </button>
            </div>

            {/* Projects */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Projects</SectionTitle>
              {projects.map((proj, i) => (
                <div key={i} className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pb-3 border-b border-gray-100 last:border-0">
                  <div className="sm:col-span-4">
                    <Label htmlFor={`proj-name-${i}`}>Project Name</Label>
                    <input
                      id={`proj-name-${i}`}
                      className={inputClass}
                      value={proj.name}
                      onChange={(e) => updateProject(i, "name", e.target.value)}
                      placeholder="Free tutoring program"
                    />
                  </div>
                  <div className="sm:col-span-3">
                    <Label htmlFor={`proj-role-${i}`}>Your Role</Label>
                    <input
                      id={`proj-role-${i}`}
                      className={inputClass}
                      value={proj.role}
                      onChange={(e) => updateProject(i, "role", e.target.value)}
                      placeholder="founder"
                    />
                  </div>
                  <div className="sm:col-span-4">
                    <Label htmlFor={`proj-imp-${i}`}>Impact</Label>
                    <input
                      id={`proj-imp-${i}`}
                      className={inputClass}
                      value={proj.impact}
                      onChange={(e) => updateProject(i, "impact", e.target.value)}
                      placeholder="Reached 150+ students"
                    />
                  </div>
                  <div className="sm:col-span-1 flex justify-center">
                    {projects.length > 1 && (
                      <button type="button" onClick={() => removeProject(i)} className="text-red-400 hover:text-red-600 text-xl">&times;</button>
                    )}
                  </div>
                </div>
              ))}
              <button type="button" onClick={addProject} className={btnSecondary}>
                + Add Project
              </button>
            </div>

            {/* Languages & Skills */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Languages & Skills</SectionTitle>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

            {/* Essay */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Essay</SectionTitle>
              <div>
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
              <div>
                <Label htmlFor="essayText" required>Your Essay</Label>
                <textarea
                  id="essayText"
                  className={`${inputClass} min-h-[200px]`}
                  value={essayText}
                  onChange={(e) => setEssayText(e.target.value)}
                  placeholder="Write your essay here. Be authentic — we value your real voice and story..."
                  required
                />
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>
                    {wordCount} word{wordCount !== 1 ? "s" : ""}
                    {wordCount > 0 && wordCount < 200 && (
                      <span className="text-amber-600 ml-2">Aim for at least 200 words</span>
                    )}
                    {wordCount >= 200 && wordCount <= 1000 && (
                      <span className="text-emerald-600 ml-2">Good length</span>
                    )}
                    {wordCount > 1000 && (
                      <span className="text-amber-600 ml-2">Consider trimming to under 1000 words</span>
                    )}
                  </span>
                  <span>Recommended: 300-800 words</span>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
              <SectionTitle>Recommendation Letter (Optional)</SectionTitle>
              <p className="text-sm text-gray-500">
                If you have a recommendation from a teacher or mentor, paste a summary here.
              </p>
              <textarea
                id="recommendation"
                className={`${inputClass} min-h-[100px]`}
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value)}
                placeholder="Paste your recommendation summary here..."
              />
            </div>

            {/* Submit */}
            <div className="flex justify-center pb-8">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-indigo-600 px-10 py-3 text-base font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
              >
                {submitting ? "Submitting..." : "Submit Application"}
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-gray-400">
          <p>InVision U Admissions &mdash; AI-Assisted Evaluation System</p>
          <p className="mt-1">
            All final admission decisions are made by the human admissions committee.
            AI provides recommendations only.
          </p>
        </div>
      </footer>
    </div>
  );
}
