import { SplitEvidence } from "./SplitEvidence";
import { RunManifest } from "./RunManifest";

export function EvidencePanels({ metrics }) {
  return (
    <section className="evidence-grid" aria-label="Data and run evidence">
      <SplitEvidence split={metrics?.split} />
      <RunManifest metrics={metrics} />
    </section>
  );
}
