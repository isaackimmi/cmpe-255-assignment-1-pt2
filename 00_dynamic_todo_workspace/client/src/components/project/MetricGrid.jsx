import { MetricCard } from "./MetricCard";

export function MetricGrid({ completedTasks, taskCount, completedStages, stageCount }) {
  const metrics = [
    { label: "Tasks complete", value: `${completedTasks} / ${taskCount}`, detail: "From API-backed queue" },
    { label: "Agent status", value: "Demo only", detail: "No connected run" },
    { label: "Workflow drafted", value: `${completedStages} / ${stageCount}`, detail: "CRISP-DM stages" },
    { label: "Measured lift", value: "Not measured", detail: "No model artifact" },
  ];
  return <section className="stat-grid" aria-label="Workspace metrics">{metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}</section>;
}
