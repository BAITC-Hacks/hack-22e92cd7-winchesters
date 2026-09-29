import type { Scorer } from "@/lib/dashboard";

const pageButton =
  "flex h-9 w-9 items-center justify-center rounded-full border border-line text-ink transition-colors hover:border-ink disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-line";

/** Search, the scorer toggle and pagination above the applicant table. */
export function Toolbar({
  scorer,
  onScorerChange,
  searchQuery,
  onSearch,
  page,
  pageSize,
  total,
  onPage,
}: {
  scorer: Scorer;
  onScorerChange: (s: Scorer) => void;
  searchQuery: string;
  onSearch: (q: string) => void;
  page: number;
  pageSize: number;
  total: number;
  onPage: (p: number) => void;
}) {
  const totalPages = Math.ceil(total / pageSize);
  return (
    <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center">
      <label className="relative flex-1">
        <span className="sr-only">Search applicants</span>
        <svg className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-3" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
          <circle cx="7" cy="7" r="5" />
          <path d="M11 11l3.5 3.5" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => onSearch(e.target.value)}
          placeholder="Search by name or id"
          className="h-11 w-full rounded-full border border-line bg-white pl-10 pr-4 text-sm text-ink outline-none transition-colors placeholder:text-ink-3 focus:border-ink"
        />
      </label>
      <div className="flex items-center justify-between gap-3">
        <div role="radiogroup" aria-label="Scorer" className="flex shrink-0 gap-1 rounded-full border border-line bg-white p-1">
          {(
            [
              ["baseline", "Completeness"],
              ["ai", "AI score"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="radio"
              aria-checked={scorer === key}
              onClick={() => onScorerChange(key)}
              className={`rounded-full px-3.5 py-1.5 text-[13px] font-semibold transition-colors ${
                scorer === key ? "bg-ink text-accent" : "text-ink-2 hover:text-ink"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {totalPages > 1 && (
          <div className="flex shrink-0 items-center gap-2">
            <span className="whitespace-nowrap text-[13px] text-ink-3">
              {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
            </span>
            <button type="button" aria-label="Previous page" onClick={() => onPage(Math.max(0, page - 1))} disabled={page === 0} className={pageButton}>
              ←
            </button>
            <button
              type="button"
              aria-label="Next page"
              onClick={() => onPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className={pageButton}
            >
              →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
