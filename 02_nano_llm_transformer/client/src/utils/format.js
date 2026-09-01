export const displayToken = (value) => (
  value === "\n" ? "↵" : value === " " ? "·" : value || "∅"
);

export const percentage = (value) => `${(Number(value) * 100).toFixed(1)}%`;

export const compactHash = (value) => value ? `${String(value).slice(0, 12)}…` : "—";
