export function MetricCard({ label, value = "—", note, accent = false }) {
  return (
    <article className={accent ? "accent-card" : undefined}>
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
      <small>{note}</small>
    </article>
  );
}
