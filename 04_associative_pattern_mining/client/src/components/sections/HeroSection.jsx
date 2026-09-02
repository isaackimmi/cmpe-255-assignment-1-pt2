export function HeroSection() {
  return (
    <section className="hero">
      <div>
        <p className="eyebrow">MARKET-BASKET INTELLIGENCE · CRISP-DM</p>
        <h1>Find the products<br /><em>that travel together.</em></h1>
        <p className="lede">An interactive evidence workbench for discovering itemsets, qualifying rules, and inspecting the baskets behind each signal.</p>
        <a className="hero-link" href="#thresholds">Open the threshold lab ↓</a>
      </div>
      <div className="hero-art" aria-hidden="true">
        <div className="orbit orbit-a" /><div className="orbit orbit-b" />
        <div className="node node-a">bread</div><div className="node node-b">milk</div><div className="node node-c">jam</div>
        <div className="core">lift<strong>↗</strong></div>
      </div>
    </section>
  );
}
