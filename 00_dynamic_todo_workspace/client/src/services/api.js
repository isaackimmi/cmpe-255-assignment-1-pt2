export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const raw = await response.text();
  let body = {};
  try {
    body = raw ? JSON.parse(raw) : {};
  } catch {
    body = { detail: raw || "The API returned an invalid response." };
  }
  if (!response.ok) {
    throw new ApiError(body.detail || body.message || `Request failed (${response.status})`, response.status);
  }
  return body;
}

export const workspaceApi = {
  getWorkspace: (options = {}) => request("/workspace", options),
  createTask: (task) => request("/tasks", { method: "POST", body: JSON.stringify(task) }),
  updateTask: (taskId, update) => request(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(update) }),
  deleteTask: (taskId) => request(`/tasks/${taskId}`, { method: "DELETE" }),
  runAgentCheck: () => request("/agent-check", { method: "POST" }),
};
