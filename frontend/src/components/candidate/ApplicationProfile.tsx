import type { Candidate } from "@/lib/types";
import { Badge } from "../ui/Badge";
import { Section } from "../ui/Section";

/** What the applicant submitted, as submitted. */
export function ApplicationProfile({ candidate: c }: { candidate: Candidate }) {
  const app = c.application;
  return (
    <>
      <Section title="Education">
        <div className="grid grid-cols-2 gap-3 text-base">
          <div>
            <span className="text-gray-500">School:</span> {app.education.school_type}
          </div>
          <div>
            <span className="text-gray-500">GPA:</span> {app.education.gpa}/4.0
          </div>
        </div>
        {app.education.academic_achievements.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {app.education.academic_achievements.map((a, i) => (
              <Badge key={i} label={a} color="blue" />
            ))}
          </div>
        )}
      </Section>

      {app.extracurriculars.length > 0 && (
        <Section title="Extracurriculars">
          <div className="space-y-2 text-base">
            {app.extracurriculars.map((ec, i) => (
              <div key={i} className="flex justify-between">
                <span>
                  {ec.activity} <span className="text-gray-400">({ec.role})</span>
                </span>
                <span className="text-gray-400">{ec.duration_months} mo</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {app.projects.length > 0 && (
        <Section title="Projects">
          {app.projects.map((p, i) => (
            <div key={i} className="mb-3 text-base">
              <p className="font-medium">
                {p.name} <span className="text-gray-400">({p.role})</span>
              </p>
              {p.impact && <p className="text-gray-500 text-sm">{p.impact}</p>}
            </div>
          ))}
        </Section>
      )}

      <Section title="Skills & Languages">
        <div className="flex flex-wrap gap-1.5">
          {app.skills.map((s) => (
            <Badge key={s} label={s} color="gray" />
          ))}
          {app.languages.map((l) => (
            <Badge key={l} label={l} color="blue" />
          ))}
        </div>
      </Section>

      <Section title="Essay">
        <p className="text-sm text-gray-400 mb-2">
          Prompt: &ldquo;{c.essay.prompt}&rdquo; &middot; {c.essay.word_count} words
        </p>
        <div className="bg-[#eae9e9] rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
          {c.essay.text}
        </div>
      </Section>

      {c.interview_transcript && (
        <Section title="Interview Transcript">
          <div className="bg-[#eae9e9] rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
            {c.interview_transcript}
          </div>
        </Section>
      )}

      {c.recommendation_summary && (
        <Section title="Recommendation">
          <div className="bg-[#eae9e9] rounded-2xl p-5 text-base">{c.recommendation_summary}</div>
        </Section>
      )}
    </>
  );
}
