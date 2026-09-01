import { Button } from "@radix-ui/themes";

export function Hero() {
  return (
    <section className="hero">
      <div>
        <p className="kicker">PROJECT 02 · CAUSAL LANGUAGE MODELING</p>
        <h1>Small model.<br /><em>Clear evidence.</em></h1>
        <p className="lede">An interactive evidence studio for a character-level language model. Follow the data split, inspect probabilities, and replay generation through a real API.</p>
        <div className="actions">
          <Button asChild size="3"><a href="#playground">Open replay ↓</a></Button>
          <a href="#method">How it works ↗</a>
        </div>
      </div>
      <div className="hero-core" aria-label="Context predicts the next character">
        <span>next</span><strong>char</strong><small>context → prediction</small>
      </div>
    </section>
  );
}
