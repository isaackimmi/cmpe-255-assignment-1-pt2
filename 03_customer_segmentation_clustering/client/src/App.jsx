import { useEffect, useState } from "react";
import { Alert, CircularProgress } from "@mui/material";
import { AppShell } from "./components/layout/AppShell";
import { Hero } from "./components/layout/Hero";
import { MetricGrid } from "./components/dashboard/MetricGrid";
import { MethodPanel } from "./components/dashboard/MethodPanel";
import { ProfileLens } from "./components/dashboard/ProfileLens";
import { RunStatus } from "./components/dashboard/RunStatus";
import { ValidationPanel } from "./components/dashboard/ValidationPanel";
import { PointExplorer } from "./components/explorer/PointExplorer";
import { ScoringWorkbench } from "./components/scoring/ScoringWorkbench";
import { DataErrorBoundary } from "./components/common/DataErrorBoundary";
import { useSegmentationData } from "./hooks/useSegmentationData";

export default function App() {
  const { summary, profiles, points, validation, status, error, loading, refresh } = useSegmentationData();
  const [cluster, setCluster] = useState("all");
  const [profileFeature, setProfileFeature] = useState("spend_score");
  const [projection, setProjection] = useState("raw");
  const [xFeature, setXFeature] = useState("spend_score");
  const [yFeature, setYFeature] = useState("annual_income_k");
  const [selectedId, setSelectedId] = useState(null);
  useEffect(() => { if (!selectedId && points.length) setSelectedId(points[0].customer_id); }, [points, selectedId]);
  return (
    <AppShell status={status}>
      <Hero selectedK={summary?.selected_k} />
      {loading && !summary && <div className="loading"><CircularProgress /><span>Loading verified experiment evidence…</span></div>}
      {error && !summary && <Alert severity="error" sx={{ mb: 3 }}>{error.message}</Alert>}
      <MetricGrid summary={summary} />
      {summary && <>
        <DataErrorBoundary>
        <section className="grid two">
          <ProfileLens profiles={profiles} cluster={cluster} feature={profileFeature} onFeatureChange={setProfileFeature} />
          <ValidationPanel rows={validation} selectedK={summary.selected_k} preprocessing={summary.selected_preprocessing} />
        </section>
        <PointExplorer points={points} profiles={profiles} cluster={cluster} onClusterChange={setCluster} projection={projection} onProjectionChange={setProjection} xFeature={xFeature} onXChange={setXFeature} yFeature={yFeature} onYChange={setYFeature} selectedId={selectedId} onSelect={setSelectedId} />
        <ScoringWorkbench />
        <section className="grid two"><MethodPanel /><RunStatus summary={summary} error={error} loading={loading} onRefresh={refresh} /></section>
        </DataErrorBoundary>
      </>}
    </AppShell>
  );
}
