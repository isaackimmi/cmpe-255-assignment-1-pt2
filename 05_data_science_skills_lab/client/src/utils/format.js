export const percent = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
export const number = (value) => (Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "—");
