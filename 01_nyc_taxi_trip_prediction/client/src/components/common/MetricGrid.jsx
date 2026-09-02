import "./metrics.css";

export function MetricGrid({ children, ariaLabel = "Model metrics" }) {
  return (
    <div className="metric-grid" role="list" aria-label={ariaLabel}>
      {children}
    </div>
  );
}
