# Project 08 — Data Science Visual Foundations

An offline-friendly, GitHub Pages-ready mini curriculum for beginner data-science students. The page is designed as a polished learning UI: a responsive lesson rail, progress cues, clear math callouts, live simulation panels, metric cards, quizzes, and interview prompts. It teaches four ideas with live, deterministic simulations:

1. **Naive Bayes** — update a prior with evidence and see the posterior move.
2. **Model evaluation** — change a threshold and inspect the confusion matrix, precision/recall, ROC curve/AUC, and an explicit cost matrix.
3. **Derivatives and gradient descent** — visualize a tangent slope and watch a parameter descend a quadratic loss.
4. **Chain rule and backpropagation** — step through a tiny one-neuron affine computation graph and see each local derivative multiply into a gradient.

Every lesson includes an intuition paragraph, the governing math, a live interaction, a check-your-understanding quiz, and interview questions. The page has no network dependency, external fonts, or build step; it can be opened directly as `index.html` or deployed to GitHub Pages.

## Run

```bash
python3 -m src.generate_plots
python3 -m pytest -q
open index.html                    # macOS; or double-click it
```

## UI and screenshot instructions

1. Open `index.html` directly in a browser. For a clean hero screenshot, use a desktop viewport around 1440 × 900 and keep the page at the default `01 · Naive Bayes` lesson.
2. Capture the first viewport for the visual overview: it includes the sticky project bar, learning-path rail, hero message, toolkit card, and the start of the active lesson.
3. Capture a lesson interaction by selecting a lesson in the left rail, then moving one or more sliders. The SVG visual, output values, and explanatory note update immediately.
4. For an interaction-focused screenshot, scroll until the simulation panel, legend, and quiz are visible together. Select a quiz answer and press **Check answer** to show the feedback state.
5. For a mobile screenshot, use a narrow viewport around 390 × 844. The lesson rail becomes a horizontal strip, cards stack vertically, and controls collapse to a single column on very narrow screens.

The visual language is intentionally self-contained in `index.html`: system fonts, inline CSS, and inline SVG keep screenshots deterministic and GitHub Pages deployment simple.

The plot command creates four snapshots in `artifacts/` (PNG when Matplotlib is installed, otherwise dependency-free SVG). The browser page uses inline SVG so it remains portable; the snapshots use concept-specific labels, values, and geometry so they remain audit-friendly without optional plotting packages.

## Project layout

- `index.html` — responsive static interactive curriculum; suitable for GitHub Pages and screenshot capture.
- `app.js` — browser-side simulations kept separate from the page shell for readable, testable parity with the Python calculations.
- `src/concepts.py` — pure-Python reference calculations used by the page design and tests.
- `src/generate_plots.py` — deterministic plot/screenshot generator.
- `tests/test_concepts.py` — numerical invariants, edge cases, ROC-AUC, and concept-specific artifact tests.
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
- **Results/artifacts:** Four dependency-free SVG snapshots and the manifest are checked in; the backprop snapshot mirrors the live graph with explicit bias and branching reverse-gradient arrows.
- **Verification:** Run `python3 -m pytest -q` after installing `requirements.txt`; lightweight syntax, numerical, HTML-structure, and fallback-artifact checks are also documented by the test suite.
