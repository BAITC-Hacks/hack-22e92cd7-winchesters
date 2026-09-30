"use client";

// The one navigation bar every page uses: brand, page links, and who is
// signed in. Below md the links fold into a menu instead of scrolling away.

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { useAuth, type Role } from "@/lib/useAuth";

const LINKS = [
  { href: "/#apply", label: "Application" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/dashboard", label: "Dashboard" },
];

const ROLE_LABEL: Record<Role, string> = {
  applicant: "Applicant",
  interviewer: "Interviewer",
  committee: "Committee",
  admin: "Admin",
};

function isCurrent(href: string, pathname: string): boolean {
  // The application form lives on the home page.
  if (href === "/#apply") return pathname === "/";
  return pathname.startsWith(href);
}

function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "?";
}

function UserChip({ name, role, onLogout, alwaysShowName = false }: { name: string; role: Role; onLogout: () => void; alwaysShowName?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-xs font-semibold text-accent">
        {initials(name)}
      </span>
      <span className={`${alwaysShowName ? "flex" : "hidden lg:flex"} flex-col leading-tight`}>
        <span className="text-sm font-semibold text-ink">{name}</span>
        <span className="text-[11px] text-ink-3">{ROLE_LABEL[role]}</span>
      </span>
      <button
        type="button"
        onClick={onLogout}
        className="ml-1 rounded-full px-3 py-1.5 text-sm font-medium text-ink-2 transition-colors hover:bg-field hover:text-ink"
      >
        Sign out
      </button>
    </div>
  );
}

export function SiteNav({ signInNext = "" }: { signInNext?: string }) {
  const pathname = usePathname() ?? "/";
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const signInHref = `/auth${signInNext ? `?next=${encodeURIComponent(signInNext)}` : ""}`;

  return (
    <nav className="sticky top-0 z-[100] bg-white">
      <div className="mx-auto flex h-[72px] max-w-[1728px] items-center justify-between gap-4 px-4 md:h-[clamp(72px,3.96vw,76.32px)] md:px-[4.7vw]">
        <Link href="/" className="shrink-0" aria-label="inVision U home">
          <img src="/assets/InVision U Dark.png" alt="inVision U" className="h-[22px] w-auto md:h-[23px]" />
        </Link>

        {/* Links with thin dividers between them, as in the Figma navbar. */}
        <div className="hidden items-center gap-[clamp(12px,1.15vw,22.32px)] md:flex">
          {LINKS.map((link, i) => {
            const current = isCurrent(link.href, pathname);
            return (
              <div key={link.label} className="flex items-center gap-[clamp(12px,1.15vw,22.32px)]">
                {i > 0 && <img src="/assets/icons/nav-line.svg" alt="" className="h-10 w-[2px]" />}
                <Link
                  href={link.href}
                  aria-current={current ? "page" : undefined}
                  className={`whitespace-nowrap rounded-[clamp(14px,0.75vw,14.4px)] p-[clamp(10px,0.75vw,14.4px)] text-[clamp(15px,0.79vw,15.12px)] font-medium leading-none text-ink transition-colors ${
                    current ? "bg-accent" : "hover:bg-field"
                  }`}
                >
                  {link.label}
                </Link>
              </div>
            );
          })}
          <img src="/assets/icons/nav-line.svg" alt="" className="h-10 w-[2px]" />
          {user ? (
            <UserChip name={user.full_name} role={user.role} onLogout={logout} />
          ) : (
            <Link href={signInHref} className="rounded-[clamp(14px,0.75vw,14.4px)] bg-ink p-[clamp(10px,0.75vw,14.4px)] text-[clamp(15px,0.79vw,15.12px)] font-medium leading-none text-white transition-opacity hover:opacity-85">
              Sign in
            </Link>
          )}
        </div>

        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full text-ink hover:bg-field md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {open ? <path d="M5 5l10 10M15 5L5 15" /> : <path d="M3 6h14M3 10h14M3 14h14" />}
          </svg>
        </button>
      </div>

      {open && (
        <div className="border-t border-line-soft bg-white px-4 pb-4 md:hidden">
          <div className="flex flex-col gap-1 pt-2">
            {LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setOpen(false)}
                className={`rounded-xl px-4 py-3 text-base font-medium text-ink ${isCurrent(link.href, pathname) ? "bg-accent" : ""}`}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="mt-3 border-t border-line-soft pt-3">
            {user ? (
              <UserChip name={user.full_name} role={user.role} onLogout={logout} alwaysShowName />
            ) : (
              <Link href={signInHref} className="block rounded-xl bg-ink px-4 py-3 text-center font-medium text-white">
                Sign in
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
