import { Button } from "@mui/material";
import { percent, seconds } from "../../utils/format";

export function HeroSection({ metrics }) {
  const model = metrics?.linear_log_target || {};
  const baseline = metrics?.baseline || {};
  const improvement = baseline.mae_seconds
    ? 1 - model.mae_seconds / baseline.mae_seconds
    : 0;
  return (
    <section className="hero" id="top">
      <div>
        <p className="eyebrow">CMPE 255 · E2E MODEL SERVICE</p>
        <h1>
          Turn trip context
          <br />
          <em>into travel time.</em>
        </h1>
        <p className="lede">
          A chronological regression experiment served as an inspectable API and
          an evidence-first analytical client.
        </p>
        <div className="hero-actions">
          <Button className="button primary" component="a" href="#explorer">
            Explore holdout ↘
          </Button>
          <Button
            className="text-link"
            component="a"
            href="#estimate"
            variant="text"
          >
            Try a route →
          </Button>
        </div>
      </div>
      <div className="hero-orbit" aria-label="Headline model performance">
        <div className="orbit" />
        <div className="orbit two" />
        <div className="hero-number">
          <small>MODEL MAE</small>
          <strong>{seconds(model.mae_seconds)}</strong>
          <span>seconds</span>
          <b>
            {metrics
              ? `${percent(improvement)} below baseline`
              : "loading evidence"}
          </b>
        </div>
      </div>
    </section>
  );
}
