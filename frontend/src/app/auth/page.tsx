"use client";

import { SiteNav } from "@/components/site/SiteNav";
import { SiteFooter } from "@/components/site/SiteFooter";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { homeFor, saveSession } from "@/lib/session";

// Sizes follow the Figma sign-up and log-in frames at 80%.
const authText = "text-[clamp(15px,0.92vw,17.6px)]";
const authInput = `h-[clamp(35.2px,1.66vw,35.2px)] w-full rounded-[11px] border border-transparent bg-field px-3.5 ${authText} text-ink outline-none transition placeholder:text-ink-muted hover:border-line focus:border-ink focus:bg-white focus:ring-4 focus:ring-accent/40`;

function Field({ id, label, hint, children }: { id: string; label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className={`mb-[clamp(8px,0.61vw,11.68px)] block font-semibold text-ink ${authText}`}>
        {label}
      </label>
      {children}
      {hint && <p className="mt-1.5 text-xs text-ink-muted">{hint}</p>}
    </div>
  );
}

function PasswordInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const [shown, setShown] = useState(false);
  return (
    <div className="relative">
      <input {...props} type={shown ? "text" : "password"} className={`${authInput} pr-12`} />
      <button
        type="button"
        onClick={() => setShown(!shown)}
        aria-label={shown ? "Hide password" : "Show password"}
        className="absolute right-2 top-1/2 flex size-9 -translate-y-1/2 items-center justify-center rounded-lg opacity-80 hover:opacity-100"
      >
        <img src="/assets/icons/eye.svg" alt="" className="h-[13px] w-[19px]" />
      </button>
    </div>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("+7 ");

  function formatPhone(value: string) {
    // Strip everything except digits
    const digits = value.replace(/\D/g, "");
    // Always start with 7
    const d = digits.startsWith("7") ? digits : "7" + digits;
    // Format: +7 XXX XXX-XX-XX
    let formatted = "+7";
    if (d.length > 1) formatted += " " + d.slice(1, 4);
    if (d.length > 4) formatted += " " + d.slice(4, 7);
    if (d.length > 7) formatted += "-" + d.slice(7, 9);
    if (d.length > 9) formatted += "-" + d.slice(9, 11);
    return formatted;
  }
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register") {
      if (password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
    }
    setLoading(true);

    try {
      let res;
      if (mode === "register") {
        res = await api.auth.register(email, password, fullName);
      } else {
        res = await api.auth.login(email, password);
      }

      saveSession(res.token, res.user);

      // Back to the page that sent the user here, if it is theirs to see;
      // useAuth on that page sends anyone else to their own home.
      const next = new URLSearchParams(window.location.search).get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : homeFor(res.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  const switchMode = (next: "login" | "register") => {
    setMode(next);
    setError(null);
  };

  const register = mode === "register";

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <SiteNav />

      <main className="flex flex-1 items-center gap-[1.21vw]">
        {/* The girl on the lime shape over a fading sky, flush with the left edge. */}
        <img src="/assets/auth/bg-girl.png" alt="" className="hidden w-[46.48vw] max-w-[893.6px] self-end lg:block" />

        <section className={`mx-auto w-full px-4 py-10 lg:mx-0 lg:px-0 ${register ? "max-w-[clamp(340px,21.25vw,408px)]" : "max-w-[clamp(340px,23.2vw,445.6px)]"}`}>
          <h1 className="text-center text-[clamp(36px,2.34vw,44.8px)] font-bold text-ink">{register ? "Sign Up" : "Log In"}</h1>

          <form onSubmit={handleSubmit} className="mt-[clamp(10px,0.6vw,11.52px)] space-y-[clamp(16px,0.92vw,17.6px)] rounded-[11px] border-2 border-line bg-white p-[clamp(18px,0.98vw,18.8px)]">
            {error && (
              <div role="alert" className="rounded-xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
                {error}
              </div>
            )}

            {register && (
              <Field id="fullName" label="Name">
                <input id="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Name" autoComplete="name" required className={authInput} />
              </Field>
            )}

            <Field id="email" label="Email">
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" autoComplete="email" required className={authInput} />
            </Field>

            {register && (
              <Field id="phone" label="Mobile phone number">
                <div className="flex h-[clamp(35.2px,1.66vw,35.2px)] items-center gap-1 rounded-[11px] border border-transparent bg-field px-3.5 transition focus-within:border-ink focus-within:bg-white focus-within:ring-4 focus-within:ring-accent/40">
                  <img src="/assets/Kazakhstan.png" alt="Kazakhstan" className="h-[21px] w-[42px] shrink-0 rounded-[4px] object-cover" />
                  <img src="/assets/icons/arrow-down.svg" alt="" className="mr-2 h-[6px] w-[14px] shrink-0" />
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(formatPhone(e.target.value))}
                    placeholder="+7 777 777-77-77"
                    autoComplete="tel"
                    className={`w-full bg-transparent text-ink outline-none placeholder:text-ink-muted ${authText}`}
                  />
                </div>
              </Field>
            )}

            <Field id="password" label="Password" hint={register ? "At least 8 characters." : undefined}>
              <PasswordInput id="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete={register ? "new-password" : "current-password"} required />
            </Field>

            {register && (
              <Field id="confirmPassword" label="Confirm Password">
                <PasswordInput id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm Password" autoComplete="new-password" required />
              </Field>
            )}

            {register && (
              <label className="flex min-h-[clamp(35.2px,1.66vw,35.2px)] cursor-pointer items-center gap-3 rounded-[11px] bg-field px-3.5 py-2 text-[clamp(11.68px,0.61vw,11.68px)] leading-tight text-ink-muted">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="size-5 shrink-0 accent-ink" />
                I consent to the processing of my data and agree to the Privacy Policy
              </label>
            )}

            <div className="border-t-2 border-line pt-[clamp(16px,0.92vw,17.6px)]">
              <button
                type="submit"
                disabled={loading}
                className={`w-full rounded-[8px] bg-accent py-[clamp(10px,0.61vw,11.68px)] font-semibold text-ink transition-colors hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60 ${authText}`}
              >
                {loading ? "Please wait…" : register ? "Sign Up" : "Sign In"}
              </button>
            </div>
          </form>

          <p className={`mt-[clamp(10px,0.56vw,10.88px)] text-center text-ink-muted ${authText}`}>
            {register ? "Already have an account? " : "Don't have an account? "}
            <button type="button" onClick={() => switchMode(register ? "login" : "register")} className="underline underline-offset-2 hover:text-ink">
              {register ? "Log In" : "Sign Up"}
            </button>
          </p>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
