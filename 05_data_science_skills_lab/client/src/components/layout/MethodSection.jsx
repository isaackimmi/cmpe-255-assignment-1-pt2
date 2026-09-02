const principles = [
  ["01", "Fit on train", "Feature medians are learned from training rows, then applied to the holdout. Missing targets are never fabricated for scoring."],
  ["02", "Compare baselines", "Every model view keeps a simple reference point nearby so improvement is measurable rather than implied."],
  ["03", "Interpret, don’t overclaim", "The CSV is a synthetic teaching fixture. Correlations and segments are descriptive, not causal or production evidence."],
];

export function MethodSection() {
  return <section className="method"><div><p className="eyebrow accent">WHY THIS MATTERS</p><h2>Metrics are only useful<br/><em>when their boundaries are visible.</em></h2></div><div className="method-grid">{principles.map(([index, title, copy]) => <article key={index}><b>{index}</b><h3>{title}</h3><p>{copy}</p></article>)}</div></section>;
}
