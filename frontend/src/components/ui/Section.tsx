import type { ReactNode } from "react";

/** A titled block inside the candidate modal, with the lime marker. */
export function Section({ title, children }: { title: ReactNode; children: ReactNode }) {
  return (
    <section>
      <h3 className="text-base font-semibold text-[#141414] uppercase tracking-wider mb-3 flex items-center gap-3">
        <span className="w-1.5 h-5 bg-[#c1f11d] rounded-full inline-block" />
        {title}
      </h3>
      {children}
    </section>
  );
}

/** The near-black gradient card used by analysis panels. */
export function DarkPanel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl p-5 ${className}`} style={{ background: "linear-gradient(180deg, #252525, #0F0F0F)" }}>
      {children}
    </div>
  );
}
