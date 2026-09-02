import { AppShell } from "./components/layout/AppShell";
import { Hero } from "./components/evidence/Hero";
import { EvidenceMetrics } from "./components/evidence/EvidenceMetrics";
import { EvidencePanels } from "./components/evidence/EvidencePanels";
import { GenerationPlayground } from "./components/playground/GenerationPlayground";
import { MethodSection } from "./components/method/MethodSection";
import { useModelEvidence } from "./hooks/useModelEvidence";

export function App() {
  const evidence = useModelEvidence();

  return (
    <AppShell
      status={evidence.status}
      loadError={evidence.loadError}
      onRetry={evidence.retryEvidence}
    >
      <Hero />
      <EvidenceMetrics metrics={evidence.metrics} />
      <EvidencePanels metrics={evidence.metrics} />
      <GenerationPlayground
        metrics={evidence.metrics}
        onGenerate={evidence.generate}
        replay={evidence.replay}
        requestState={evidence.requestState}
        requestError={evidence.requestError}
        enabled={evidence.canGenerate}
      />
      <MethodSection />
    </AppShell>
  );
}
