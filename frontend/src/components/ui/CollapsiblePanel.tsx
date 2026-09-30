"use client";

import { useState, type ReactNode } from "react";

/** A titled, collapsible bar on the dashboard (settings, audit), styled after the Figma dashboard. */
export function CollapsiblePanel({
  icon,
  title,
  badge,
  children,
}: {
  /** A round icon with its own dark background, from the Figma file. */
  icon: string;
  title: string;
  badge?: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <section className="rounded-[clamp(20px,1.12vw,21.6px)] border-2 border-line bg-white p-[clamp(8px,0.56vw,10.8px)]">
      <div className="rounded-[15px] bg-field p-[clamp(6px,0.42vw,7.92px)]">
        <button
          type="button"
          className="flex w-full items-center gap-[clamp(10px,0.56vw,10.8px)] rounded-[5px] bg-muted p-[clamp(12px,0.75vw,14.4px)] text-left transition-colors hover:bg-line"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          <img src={icon} alt="" className="size-[clamp(36px,1.98vw,38.16px)] shrink-0" />
          <span className="text-[clamp(17px,1.06vw,20.16px)] font-semibold text-ink">{title}</span>
          {badge}
          <span className="ml-auto text-2xl text-ink-2" aria-hidden>
            {open ? "−" : "+"}
          </span>
        </button>
      </div>
      {open && <div className="px-4 pb-5 pt-6 md:px-6">{children}</div>}
    </section>
  );
}
