const jsonHeaders = { "content-type": "application/json" };

/** @typedef {{prompt: string, maxNewTokens: number, temperature: number, signal?: AbortSignal}} GenerationInput */
/** @typedef {{token: string, probability: number}} ProbabilityCandidate */
/** @typedef {{generated: string, context_order: number, deterministic: boolean, trace: Array<object>}} ReplayPayload */

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload?.detail === "string"
      ? payload.detail
      : payload?.detail?.message || payload?.detail?.code;
    throw new ApiError(payload?.error?.message || detail || `Request failed (${response.status})`, response.status);
  }
  return response.json();
}

export const modelApi = {
  metrics: ({ signal } = {}) => request("/api/metrics", { signal }),
  behavior: ({ signal } = {}) => request("/api/behavior", { signal }),
  /** @param {GenerationInput} input @returns {Promise<ReplayPayload>} */
  generate: ({ prompt, maxNewTokens, temperature, signal }) => request("/api/generate", {
    method: "POST",
    headers: jsonHeaders,
    signal,
    body: JSON.stringify({ prompt, max_new_tokens: maxNewTokens, temperature }),
  }),
  /** @returns {Promise<{context: string, candidates: ProbabilityCandidate[]}>} */
  probabilities: (context, { signal } = {}) => request("/api/probabilities", {
    method: "POST",
    headers: jsonHeaders,
    signal,
    body: JSON.stringify({ context }),
  }),
};
