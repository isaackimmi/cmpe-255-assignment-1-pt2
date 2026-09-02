# Final polish review — Project 08

Scope: `08_datascience_visual_mastery`. This is a static-source and artifact audit of the current project state. The codebase was not modified beyond adding this review. Per the task constraint, no local server or browser automation was used, so runtime behavior is assessed from the DOM, event wiring, and render functions rather than from a live browser session.

Severity:

- **P1** — material mathematical or teaching-claim defect in a core lesson.
- **P2** — important fidelity, robustness, or interaction gap worth fixing before calling the artifact final.
- **P3** — polish, maintainability, or test-coverage improvement.

## Executive assessment

The current active implementation is substantially stronger than the older `DS_REVIEW.md` snapshot. The core scalar calculations are correct for the stated toy examples: two-feature Bayes updating, threshold confusion counts, ROC-AUC, the quadratic derivative/update, and one-neuron affine backpropagation all agree between the Python reference layer and the browser formulas. The page is also structurally a real interactive curriculum, not merely a landing page: it contains five Bayes sliders, a threshold slider, two calculus sliders, two backprop sliders, lesson navigation, quiz feedback, SVG redraw functions, and explanatory text that is regenerated from the control values.

**Recommendation: conditional GO.** The project meets the assignment scope and is suitable for a demo or submission after targeted polish, but I recommend fixing the three P2 fidelity issues below before describing it as a fully rigorous visual curriculum. There are no confirmed P1 mathematical defects in the current active path. Because runtime execution was intentionally not performed, a final manual smoke test should still be done after any edits.

## Findings

### [P2] Backpropagation gradients are described but not drawn as a backward graph

Evidence:

- The active graph creates the correct forward topology, including separate `x` and `w` inputs, `w×x`, `+ b`, `ŷ`, and `L` nodes at [`app.js:163`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:163).
- Every rendered edge is built with the same blue stroke and forward arrow marker at [`app.js:165`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:165)–[`app.js:168`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:168). The backward values appear only in a pink text line; there are no reverse arrows or edge-local derivative labels.
- The copy promises that the graph will show the loss gradient branching back to both parameters at [`app.js:184`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:184), while the legend in [`index.html:40`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/index.html:40) claims a separate backward-gradient visual channel.

Impact: The forward computation is faithful, but the key visual intuition of backpropagation—one output gradient flowing backward and splitting into parameter gradients—is not actually visible. A learner sees a forward graph plus a sentence about gradients, rather than a chain-rule graph.

Action: Add a distinct pink reverse-arrow marker and draw reverse paths from `L → ŷ → +b`, then branch to `b` and `w×x → w`. Label the local factors on or beside those edges, including `dL/dŷ`, `dŷ/d(w×x)`, `d(w×x)/dw`, and `dŷ/db`. Keep the numeric results already computed by `updateBp`.

### [P2] The dependency-installed PNG path is not parity-correct with the current backprop lesson

Evidence:

- The Matplotlib branch uses a four-point horizontal sketch with labels `x`, `w`, `w·x+b`, and `loss` at [`src/generate_plots.py:54`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/generate_plots.py:54)–[`src/generate_plots.py:60`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/generate_plots.py:60).
- That branch does not call `backprop_demo`, does not render a separate bias input, and does not render numeric backward derivatives. By contrast, the dependency-free SVG path does include `w×x`, `+ b`, the affine-model wording, and derivative values at [`src/generate_plots.py:159`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/generate_plots.py:159)–[`src/generate_plots.py:169`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/generate_plots.py:169).
- The project advertises both PNG and SVG generation in [`README.md:30`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/README.md:30).

Impact: A machine with the pinned NumPy/Matplotlib dependencies can produce a less accurate backprop artifact than a minimal install. This is a reproducibility and teaching-fidelity mismatch.

Action: Make the PNG renderer use the same faithful graph model as the SVG renderer, including `backprop_demo()` values and a visible backward branch, or deliberately make both artifact paths point to one shared SVG renderer. Add a test that checks the generated artifact for `+ b`, `dL/dw`, and `dL/db` in either format.

### [P2] The learning-rate control cannot demonstrate the failure mode described by the lesson

Evidence: The lesson asks what happens when a learning rate is too large at [`index.html:38`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/index.html:38), but the active slider is constrained to `0.03`–`0.35` in that same control. For `f(x)=(x−3)^2+1`, the update factor is `1−2η`; throughout this range it remains positive, so the path converges without crossing the minimum. The update implementation is visible at [`app.js:145`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:145) and [`app.js:146`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:146).

Impact: The interview explanation mentions overshooting, oscillation, or divergence, but the live control only shows stable descent. The learner cannot experimentally connect the explanation to the plot.

Action: Extend the control above `η=0.5` so oscillation is visible, and optionally above `η=1` with a bounded path/warning so divergence is explicit. Update the note when the selected rate is unstable, and ensure the y-axis remains readable for the wider path.

### [P3] Cost matrix cells show costs but not each cell's contribution to total cost

Evidence: The active SVG helper labels each cell as `count · cost` at [`app.js:109`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:109) and [`app.js:122`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:122), while the summary only expands FP and FN at [`app.js:132`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:132).

