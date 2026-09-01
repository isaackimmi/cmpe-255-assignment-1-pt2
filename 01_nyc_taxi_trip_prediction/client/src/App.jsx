import { AppShell } from "./components/layout/AppShell";
import { ErrorState, LoadingState } from "./components/common/AsyncState";
import { EvidenceSection } from "./components/evidence/EvidenceSection";
import { SliceExplorer } from "./components/explorer/SliceExplorer";
import { TripEstimator } from "./components/estimator/TripEstimator";
import { HeroSection } from "./components/sections/HeroSection";
import { MethodSection } from "./components/sections/MethodSection";
import { useExperimentData } from "./hooks/useExperimentData";

export default function App() {
  const { metrics, importance, status, error, reload } = useExperimentData();
  return (
    <AppShell status={status} source={metrics?.source}>
      <HeroSection metrics={metrics} />
      {status === "loading" && (
        <section className="section">
          <LoadingState label="Loading experiment evidence…" />
        </section>
      )}
      {status === "error" && (
        <section className="section">
          <ErrorState
            error={error}
            message={
              error?.status === 0
                ? "Cannot reach the analytics API. Start FastAPI on port 8001 and retry."
                : undefined
            }
            onRetry={reload}
          />
        </section>
      )}
      {status === "success" && (
        <EvidenceSection metrics={metrics} importance={importance} />
      )}
      <SliceExplorer enabled={status === "success"} />
      <TripEstimator />
      <MethodSection />
    </AppShell>
  );
}
