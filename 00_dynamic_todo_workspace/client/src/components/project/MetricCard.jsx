export function MetricCard({ label, value, detail }) {
  return (
    <article className="stat">
      <p className="eyebrow">{label}</p>
      <strong>{value}</strong>
      <span className="muted">{detail}</span>
    </article>
  );
}
