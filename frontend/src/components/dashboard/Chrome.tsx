"use client";

// Page furniture for the dashboard: scroll progress, and the header with the file filters.

import { useEffect, useState } from "react";


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
      className="fixed top-0 left-0 h-[3px] bg-accent z-[200] transition-all duration-150"
      style={{ width: `${progress}%` }}
    />
  );
}

export interface StatButton {
  key: string;
  label: string;
  count: number;
}

/** Dark banner with the boy on the lime shape, and the filters overlapping its lower edge (Figma "Desktop - 13"). */
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
    <header className="mx-auto w-full max-w-[1728px] px-4 pt-8 md:px-[4.27vw] md:pt-[2.23vw]">
      <div className="relative overflow-hidden rounded-[clamp(24px,1.39vw,26.64px)] bg-ink lg:h-[clamp(340px,20.88vw,401.76px)]">
        <img src="/assets/Dots.png" alt="" className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="relative flex items-start justify-center gap-[clamp(24px,6.12vw,118.08px)] px-6 pb-[clamp(90px,9.36vw,180px)] pt-8 lg:pb-0 lg:pt-[0.94vw]">
          <div className="pt-[clamp(0px,1.87vw,36px)]">
            <h1 className="max-w-[5.8em] text-[clamp(36px,2.77vw,53.28px)] font-bold leading-none text-accent">Admissions Dashboard</h1>
            <p className="mt-[clamp(7.2px,0.38vw,7.2px)] text-[clamp(15px,1.12vw,21.6px)] text-white">AI-Assisted Screening • Human-in-the-loop</p>
          </div>
          {/* The boy stands on the lime shape; the filters card hides his lower half. */}
          <div className="relative hidden h-[16.92vw] max-h-[324.72px] w-[18.36vw] max-w-[352.08px] shrink-0 lg:block">
            <img src="/assets/dashboard/boy-shape.svg" alt="" className="absolute inset-0 h-full w-full" />
            <div className="absolute inset-y-0 left-[4.8%] right-[4.7%] overflow-hidden">
              <img src="/assets/dashboard/boy.png" alt="" className="absolute left-[-4.7%] top-0 h-[128.48%] w-[104.7%] max-w-none" />
            </div>
          </div>
          <p className="hidden items-center gap-[10px] whitespace-nowrap pt-[clamp(0px,1.87vw,36px)] text-[clamp(15px,1.12vw,21.6px)] text-white md:flex">
            <img src="/assets/icons/status-dot.svg" alt="" className="size-[11px]" />
            System active
          </p>
        </div>
      </div>

      <div
        role="group"
        aria-label="Filter applicants by file"
        className="relative z-[1] -mt-[clamp(70px,8.5vw,163.44px)] grid grid-cols-2 gap-[10px] rounded-[clamp(24px,1.39vw,26.64px)] border-2 border-line bg-white px-[clamp(12px,1.12vw,21.6px)] py-[clamp(12px,0.75vw,14.4px)] sm:flex sm:items-center lg:h-[clamp(120px,8.5vw,163.44px)]"
      >
        {stats.map((stat) => {
          const on = active === stat.key;
          return (
            <button
              key={stat.key}
              type="button"
              onClick={() => onSelect(stat.key)}
              aria-pressed={on}
              className={`flex min-h-[clamp(88px,5.69vw,109.44px)] flex-1 flex-col justify-center rounded-[17px] px-[clamp(14px,1.12vw,21.6px)] text-left text-ink transition-colors ${
                on ? "bg-accent" : "bg-muted hover:bg-line"
              }`}
            >
              <span className="block text-[clamp(36px,3.57vw,68.4px)] font-bold leading-none">{stat.count}</span>
              <span className="mt-[clamp(6px,0.38vw,7.2px)] block text-[clamp(14px,1.17vw,22.32px)] leading-tight">{stat.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
