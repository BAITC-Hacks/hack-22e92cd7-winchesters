/**
 * The neutral state for a view with nothing behind it (LED-12): no numbers,
 * no zeros, no red. It says that nothing was scored and why.
 */
export function Unavailable({ title, detail }: { title: string; detail: string }) {
  return (
    <main className="min-h-screen bg-subtle px-5 py-8 text-ink sm:px-10">
      <div className="mx-auto max-w-3xl">
        <section data-slot="unavailable" className="border border-line bg-white p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-3">{title}</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">Unavailable — nothing was scored</h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-2">{detail}</p>
        </section>
      </div>
    </main>
  );
}
