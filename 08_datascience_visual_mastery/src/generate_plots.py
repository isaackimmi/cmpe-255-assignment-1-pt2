"""Generate deterministic visual snapshots for the Project 08 README."""
from __future__ import annotations

import json
from pathlib import Path

try:
    import numpy as np
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # pragma: no cover - exercised on minimal installs
    np = None
    plt = None

from .concepts import (backprop_demo, gradient_descent, naive_bayes_posterior,
                       quadratic, roc_auc, roc_points, threshold_metrics)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"


def save_figures() -> dict[str, str]:
    OUT.mkdir(exist_ok=True)
    if plt is None:
        return _save_svg_fallback()
    plt.style.use("seaborn-v0_8-whitegrid")

    x = np.linspace(0.01, 0.99, 100)
    posterior = [naive_bayes_posterior(p, 0.8, 0.2) for p in x]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.plot(x, posterior, color="#2563eb", linewidth=2.5)
    ax.plot(x, x, "--", color="#94a3b8", label="prior")
    ax.set(xlabel="Prior P(class)", ylabel="Posterior P(class | evidence)", title="Bayes updates belief")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT / "naive_bayes.png", dpi=150); plt.close(fig)

    true = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.95, 0.83, 0.62, 0.36, 0.79, 0.55, 0.41, 0.18, 0.09, 0.02])
    roc = roc_points(true.tolist(), scores.tolist())
    fpr = [point[0] for point in roc]
    tpr = [point[1] for point in roc]
    auc = roc_auc(true.tolist(), scores.tolist())

    fig, ax = plt.subplots(figsize=(6, 3.4)); ax.plot(fpr, tpr, "o-", color="#db2777", label=f"ROC-AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="#94a3b8", label="random")
    ax.set(xlabel="False-positive rate", ylabel="True-positive rate", title="ROC curve across thresholds")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT / "evaluation.png", dpi=150); plt.close(fig)

    path = gradient_descent(); grid = np.linspace(-3, 7, 200)
    fig, ax = plt.subplots(figsize=(6, 3.4)); ax.plot(grid, [quadratic(v) for v in grid], color="#0f766e")
    ax.plot(path, [quadratic(v) for v in path], "o-", color="#f97316")
    ax.set(xlabel="Parameter x", ylabel="Loss f(x)", title="Gradient descent follows the slope")
    fig.tight_layout(); fig.savefig(OUT / "gradient_descent.png", dpi=150); plt.close(fig)

    values = backprop_demo()
    nodes = [("x = 2", 0.10, 0.68), ("w = 3", 0.10, 0.28),
             ("w×x", 0.30, 0.48), ("b = 1", 0.48, 0.14),
             ("+ b", 0.50, 0.48), (f"ŷ = {values['y_hat']:.1f}", 0.70, 0.48),
             (f"L = {values['loss']:.1f}", 0.90, 0.48)]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for label, x_pos, y_pos in nodes:
        ax.scatter([x_pos], [y_pos], s=900, c=["#eef2ff"], edgecolors="#3b6cf5", linewidths=1.5, zorder=3)
        ax.text(x_pos, y_pos, label, ha="center", va="center", color="#172033", weight="bold", fontsize=9, zorder=4)

    forward_edges = [((0.14, 0.68), (0.26, 0.51)), ((0.14, 0.28), (0.26, 0.45)),
                     ((0.34, 0.48), (0.46, 0.48)), ((0.52, 0.48), (0.66, 0.48)),
                     ((0.74, 0.48), (0.86, 0.48)), ((0.48, 0.18), (0.49, 0.42))]
    for start, end in forward_edges:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#3b6cf5", "lw": 1.8})
    reverse_edges = [((0.86, 0.42), (0.74, 0.42)), ((0.66, 0.42), (0.54, 0.42)),
                     ((0.46, 0.42), (0.34, 0.42)), ((0.48, 0.42), (0.45, 0.20)),
                     ((0.26, 0.42), (0.14, 0.30))]
    for start, end in reverse_edges:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#d95d9b", "lw": 1.8})
    ax.text(0.50, 0.87, "forward pass →", ha="center", color="#3b6cf5", weight="bold", fontsize=10)
    ax.text(0.80, 0.34, f"dL/dŷ = {values['dL_dy']:.1f}", ha="center", color="#d95d9b", fontsize=8)
    ax.text(0.58, 0.36, "dŷ/d(w×x) = 1", ha="center", color="#d95d9b", fontsize=8)
    ax.text(0.43, 0.24, "dŷ/db = 1", ha="center", color="#d95d9b", fontsize=8)
    ax.text(0.20, 0.38, "d(w×x)/dw = x = 2", ha="center", color="#d95d9b", fontsize=8)
    ax.text(0.50, 0.04, f"backward: dL/dw = {values['dL_dw']:.1f} · dL/db = {values['dL_db']:.1f}", ha="center", color="#d95d9b", fontsize=9)
    ax.set(xlim=(0, 1), ylim=(0, 1), title="Backpropagation reverses the chain"); ax.axis("off")
    fig.tight_layout(); fig.savefig(OUT / "backpropagation.png", dpi=150); plt.close(fig)

    # Tests may redirect OUT to pytest's temporary directory, which is not
    # necessarily below ROOT. Keep repository-relative paths when possible,
    # otherwise return paths relative to the redirected output directory.
    manifest = {
        name: str((OUT / name).relative_to(ROOT)) if (OUT / name).is_relative_to(ROOT) else str(OUT / name)
        for name in ["naive_bayes.png", "evaluation.png", "gradient_descent.png", "backpropagation.png"]
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _save_svg_fallback() -> dict[str, str]:
    """Render concept-specific SVGs without NumPy or Matplotlib."""
    _write_svg(OUT / "naive_bayes.svg", _bayes_svg())
    _write_svg(OUT / "evaluation.svg", _evaluation_svg())
    _write_svg(OUT / "gradient_descent.svg", _gradient_svg())
    _write_svg(OUT / "backpropagation.svg", _backprop_svg())
    specs = {filename: None for filename in (
        "naive_bayes.svg", "evaluation.svg", "gradient_descent.svg", "backpropagation.svg")}
    manifest = {
        filename: str((OUT / filename).relative_to(ROOT)) if (OUT / filename).is_relative_to(ROOT) else str(OUT / filename)
        for filename in specs
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _write_svg(path: Path, content: str) -> None:
    path.write_text(content)


def _svg_shell(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
<rect width="900" height="420" fill="#f8fafc"/>
<text x="50" y="58" font-family="sans-serif" font-size="30" font-weight="bold" fill="#172033">{title}</text>
<text x="50" y="91" font-family="sans-serif" font-size="17" fill="#64748b">{subtitle}</text>{body}</svg>'''


def _bayes_svg() -> str:
    prior = 0.5
    posterior = naive_bayes_posterior(prior, [0.8, 0.7], [0.2, 0.3])
    bars = []
    for x, value, color, label in ((180, prior, "#aab6cb", "prior"),
                                    (520, posterior, "#2563eb", "posterior")):
        height = 180 * value
        bars.append(f'<rect x="{x}" y="{300-height:.1f}" width="150" height="{height:.1f}" rx="12" fill="{color}"/>')
        bars.append(f'<text x="{x+75}" y="330" text-anchor="middle" font-family="sans-serif" font-size="17" fill="#475569">{label}</text>')
        bars.append(f'<text x="{x+75}" y="{285-height:.1f}" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="bold" fill="#172033">{value:.2f}</text>')
    return _svg_shell("Bayes updates belief", "P(class | feature₁, feature₂) = product of likelihoods × prior ÷ evidence", ''.join([
        '<path d="M120 300 H760 M120 300 V120" stroke="#94a3b8" stroke-width="2"/>',
        '<line x1="380" y1="205" x2="490" y2="205" stroke="#7c3aed" stroke-width="3"/>',
        '<path d="M480 197 L494 205 L480 213" fill="none" stroke="#7c3aed" stroke-width="3"/>',
        *bars,
        f'<text x="450" y="385" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#475569">features: (0.80, 0.70) vs (0.20, 0.30) · posterior = {posterior:.3f}</text>'
    ]))


def _evaluation_svg() -> str:
    labels = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    scores = [.95, .83, .62, .36, .79, .55, .41, .18, .09, .02]
    points = roc_points(labels, scores)
    auc = roc_auc(labels, scores)
    origin_x, origin_y, width, height = 120, 330, 600, 220
    path = ' '.join(f'{origin_x + x*width:.1f},{origin_y-y*height:.1f}' for x, y, _ in points)
    metric = threshold_metrics(labels, scores, .5)
    cells = [("TP", metric.tp, 0, 160, 150, "#e8f8f5"),
             ("FN", metric.fn, 4, 430, 150, "#fff2e8"),
             ("FP", metric.fp, 1, 160, 220, "#fff2e8"),
             ("TN", metric.tn, 0, 430, 220, "#e8f8f5")]
    matrix = ''.join(f'<rect x="{x}" y="{y}" width="220" height="52" rx="8" fill="{color}"/><text x="{x+110}" y="{y+21}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#475569">{label}: count {count}</text><text x="{x+110}" y="{y+43}" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="bold" fill="#172033">{count} × {cost} = {count * cost}</text>' for label, count, cost, x, y, color in cells)
    return _svg_shell("ROC curve and Cost matrix", f"ROC-AUC = {auc:.3f} · threshold = 0.50 · cost = FP×1 + FN×4 = {metric.cost:.0f}", ''.join([
        f'<line x1="{origin_x}" y1="{origin_y}" x2="{origin_x+width}" y2="{origin_y-height}" stroke="#e1e6f0" stroke-dasharray="7 7" stroke-width="2"/>',
        f'<path d="M{origin_x} {origin_y} L{origin_x+width} {origin_y-height}" stroke="#94a3b8" stroke-width="2"/>',
        f'<polyline points="{path}" fill="none" stroke="#db2777" stroke-width="5" stroke-linejoin="round"/>',
        f'<text x="{origin_x+width/2}" y="385" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#475569">false-positive rate</text>',
        f'<text x="78" y="220" transform="rotate(-90 78 220)" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#475569">true-positive rate</text>',
        '<text x="660" y="128" font-family="sans-serif" font-size="16" font-weight="bold" fill="#172033">At t = 0.50</text>',
        '<text x="660" y="151" font-family="sans-serif" font-size="13" fill="#475569">actual × predicted</text>', matrix
    ]))


def _gradient_svg() -> str:
    path = gradient_descent()
    x_min, x_max = -3, 7
    def gx(value: float) -> float: return 100 + (value-x_min) * 70
    def gy(value: float) -> float: return 330 - value * 8
    curve = ' '.join(f'{gx(x):.1f},{gy(quadratic(x)):.1f}' for x in [x_min+i*.1 for i in range(101)])
    steps = ' '.join(f'{gx(x):.1f},{gy(quadratic(x)):.1f}' for x in path)
    return _svg_shell("Gradient descent follows the slope", "f(x) = (x − 3)² + 1 · f′(x) = 2(x − 3) · xₙ₊₁ = xₙ − η f′(xₙ)", ''.join([
        '<path d="M100 330 H800 M100 330 V120" stroke="#94a3b8" stroke-width="2"/>',
        f'<polyline points="{curve}" fill="none" stroke="#0f766e" stroke-width="5"/>',
        f'<polyline points="{steps}" fill="none" stroke="#f97316" stroke-width="3" stroke-dasharray="5 4"/>',
        ''.join(f'<circle cx="{gx(x):.1f}" cy="{gy(quadratic(x)):.1f}" r="6" fill="#f97316"/>' for x in path),
        '<text x="310" y="385" font-family="sans-serif" font-size="15" fill="#475569">orange points: six updates toward minimum x = 3</text>'
    ]))


def _backprop_svg() -> str:
    values = backprop_demo()
    nodes = [("x = 2", 105, 150), ("w = 3", 105, 285), ("w×x", 290, 215),
             ("b = 1", 430, 335), ("+ b", 495, 215),
             (f"ŷ = {values['y_hat']:.1f}", 665, 215), (f"L = {values['loss']:.1f}", 830, 215)]
    circles = ''.join(f'<circle cx="{x}" cy="{y}" r="38" fill="#eef2ff" stroke="#3b6cf5" stroke-width="2"/><text x="{x}" y="{y+5}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="bold" fill="#172033">{label}</text>' for label, x, y in nodes)
    forward_edges = [(143, 150, 252, 215), (143, 285, 252, 225), (328, 215, 457, 215),
                     (468, 335, 476, 253), (533, 215, 627, 215), (703, 215, 792, 215)]
    arrows = ''.join(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#3b6cf5" stroke-width="3" marker-end="url(#arrow-forward)"/>' for x1, y1, x2, y2 in forward_edges)
    reverse = '<path d="M792 245 H703" fill="none" stroke="#d95d9b" stroke-width="3" marker-end="url(#arrow-backward)"/><path d="M627 245 H533" fill="none" stroke="#d95d9b" stroke-width="3" marker-end="url(#arrow-backward)"/><path d="M457 245 H328" fill="none" stroke="#d95d9b" stroke-width="3" marker-end="url(#arrow-backward)"/><path d="M476 245 C470 282 448 300 430 297" fill="none" stroke="#d95d9b" stroke-width="3" marker-end="url(#arrow-backward)"/><path d="M252 242 C210 270 175 285 143 285" fill="none" stroke="#d95d9b" stroke-width="3" marker-end="url(#arrow-backward)"/>'
    return _svg_shell("Backpropagation through an affine neuron", "x,w → multiply → + b → ŷ → L · local derivatives multiply backward", ''.join([
        '<defs><marker id="arrow-forward" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#3b6cf5"/></marker><marker id="arrow-backward" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#d95d9b"/></marker></defs>',
        circles, arrows, reverse,
        '<text x="450" y="120" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="bold" fill="#3b6cf5">forward pass →</text>',
        f'<text x="750" y="265" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#d95d9b">dL/dŷ = {values["dL_dy"]:.1f}</text>',
        '<text x="580" y="270" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#d95d9b">dŷ/d(w×x) = 1</text>',
        '<text x="450" y="300" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#d95d9b">dŷ/db = 1</text>',
        '<text x="205" y="260" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#d95d9b">d(w×x)/dw = x = 2</text>',
        f'<text x="450" y="382" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#db2777">backward results: dL/dw = {values["dL_dw"]:.1f} · dL/db = {values["dL_db"]:.1f}</text>',
        '<text x="450" y="405" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#71809a">pink arrows branch the loss gradient to both parameters</text>'
    ]))


if __name__ == "__main__":
    print(json.dumps(save_figures(), indent=2))
