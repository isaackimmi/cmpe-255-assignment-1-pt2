import { MetricCard } from "./MetricCard";

export function EvidenceMetrics({ metrics }) {
  const backend = metrics?.backend === "stdlib_char_ngram"
    ? "CHAR N-GRAM"
    : String(metrics?.backend || "—").toUpperCase();
  const cards = [
    ["TEST PERPLEXITY", metrics?.test?.perplexity ?? metrics?.perplexity, "conditional character stream"],
    ["BACKEND", backend, `${metrics?.device || "cpu"} · seed ${metrics?.seed ?? "—"}`],
    ["TEST LOSS", metrics?.test?.loss ?? metrics?.loss, "nats per character"],
    ["TEST TARGETS", metrics?.test?.target_chars ?? metrics?.test_chars, "chronological holdout"],
  ];
  return (
    <section className="metric-grid" id="evidence" aria-label="Held-out model metrics">
      {cards.map(([label, value, note]) => <MetricCard key={label} label={label} value={value} note={note} />)}
    </section>
  );
}