Impact: The matrix is present and the arithmetic is valid for zero TP/TN costs, but the visual does not show the general rule `Σ count(cell) × cost(cell)`. That weakens the explanation of why a cost matrix is more general than a single weighted-error scalar.

Action: Put the product, such as `FN: 1 × 4 = 4`, inside each cell and show the total as the sum of all four cell contributions. If desired, add editable FP/FN cost controls so the threshold tradeoff has a visibly stakeholder-defined objective.

### [P3] Evaluation thresholds omit the two endpoint decision states

Evidence: The threshold slider is limited to `0.05`–`0.95` at [`index.html:36`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/index.html:36), while the ROC renderer includes explicit `(0,0)` and `(1,1)` endpoints at [`app.js:92`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:92) and [`app.js:99`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:99).

Impact: The curve communicates all-threshold behavior, but the learner cannot select the all-negative or all-positive confusion-matrix states from the control. Those states are useful for explaining undefined precision/recall and why metrics need denominators.

Action: Allow thresholds from `0` to `1` (or add explicit endpoint buttons) and label undefined ratios as `undefined`, which the active formatter already supports at [`app.js:31`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:31) and [`app.js:33`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:33).

### [P3] An inert legacy script preserves contradictory old teaching logic

Evidence: The active page loads `app.js` at [`index.html:56`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/index.html:56), but a large obsolete implementation remains as `type="text/plain"` at [`index.html:44`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/index.html:44). That inert copy contains the former one-feature Bayes display, one-point ROC view, and unbranched backprop sketch.

Impact: It does not execute in a normal browser, but it creates two competing sources of truth for reviewers and future maintainers. Static audits can also mistake it for the active implementation.

Action: Remove the legacy block after confirming no external tooling depends on it, or replace it with a short comment naming the active file and the reason for the split.

### [P3] Long Naive Bayes feature lists can underflow in the reference calculation

Evidence: Feature likelihood products are accumulated directly with `math.prod` at [`src/concepts.py:34`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:34)–[`src/concepts.py:35`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:35). The README already correctly limits the lesson to small synthetic numbers at [`README.md:43`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/README.md:43).

Impact: The current toy values are safe, but the function's public one-or-more-feature contract can silently collapse very small products to zero for realistic feature counts.

Action: Either document the deliberately toy-only scope in the function docstring or compute in log space with a stable normalization. Add a long-feature regression test if the broader API is retained.

## What is already correct and complete

- Bayes uses two feature likelihood products in the active browser code at [`app.js:35`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:35)–[`app.js:39`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:39), and the Python implementation validates aligned probability lists at [`src/concepts.py:19`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:19)–[`src/concepts.py:40`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:40).
- Threshold metrics correctly compute TP/FP/TN/FN and weighted cost at [`src/concepts.py:98`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:98)–[`src/concepts.py:110`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:110); the active UI redraws both confusion and cost matrices at [`app.js:139`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:139)–[`app.js:140`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:140).
- ROC points include endpoints and the active UI computes and labels AUC at [`app.js:102`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:102)–[`app.js:107`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:107) and [`app.js:128`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:128)–[`app.js:140`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:140).
- The calculus renderer derives its y mapping from a bounded range that contains the full slider domain at [`app.js:148`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:148)–[`app.js:155`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:155); the earlier endpoint-clipping concern in `DS_REVIEW.md` is no longer applicable to the active code.
- The Python sigmoid is sign-stable for finite inputs at [`src/concepts.py:175`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:175)–[`src/concepts.py:182`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/src/concepts.py:182), and the active backprop arithmetic correctly uses `L=½(error)^2`, `dL/dw=error·x`, and `dL/db=error` at [`app.js:159`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:159)–[`app.js:162`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:162).
- The active event wiring is substantive: dynamically added Bayes controls are wired at [`app.js:28`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:28), navigation and quiz actions at [`app.js:191`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:191)–[`app.js:209`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:209), and all simulation inputs at [`app.js:212`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:212)–[`app.js:218`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/app.js:218).

## Checks performed

- `python3 -m compileall -q src tests`: **PASS**.
- Direct Python probes: **PASS** for Bayes posterior `0.9032258`, default confusion counts `(TP=3, FP=2, TN=4, FN=1)`, default cost `6`, ROC-AUC `0.8333333`, gradient-descent loss reduction, affine backprop derivatives, and stable sigmoid behavior.
- Artifact inspection: **PASS** for the checked-in dependency-free SVGs being concept-specific; the manifest points to all four SVG artifacts.
- `python3 -m pytest -q`: **NOT RUNNABLE** in this environment because `pytest` is not installed, despite the pinned dependency in [`requirements.txt:3`](/Users/isaackim/Desktop/MSSE%20DS/Fall%202026/CMPE%20255/HW/cmpe-255-assignment-1-pt2/08_datascience_visual_mastery/requirements.txt:3).
- Browser/server verification: **NOT RUN** by instruction. Static wiring strongly supports genuine interaction, but a final manual check should exercise one control in each lesson, both threshold endpoints, all quiz buttons, and the mobile layout.

## Suggested final order

1. Draw the actual backward gradient paths in the active backprop SVG.
2. Bring the Matplotlib backprop artifact into parity with the active/SVG lesson.
3. Widen the learning-rate experiment and add an instability explanation.
4. Apply the P3 teaching and maintainability polish, then run the pinned pytest suite and a short manual UI smoke test.
