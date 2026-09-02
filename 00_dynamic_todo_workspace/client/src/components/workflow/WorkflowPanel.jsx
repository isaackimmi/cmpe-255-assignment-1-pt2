import { useMemo, useState } from "react";
import { WorkflowStage } from "./WorkflowStage";

export function WorkflowPanel({ workflow }) {
  const [selectedStage, setSelectedStage] = useState(null);
  const drafted = useMemo(() => workflow.stages.filter((stage) => stage.status === "complete").length, [workflow.stages]);
  const percentage = Math.round((drafted / workflow.stages.length) * 100);
  return (
    <article className="panel workflow">
      <div className="section-head"><div><h2>Example workflow</h2><p>Plan evidence, not live progress.</p></div></div>
      <div className="progress">
        <div className="ring" style={{ "--progress": `${percentage}%` }}><span>{percentage}%</span></div>
        <div><strong>{workflow.current}</strong><div className="muted">{drafted} of {workflow.stages.length} stages drafted</div></div>
      </div>
      <div>{workflow.stages.map((stage, index) => <WorkflowStage key={stage.name} stage={stage} index={index} selected={selectedStage?.name === stage.name} detailId="workflow-detail" onSelect={setSelectedStage} />)}</div>
      <div id="workflow-detail" className="detail" role="status" aria-live="polite" aria-label="Selected workflow evidence">{selectedStage?.detail || "Select a stage to inspect the evidence expected next."}</div>
    </article>
  );
}
