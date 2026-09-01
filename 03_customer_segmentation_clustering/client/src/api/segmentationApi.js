const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload?.detail;
    throw new Error(typeof detail === "string" ? detail : detail?.code || `API request failed: ${response.status}`);
  }
  return payload;
}

export const segmentationApi = {
  evidenceStatus: (signal) => request("/evidence-status", { signal }),
  summary: (signal) => request("/summary", { signal }),
  profiles: (signal) => request("/profiles", { signal }),
  points: (cluster = "all", signal) => request(`/points${cluster === "all" ? "" : `?cluster=${cluster}`}`, { signal }),
  validation: (signal) => request("/validation", { signal }),
  score: (observation, signal) => request("/score", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(observation),
  }),
};
