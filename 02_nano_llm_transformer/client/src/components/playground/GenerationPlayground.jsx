import { SectionHeader } from "../ui";
import { GenerationForm } from "./GenerationForm";
import { BehaviorInspector } from "./BehaviorInspector";

export function GenerationPlayground({ metrics, onGenerate, replay, requestState, requestError, enabled }) {
  return (
    <section className="playground" id="playground">
      <SectionHeader eyebrow="LIVE API PLAYGROUND" title="Watch the next character happen." description="The browser calls FastAPI, which loads the local model adapter and returns a bounded, auditable generation trace." endpoint="POST /api/generate" />
      <div className="play-grid">
        <GenerationForm onGenerate={onGenerate} replay={replay} requestState={requestState} requestError={requestError} enabled={enabled} />
        <BehaviorInspector replay={replay} metrics={metrics} />
      </div>
    </section>
  );
}
