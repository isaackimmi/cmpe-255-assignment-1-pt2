import { API_BASE } from "../../services/api";

export function WorkspaceError({ error }) {
  return (
    <main className="main">
      <div className="error" role="alert">
        <h1>API unavailable</h1>
        <p>{error?.message || "The workspace could not be loaded."}</p>
        <p>Start the FastAPI server, then reload.</p>
        <p className="muted">Expected API base: {API_BASE}</p>
      </div>
    </main>
  );
}
