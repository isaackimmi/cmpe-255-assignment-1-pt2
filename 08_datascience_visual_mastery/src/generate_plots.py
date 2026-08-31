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

from .concepts import gradient_descent, naive_bayes_posterior, quadratic


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

    thresholds = np.linspace(0.05, 0.95, 19)
    true = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    scores = np.array([0.95, 0.83, 0.62, 0.36, 0.79, 0.55, 0.41, 0.18, 0.09, 0.02])
    recall, precision = [], []
    for t in thresholds:
        pred = scores >= t
        tp = ((true == 1) & pred).sum(); fp = ((true == 0) & pred).sum()
        fn = ((true == 1) & ~pred).sum()
        recall.append(tp / (tp + fn)); precision.append(tp / (tp + fp) if tp + fp else 0)
    fig, ax = plt.subplots(figsize=(6, 3.4)); ax.plot(recall, precision, "o-", color="#db2777")
    ax.set(xlabel="Recall", ylabel="Precision", title="Threshold tradeoff")
    fig.tight_layout(); fig.savefig(OUT / "evaluation.png", dpi=150); plt.close(fig)

    path = gradient_descent(); grid = np.linspace(-3, 7, 200)
    fig, ax = plt.subplots(figsize=(6, 3.4)); ax.plot(grid, [quadratic(v) for v in grid], color="#0f766e")
    ax.plot(path, [quadratic(v) for v in path], "o-", color="#f97316")
    ax.set(xlabel="Parameter x", ylabel="Loss f(x)", title="Gradient descent follows the slope")
    fig.tight_layout(); fig.savefig(OUT / "gradient_descent.png", dpi=150); plt.close(fig)

    labels = ["x", "w", "w·x+b", "loss"]; xs = [0.1, 0.35, 0.62, 0.9]
    fig, ax = plt.subplots(figsize=(6, 2.6)); ax.scatter(xs, [0.5] * 4, s=800, c=["#8b5cf6"] * 4)
    for pos, label in zip(xs, labels): ax.text(pos, .5, label, ha="center", va="center", color="white", weight="bold")
    ax.annotate("forward pass →", (0.2, .68), (0.75, .68), arrowprops={"arrowstyle": "->", "color": "#475569"})
    ax.annotate("← gradients flow back", (0.75, .32), (0.2, .32), arrowprops={"arrowstyle": "->", "color": "#dc2626"})
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
    """Keep the artifact command useful before optional plotting packages exist."""
    specs = {
        "naive_bayes.svg": ("Bayes updates belief", "Prior → posterior after evidence", "#2563eb"),
        "evaluation.svg": ("Threshold tradeoff", "Precision and recall change with the cutoff", "#db2777"),
        "gradient_descent.svg": ("Gradient descent", "Steps move toward the minimum", "#f97316"),
        "backpropagation.svg": ("Backpropagation", "Forward values and backward gradients", "#7c3aed"),
    }
    for filename, (title, subtitle, color) in specs.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
<rect width="900" height="420" fill="#f8fafc"/><text x="50" y="68" font-family="sans-serif" font-size="30" font-weight="bold" fill="#172033">{title}</text>
<text x="50" y="105" font-family="sans-serif" font-size="18" fill="#64748b">{subtitle}</text>
<path d="M90 330 H820 M90 330 V145" stroke="#94a3b8" stroke-width="2"/>
<path d="M120 290 C250 145 360 145 470 280 S680 340 790 165" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
<circle cx="470" cy="280" r="13" fill="{color}"/><text x="470" y="370" text-anchor="middle" font-family="sans-serif" font-size="17" fill="#475569">generated snapshot</text></svg>'''
        (OUT / filename).write_text(svg)
    manifest = {
        filename: str((OUT / filename).relative_to(ROOT)) if (OUT / filename).is_relative_to(ROOT) else str(OUT / filename)
        for filename in specs
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(save_figures(), indent=2))
