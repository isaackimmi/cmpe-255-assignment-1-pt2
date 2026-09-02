const API_BASE = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, signal) {
  const response = await fetch(`${API_BASE}/${path}`, { signal });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === "string" ? payload.detail : `API request failed: ${response.status}`;
    throw new ApiError(detail, response.status);
  }
  return response.json();
}

function miningQuery(filters) {
  return new URLSearchParams({
    min_support: filters.support,
    min_confidence: filters.confidence,
    min_count: filters.count,
    sort: filters.sort,
  });
}

export const basketApi = {
  getSummary(filters, signal) {
    const query = miningQuery(filters);
    return request(`summary?${query}`, signal);
  },

  getItemsets(filters, signal) {
    const query = miningQuery(filters);
    if (filters.size) query.set("size", filters.size);
    return request(`itemsets?${query}`, signal);
  },

  getRules(filters, signal) {
    return request(`rules?${miningQuery(filters)}`, signal);
  },

  getTransactions(signal) {
    return request("transactions", signal);
  },

  getContext(item, signal) {
    return request(`context?item=${encodeURIComponent(item)}`, signal);
  },
};
