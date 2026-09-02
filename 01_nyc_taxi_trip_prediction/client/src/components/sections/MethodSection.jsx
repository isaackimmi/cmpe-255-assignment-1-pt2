const steps = [
  "Validate rows and timestamps",
  "Split whole pickup-time groups",
  "Fit on training only",
  "Compare against baselines",
];

export function MethodSection() {
  return (
    <section className="section method">
      <p className="eyebrow">04 / CRISP-DM trace</p>
      <div className="method-grid">
        <div>
          <h2>
            From future-safe split
            <br />
            to useful evidence.
          </h2>
          <p>
            The experiment cleans structural defects, derives distance/time
            features, fits a regularized linear model on log duration, and
            scores a complete chronological holdout.
          </p>
        </div>
        <ol>
          {steps.map((step, index) => (
            <li key={step}>
              <b>{String(index + 1).padStart(2, "0")}</b>
              {step}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
