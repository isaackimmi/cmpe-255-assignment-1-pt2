import { Card } from "@radix-ui/themes";

/** @param {{label: string, value?: string|number, note: string}} props */
export function MetricCard({ label, value = "—", note }) {
  return (
    <Card className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </Card>
  );
}
