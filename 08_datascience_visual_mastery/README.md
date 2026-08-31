# Project 08 — Data Science Visual Foundations

An offline-friendly, GitHub Pages-ready mini curriculum for beginner data-science students. It teaches four ideas with live, deterministic simulations:

1. **Naive Bayes** — update a prior with evidence and see the posterior move.
2. **Model evaluation** — change a threshold and inspect the confusion matrix, precision/recall, ROC point, and a simple cost matrix.
3. **Derivatives and gradient descent** — visualize a tangent slope and watch a parameter descend a quadratic loss.
4. **Chain rule and backpropagation** — step through a tiny two-layer computation graph and see each local derivative multiply into a gradient.

Every lesson includes an intuition paragraph, the governing math, a live interaction, a check-your-understanding quiz, and interview questions. The page has no network dependency and can be opened directly as `index.html` or deployed to GitHub Pages.

## Run

```bash
python3 -m src.generate_plots
python3 -m pytest -q
open index.html                    # macOS; or double-click it
```

The plot command creates four snapshots in `artifacts/` (PNG when Matplotlib is installed, otherwise dependency-free SVG). The browser page uses inline SVG so it remains portable; the snapshots are audit-friendly views of the same concepts.

## Project layout

- `index.html` — static interactive curriculum; suitable for GitHub Pages.
- `src/concepts.py` — pure-Python reference calculations used by the page design and tests.
- `src/generate_plots.py` — deterministic plot/screenshot generator.
- `tests/test_concepts.py` — numerical invariants, edge cases, and artifact tests.
- `artifacts/` — generated plots and `manifest.json`.

## Reproducibility and responsible interpretation

The examples use deliberately small synthetic numbers so that students can verify the math by hand. They are not claims about a real medical, financial, or operational dataset. Naive Bayes assumes conditional independence; threshold metrics depend on prevalence and the selected cutoff; ROC-AUC does not encode business costs; gradient descent is shown on a convex toy loss; and the backpropagation graph is intentionally tiny. Production decisions require domain validation, uncertainty analysis, calibration, and a cost model agreed with stakeholders.

## Documented deviation from the original prompt

The prompt asks for a “live simulation” and a GitHub.io-ready page. This reproduction uses a single static HTML file with browser-native JavaScript/SVG rather than a heavier React dashboard, so it can run offline and publish directly on GitHub Pages. The PNGs are generated locally instead of captured from a browser. The learning coverage and requested interactions are preserved; framework-specific styling and external datasets are intentionally omitted.

## Original prompt

> `/teamwork-preview lets do another project - teach beginner data science students in an excellent way with deep intuition and rigorous math and visual intuition and live simulation on:`
>
> 1. naive bayes
> 2. evaluation of model - confusion matrix, type 1 and type 2 errors, roc-auc, cost matrix, tradeoff between precision and recall
> 3. differential calculus, derivatives and how they connect to gradient descent
> 4. chain rule and how it connects to backpropagation
> include quizzes for each concept and interview prep questions. also create a github.io ready page for this project.
## Integration verification

- **Prompt alignment:** Public Project 08 asks for Naive Bayes, evaluation, calculus/gradient descent, backpropagation, quizzes, interview prep, live simulation, and GitHub Pages readiness; all are represented.
- **Results/artifacts:** Four snapshots and manifest are present; pytest passed 6/6.
- **Issue/resolution:** Fixed a manifest path bug when pytest redirects output outside the repository.
