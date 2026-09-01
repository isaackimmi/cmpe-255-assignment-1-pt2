import { validateModule, validateRows, validateSummary } from "./contracts";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { Accept: "application/json", ...options.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || {});
    throw new Error(detail || `API ${response.status}`);
  }
  return body;
}

export const labApi = {
  getSummary: async ({ signal } = {}) => validateSummary(await request("/api/summary", { signal })),
  getModule: async (module, route, { signal } = {}) => validateModule(module, await request(route, { signal })),
  getRows: async (filters, { signal } = {}) => {
    const query = new URLSearchParams({ ...filters, limit: "1000" });
    return validateRows(await request(`/api/rows?${query}`, { signal }));
  },
};
