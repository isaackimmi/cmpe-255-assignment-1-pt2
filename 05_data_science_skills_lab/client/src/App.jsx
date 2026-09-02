import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import { useEffect, useRef } from "react";
import { AppShell } from "./components/layout/AppShell";
import { Hero } from "./components/layout/Hero";
import { MethodSection } from "./components/layout/MethodSection";
import { ExplorerFilters } from "./components/filters/ExplorerFilters";
import { MetricGrid } from "./components/metrics/MetricGrid";
import { EvidencePanels } from "./components/evidence/EvidencePanels";
import { FilteredRowsPanel } from "./components/evidence/FilteredRowsPanel";
import { MODULE_COPY } from "./constants/modules";
import { useLabData } from "./hooks/useLabData";

export default function App() {
  const lab = useLabData();
  const copy = MODULE_COPY[lab.module];
  const moduleHeading = useRef(null);
  useEffect(() => { moduleHeading.current?.focus(); }, [lab.module]);
  const status = lab.error ? "○ API ERROR" : lab.loading ? "CONNECTING…" : `● API CONNECTED · ${lab.module === "overview" ? `${lab.rowsResult.count} ROWS` : lab.module.toUpperCase()}`;
  return <AppShell activeModule={lab.module} onSelectModule={lab.selectModule} status={status} ready={!lab.error && !lab.loading}>
      <Hero/>
      <MetricGrid metrics={lab.metrics}/>
      <section className="workspace">
        <div className="workspace-head"><div><p className="eyebrow accent">LIVE EXPLORER</p><h2 ref={moduleHeading} tabIndex="-1">{copy[0]}</h2><p className="muted">{copy[1]}</p></div><ExplorerFilters filters={lab.filters} onChange={lab.updateFilter} disabled={lab.pending.rows}/></div>
        {lab.error && <Alert severity="error" action={<Button color="inherit" onClick={lab.retry}>Retry</Button>}>Evidence request failed: {lab.error.message}. No model result was fabricated in the browser.</Alert>}
        {lab.loading && !lab.error && <div className="loading-state"><CircularProgress size={28}/><span>Loading API-backed evidence…</span></div>}
        {!lab.pending.summary && !lab.errors.summary && lab.summary && lab.metrics && <>
          {!lab.pending.module && !lab.errors.module && <EvidencePanels module={lab.module} metrics={lab.metrics} moduleData={lab.moduleData} summary={lab.summary} rowsResult={lab.rowsResult}/>}
          <FilteredRowsPanel rowsResult={lab.rowsResult} filters={lab.filters} updating={lab.pending.rows}/>
        </>}
      </section>
      <MethodSection/>
      <footer>PROJECT 05 · LOCAL ARTIFACT WORKBENCH <span>seed 255 · standard-library ML</span></footer>
  </AppShell>;
}
