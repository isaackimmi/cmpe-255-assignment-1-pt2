# Data-science robustness review

Scope: Project 08 (`08_datascience_visual_mastery`). This review covers the Python reference calculations, browser simulations, generated artifacts, and tests. No source code was changed.

Severity legend: **P1** is a material correctness or teaching-claim problem in a core lesson; **P2** is an important robustness, coverage, or visual-fidelity gap; **P3** is a minor polish issue.

## Findings

### [P1] ROC-AUC is taught in the quiz but is neither computed nor visualized

Evidence:

- `README.md:6,53` lists ROC-AUC as part of model evaluation.
- `index.html:36` labels the lesson “ROC-AUC” and asks “What does ROC-AUC summarize?”, but `index.html:50` computes only the current cutoff's FPR and recall and draws a diagonal random baseline plus one point.
- `src/generate_plots.py:35-46` generates a precision-recall curve, not an ROC curve, and has no AUC calculation.

Impact: A learner can answer the quiz correctly without ever seeing the quantity being assessed. The static artifact titled “Threshold tradeoff” also cannot support an ROC-AUC interpretation. The fixed example's ranking AUC is approximately 0.833, but that value is absent.

Fix: Build the ROC points from thresholds including the all-negative and all-positive endpoints, sort by FPR, integrate with the trapezoidal rule, and display/label the resulting AUC. Keep the current cutoff marker as a separate point. If the intended plot is precision-recall, label it explicitly and add a separate ROC panel.

### [P1] The ROC point is plotted with a different scale from its axes

Evidence: `index.html:50` draws the ROC axes from `(423,232)` to `(733,54)` (width 310, height 178), but maps the current point with `423 + fpr*280` and `232 - recall*155`. For the default data at threshold 0.50, the code computes TP=3, FP=2, TN=4, FN=1, hence FPR=1/3 and TPR=0.75. The point is placed at approximately `(516.3,115.8)`; the same axes imply approximately `(526.3,98.5)`.

Impact: Even the one displayed ROC point does not represent the numeric FPR/TPR at the coordinates shown by the axes, so the visual teaches the wrong geometric location.

Fix: Define one `plotX`/`plotY` origin and one shared width/height, use those constants for both the baseline and all ROC points, and add 0/0.5/1 tick labels so the mapping is auditable.

### [P2] The advertised cost matrix is reduced to an unexplained scalar

Evidence:

- `README.md:6,53` and `index.html:36` promise a cost matrix.
- `index.html:36,50` communicate only “false negative costs four times a false positive” and the scalar `cost = FP + 4*FN`; no four-cell matrix for predicted/actual outcomes is rendered.
- `src/concepts.py:49-50` likewise stores only the aggregate cost and accepts no true-positive/true-negative costs or matrix representation.

Impact: The arithmetic is a valid weighted error total under the stated FP=1/FN=4 convention, but learners do not see that costs are assigned to outcome cells and that different stakeholder choices change the objective. The lesson therefore does not meet its own cost-matrix claim.

Fix: Render an explicit actual-by-predicted cost matrix, label the four cell costs, and show the aggregate as the sum of cell counts times cell costs. Keep the scalar as a derived expected cost, not as the matrix itself.

### [P1] The backpropagation “computation graph” omits the bias and addition operation

Evidence:

- `index.html:40` presents `ŷ = wx + b` and exposes both `w` and `b` controls.
- `index.html:52` renders only the nodes `x`, `w`, `ŷ`, and `L`, with a linear `x → w → ŷ → L` chain. There is no `b` node, multiplication node, or addition node, although the text reports `∂L/∂b`.
- `README.md:8` calls this a “two-layer computation graph”; `src/concepts.py:71-78` actually implements one affine unit followed by squared error, not a two-layer neural network.

Impact: The displayed topology is mathematically inconsistent with the formula and hides exactly the branching/addition structure that makes the chain rule useful. It also overstates the depth of the example.

Fix: Render a faithful graph such as `x,w → multiply → + b → ŷ → loss`, with `b` as a second input. Show the local factors (`dL/dŷ`, `dŷ/d(multiply)`, `d(multiply)/dw`, `dŷ/db`) and the resulting `dL/dw`, `dL/db`; either rename the example as a one-neuron affine model or implement an actual hidden layer before calling it two-layer.

### [P1] The dependency-free artifact fallback is not a snapshot of the concepts

Evidence:

- `src/generate_plots.py:73-93` writes the same generic cubic Bézier curve and the text “generated snapshot” for all four fallback SVGs; it does not use Bayes, the metric data, the quadratic, or the backprop values.
- The current `artifacts/manifest.json:2-5` points to those SVGs. The environment check found NumPy/Matplotlib unavailable, so this is the active output path.
- `README.md:30` describes the snapshots as audit-friendly views of the same concepts.

Impact: A clean/minimal install gets four polished-looking but semantically fabricated plots. This directly conflicts with the offline/dependency-free claim and makes the artifact set unsafe for teaching or review.

Fix: Implement real dependency-free SVG renderers for each concept (or make the fallback visibly labeled as a placeholder and remove the “same concepts/audit-friendly” claim). Add artifact assertions that check concept-specific labels/data, not just file existence.

### [P1] `sigmoid` overflows on valid finite inputs

Evidence: `src/concepts.py:81-82` computes `math.exp(-value)` directly. A direct check of `sigmoid(-1000)` raises `OverflowError: math range error` even though the mathematical sigmoid is well-defined and finite (approximately 0).

