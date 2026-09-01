export function MetricCard({ label, value, note, accent = false }) {
  return <article className={`metric${accent ? " lime" : ""}`}><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}
