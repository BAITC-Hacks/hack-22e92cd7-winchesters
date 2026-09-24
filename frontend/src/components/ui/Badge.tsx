export type BadgeColor = "green" | "yellow" | "red" | "blue" | "gray";

const COLORS: Record<BadgeColor, string> = {
  green: "bg-[#c1f11d] text-[#141414]",
  yellow: "bg-[#eae9e9] text-[#141414]",
  red: "bg-[#eae9e9] text-[#141414]",
  blue: "bg-[#141414] text-white",
  gray: "bg-[#eae9e9] text-[#141414]",
};

export function Badge({ label, color }: { label: string; color: BadgeColor }) {
  return (
    <span className={`inline-block px-2.5 py-1 rounded-full text-sm font-medium ${COLORS[color]}`}>
      {label}
    </span>
  );
}
