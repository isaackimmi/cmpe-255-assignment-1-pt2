export const percent = (value) => `${(Number(value) * 100).toFixed(1)}%`;
export const seconds = (value) =>
  value == null ? "—" : `${Number(value).toFixed(1)} sec`;
export const durationClock = (value) => {
  const total = Number(value) || 0;
  return `${Math.floor(total / 60)}:${String(Math.round(total % 60)).padStart(2, "0")}`;
};
