export type BadgeColor = "green" | "yellow" | "red" | "blue" | "gray";

const COLORS: Record<BadgeColor, string> = {
  green: "bg-accent text-ink",
  yellow: "bg-muted text-ink",
  red: "bg-muted text-ink",
  blue: "bg-ink text-white",
  gray: "bg-muted text-ink",
};

export function Badge({ label, color }: { label: string; color: BadgeColor }) {
  return (
    <span className={`inline-block px-2.5 py-1 rounded-full text-sm font-medium ${COLORS[color]}`}>
      {label}
    </span>
  );
}
