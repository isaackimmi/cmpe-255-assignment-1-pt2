import { Button, Card } from "@mui/material";

export function RunStatus({ summary, error, loading, onRefresh }) {
  return <Card component="article" className="panel api-card"><p className="eyebrow">E2E RUN STATUS</p><h2>Live experiment surface.</h2>{error ? <p className="error" role="alert">{error.message}. Check the artifact run and refresh.</p> : summary && <div className="run-meta"><div><span>API</span><b>FastAPI · connected</b></div><div><span>RUN</span><b>seed {summary.seed} · {summary.provenance.python}</b></div><div><span>DATA</span><b>{summary.generator.interpretation}</b></div><div><span>MANIFEST</span><b>SHA-256 set verified</b></div></div>}<Button variant="contained" color="secondary" onClick={onRefresh} disabled={loading}>{loading ? "Checking…" : "Refresh artifacts ↻"}</Button><p className="note">The browser does not invent metrics. It requests validated JSON from FastAPI, which reads the reproducible artifacts and exposes a scoring endpoint.</p></Card>;
}
