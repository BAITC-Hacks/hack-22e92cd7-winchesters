import type { Scorer } from "@/lib/dashboard";

const pageButton = (disabled: boolean, fg: string) => ({
  padding: "8px 16px",
  borderRadius: "10px",
  border: "none",
  backgroundColor: disabled ? "#eae9e9" : "#141414",
  color: disabled ? "#969696" : fg,
  fontSize: "13px",
  fontWeight: 600,
  cursor: disabled ? "not-allowed" : "pointer",
});

/** Scorer toggle, search and pagination above the candidate grid. */
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
    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px", backgroundColor: "#fff", borderRadius: "20px", border: "2px solid #d7d7d7", padding: "10px 14px" }}>
      <div role="radiogroup" aria-label="Scorer" className="flex shrink-0 rounded-[10px] bg-[#eae9e9] p-1 gap-1">
        {(
          [
            ["baseline", "Completeness"],
            ["ai", "AI score"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            role="radio"
            aria-checked={scorer === key}
            onClick={() => onScorerChange(key)}
            className={`px-3 py-1.5 rounded-[8px] text-[13px] font-semibold ${scorer === key ? "bg-[#141414] text-[#c1f11d]" : "text-[#141414]"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value)}
        placeholder="Search candidates by name..."
        style={{
          flex: 1,
          padding: "10px 14px",
          borderRadius: "10px",
          border: "none",
          backgroundColor: "#f5f5f5",
          fontSize: "14px",
          outline: "none",
          boxSizing: "border-box" as const,
        }}
      />
      {totalPages > 1 && (
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          <span style={{ fontSize: "13px", color: "#969696", whiteSpace: "nowrap" }}>
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
          </span>
          <button onClick={() => onPage(Math.max(0, page - 1))} disabled={page === 0} style={pageButton(page === 0, "#fff")}>
            &larr;
          </button>
          <button
            onClick={() => onPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            style={pageButton(page >= totalPages - 1, "#c1f11d")}
          >
            &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
