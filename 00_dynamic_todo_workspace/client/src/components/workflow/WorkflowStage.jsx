export function WorkflowStage({ stage, index, selected, detailId, onSelect }) {
  const complete = stage.status === "complete";
  return (
    <button className={`stage ${complete ? "done" : ""}`} type="button" aria-pressed={selected} aria-controls={detailId} onClick={() => onSelect(stage)}>
      <span className="number">{complete ? "✓" : index + 1}</span>
      <span><strong>{stage.name}</strong><small>{stage.evidence}</small></span>
    </button>
  );
}