Impact: Any future lesson or caller using a moderately large negative logit can crash instead of returning a stable probability. This is a numerical-stability defect in the reference layer.

Fix: Use a sign-stable implementation (for example, compute `1/(1+exp(-z))` for `z >= 0` and `exp(z)/(1+exp(z))` otherwise), and test large positive/negative values plus finiteness and monotonicity.

### [P2] Zero-probability Bayes evidence is silently assigned posterior 0

Evidence: `src/concepts.py:15-17` returns `0.0` whenever the evidence denominator is zero. For `prior=0.5`, `likelihood_positive=0`, and `likelihood_negative=0`, `P(E)=0`, so `P(class|E)` is undefined—not 0. The browser avoids this exact state only because `index.html:34` sets positive likelihood minimum 0.05 and negative likelihood minimum 0.01. Existing tests in `tests/test_concepts.py:10-13` cover only ordinary positive likelihoods.

Impact: The reference calculation can teach a false posterior for impossible evidence and masks an invalid input/state.

Fix: Raise a clear error or return an explicit undefined result when the normalizer is zero; add boundary tests for `(0,0)`, one-sided zero likelihoods, and valid prior endpoints. If multiple evidence features are added, use log-space products to avoid underflow.

### [P2] The “Naive Bayes” interaction demonstrates only one-feature Bayes

Evidence: `src/concepts.py:8-17` accepts one likelihood pair, and `index.html:34,48` exposes one evidence event `E` with `P(E|class)` and `P(E|not class)`. No product of two or more conditionally independent feature likelihoods is shown.

Impact: The single-feature calculation is correct, but it does not demonstrate the defining naive-independence assumption or the multiplication across features. Beginners may leave with “Naive Bayes is Bayes with one likelihood” as the mental model.

Fix: Add at least two feature likelihood pairs and show the numerator as a product, or rename the lesson to binary Bayes updating and explicitly state that the Naive Bayes extension is omitted. Include a correlated-feature warning and, for realistic feature counts, a log-odds/log-probability implementation.

### [P2] Threshold metrics accept malformed labels and non-finite scores without error

Evidence: `src/concepts.py:37-50` checks only length, non-emptiness, and threshold range. It never validates that labels are in `{0,1}`, scores are finite, or costs are finite/nonnegative. A direct check of `threshold_metrics([2,0],[0.9,0.1],0.5)` returns counts summing to 1 rather than 2; a NaN score is silently treated as not predicted positive.

Impact: Invalid inputs can produce internally inconsistent confusion matrices and apparently valid metrics. The threshold's `[0,1]` contract also assumes probability scores, but the score scale is not documented or enforced.

Fix: Validate binary labels, aligned finite scores, and finite costs. Either enforce scores in `[0,1]` or document arbitrary score units and remove the probability-specific threshold restriction. Add tests for invalid labels, NaN/Inf scores, negative costs, and class-absence cases.

### [P2] Undefined precision/recall/FPR cases are silently conflated with zero

Evidence: `src/concepts.py:46-48` returns `0.0` when a metric denominator is zero. That is a common library convention, but it is not the mathematical value of an undefined ratio and is not disclosed in the UI. The current fixture avoids some cases because `index.html:36,50` uses a fixed balanced-enough dataset and restricts the threshold to 0.05–0.95.

Impact: Students may interpret zero precision as “none of the predicted positives were correct” when there were no predicted positives, or zero recall/FPR as measured performance when the relevant class is absent.

Fix: Expose a documented `zero_division` policy, or return `None`/NaN with an “undefined” label in the teaching UI. Add tests with no predicted positives, no actual positives, and no actual negatives.

### [P2] Valid calculus slider values can place the curve and points outside the SVG viewport

Evidence: `index.html:38` allows `x` from -2.5 to 7.5. `index.html:51` maps the quadratic with `gy(v)=278-((v-3)**2+1)*18`; at either endpoint the loss is 31.25 and the y coordinate is -284.5, outside the `viewBox="0 0 800 330"`.

Impact: Dragging to valid slider endpoints clips the curve, tangent, and/or descent points, weakening the claim that the live plot shows the loss landscape across the whole control range.

Fix: Compute y-axis bounds from the plotted x range and add padding, or constrain the x range to the visible y domain. Add a browser-level smoke check at both slider endpoints.

## Checks run

- `python3 -m compileall -q src tests`: **PASS**.
- Browser JavaScript extraction plus `new Function(...)` parse: **PASS**.
- Direct numerical probes: confirmed the default evaluation counts (TP=3, FP=2, TN=4, FN=1), the ROC scale mismatch, `sigmoid(-1000)` overflow, zero-evidence Bayes returning 0, and malformed-label metrics being silently dropped.
- `python3 -m pytest -q`: **NOT RUNNABLE in the review environment** because `pytest` is not installed; NumPy/Matplotlib are also absent. The pinned versions are listed in `requirements.txt:1-3`.
- Fallback generation in a temporary directory: completed and confirmed all four SVGs contain the generic “generated snapshot” placeholder.

## Overall assessment

The ordinary-path scalar formulas for one-feature Bayes, the confusion counts, the quadratic derivative/update, and the affine-model MSE derivatives are correct for their constrained defaults. The main risks are the missing/misrepresented ROC-AUC and cost-matrix lessons, the structurally incorrect backprop graphic, the semantically fake fallback artifacts, and insufficient numerical/input edge-case handling. These should be addressed before presenting the project as a rigorous data-science curriculum.
