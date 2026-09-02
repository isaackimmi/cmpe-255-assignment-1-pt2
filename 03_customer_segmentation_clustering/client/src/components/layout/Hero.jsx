export function Hero({ selectedK }) {
  return (
    <section className="hero">
      <div><p className="eyebrow">PROJECT 03 · UNSUPERVISED LEARNING</p><h1>Find the shape<br /><em>of your customers.</em></h1><p className="lede">An interactive evidence surface for a deterministic K-Means experiment. Inspect the geometry, compare candidate models, and keep synthetic hypotheses separate from business truth.</p><div className="hero-tags"><span>artifact-backed</span><span>seed 255</span><span>no target labels</span></div></div>
      <div className="hero-orbit" aria-label={`Selected model has ${selectedK ?? "unknown"} clusters`}><div className="orbit" /><div className="orbit orbit-small" /><div className="core"><small>SELECTED K</small><strong>{selectedK ?? "—"}</strong><span>clusters</span></div></div>
    </section>
  );
}
