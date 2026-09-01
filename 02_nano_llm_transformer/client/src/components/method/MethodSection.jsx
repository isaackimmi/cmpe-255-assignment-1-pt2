const steps = [
  ["01 · Prepare", "Preserve character order and split 80/10/10 chronologically to prevent future-character leakage."],
  ["02 · Model", "The default is a smoothed character n-gram. The optional Torch path adds a causal Transformer."],
  ["03 · Evaluate", "Validation informs selection; the untouched test suffix reports loss, perplexity, and OOV rate."],
];

export function MethodSection() {
  return (
    <section className="method" id="method">
      <p className="kicker">CRISP-DM · MODEL CARD</p>
      <h2>Transparent mechanics beat impressive claims.</h2>
      <div className="method-grid">
        {steps.map(([title, copy]) => <article key={title}><b>{title}</b><p>{copy}</p></article>)}
      </div>
    </section>
  );
}
