export const percent = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
export const decimal = (value) => Number(value || 0).toFixed(2);
export const rank = (index) => String(index + 1).padStart(2, "0");
