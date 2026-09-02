# Project 04 final polish review

## Recommendation

**Conditional approve as an offline educational demonstration; do not present it as a validated recommendation or customer-behavior model.** The checked-in implementation is numerically sound for its 24-row synthetic fixture and gives users a useful support/rule threshold lab. The remaining work is primarily about making the statistical limits impossible to miss and making the basket explorer actually apply rules to the selected basket.

## What is already sound

- `analysis.py:16-54` performs explicit CSV schema, ID, empty-token, duplicate-ID, and duplicate-within-basket handling. The duplicate-product policy is documented in `README.md:29-31`.
- `analysis.py:81-97` implements level-wise Apriori with the expected anti-monotone subset pruning. The checked-in tests compare it with an independent brute-force oracle at five thresholds (`tests/test_analysis.py:14-21,37-40`).
- `analysis.py:99-120` uses the standard support, confidence, and lift formulas, and `tests/test_analysis.py:50-55` checks an exact rule (`{bread,jam} -> {butter}`): support `6/24`, confidence `1.0`, lift `24/13`.
- `scripts/generate_browser_data.py:15-21` generates the browser payload from the CSV, and `tests/test_analysis.py:97-105` checks Python/browser row parity. The current payload matches all 24 transaction IDs and six products.
- The UI is genuinely interactive at the code level: `app.js:106-115` recomputes itemsets and rules on support-slider input, and `app.js:117-135,138-143` lets users inspect every transaction and its local context. The static screenshot (`ui_screenshots/project-04.png`) shows a clear, readable visual hierarchy and explicit synthetic/local-data labeling.

## Prioritized improvements

### P0 — Add generalization/stability evidence or narrow the claims

**Evidence:** The fixture has only 24 synthetic baskets (`data/transactions.csv:1-25`). At the default support/confidence settings (`analysis.py:142-144`), the top rule is `{bread,jam} -> {butter}` with support `6/24`, confidence `1.0`, and lift about `1.846`. At 10% minimum support, rules can be based on only 3 of 24 baskets. `README.md:39` correctly calls out holdout validation and resampling stability as future production work, but the UI still presents “signals worth a closer look” without a stability or uncertainty view.

**Impact:** These are descriptive, in-sample associations. A perfect confidence score on six baskets is not evidence that the rule will predict future purchases, and lift can be inflated by small denominators. The current synthetic data cannot support claims about real customer behavior.

**Action:** Keep the existing synthetic-data disclaimer, but surface `n`, support count, and “exploratory/in-sample” beside the rule board. For a defensible analytic tool, add bootstrap rule-selection frequency/confidence intervals and, when timestamps are available, train-period mining plus later-period rule evaluation. Add a minimum absolute support-count control or floor.

### P1 — Make the basket explorer rule-driven, not only context-driven

**Evidence:** `index.html:87-99` describes the explorer as a way to test a signal against a basket, but `app.js:117-135` only counts contained frequent patterns and computes `P(candidate | any selected basket item)`. The page labels this estimand accurately in `index.html:99`, but it does not show which mined rules have antecedents contained in the selected basket or which consequents would be suggested.

**Impact:** A user selecting a basket cannot answer the most actionable association-mining question: “Which qualifying rules fire for this basket?” The current context bars are useful exploratory co-occurrence summaries, but they are not rule confidence, lift, or a recommendation score.

**Action:** Add a “Rules triggered by this basket” panel. Filter rules where the antecedent is a subset of the selected basket, display consequent, support count, confidence, lift, and the exact antecedent denominator, and sort/filter by the active thresholds. Keep the current `P(candidate | any selected basket item)` visualization as a separately named context view.

### P1 — Expose both thresholds and show the effective count threshold

**Evidence:** The Python entry point fixes minimum support at `0.25` and confidence at `0.60` (`analysis.py:142-144`). In the browser, `minConfidence` is hard-coded at `app.js:8`, while only support is interactive (`app.js:106-115`; `index.html:75-78`). With 24 baskets, a 25% support setting means at least 6 baskets, 30% means at least 8 baskets, and 55% means at least 14 baskets because support counts are discrete.

**Impact:** “Thresholds” are only partly explorable, and the current percentage slider hides discontinuities caused by a small denominator. The copy “Higher = fewer, more prevalent patterns” (`index.html:75`) is directionally correct but can be read as “stronger.”

**Action:** Add a confidence slider and, preferably, minimum lift and minimum support-count controls. Display `minimum support: 25% (at least 6/24 baskets)` and update the effective count live. Describe support as a prevalence filter; reserve “strength” for confidence/lift or a separately defined stability measure.

### P1 — Show the full rule set or make truncation and redundancy explicit

**Evidence:** At the default settings, the implementation produces 15 qualifying rules, but `app.js:99-103` renders only `rules.slice(0, 8)` and reports only the eight visible rules. The ranking in `analysis.py:120` and `app.js:77` is lift-first; the top three rules are different directions/partitions of the same six-basket `{bread,butter,jam}` pattern.

**Impact:** Users may mistake the eight cards for the complete result and see redundant variants crowd out other itemsets. Lift-first ranking also favors low-support rules unless the count floor is enforced.

**Action:** Show “8 of 15 rules” with an expand/paginate control, add sort choices for lift/support/confidence, and group directional rules by underlying itemset or provide a diversity-aware top-k view. Keep the raw complete result available for audit/export.

### P2 — Separate singleton prevalence from multi-item patterns

**Evidence:** Both the Python artifact (`analysis.py:122-124`) and live chart (`app.js:93-96`) rank all frequent itemsets together, including six singleton itemsets, nine pairs, and three triples at the default threshold. The card is titled “Most supported combinations” (`index.html:57`), although single products are included.

**Impact:** The most prevalent products can dominate a chart intended to communicate co-purchase structure. A learner may conflate “frequent product” with “association pattern.”

**Action:** Add an itemset-size filter or tabs for singletons, pairs, and triples; make “all itemsets” explicit when that is the chosen view. Default the association-focused view to size at least two while retaining singleton prevalence as a baseline.

### P2 — Tighten API invariants, browser parity, and documentation claims

**Evidence:** `association_rules` validates numeric ranges and missing subsets (`analysis.py:101-116`) but cannot verify that an arbitrary caller-provided `frequent` mapping contains supports from one consistent transaction universe. The browser independently reimplements mining (`app.js:36-77`), while tests currently verify row parity but not equality of browser/Python itemset and rule outputs (`tests/test_analysis.py:97-105`). Finally, `README.md:47` says “pytest passed 3/3,” but the current test file contains substantially more cases and the review environment did not have pytest installed.

**Impact:** The normal `apriori(...) -> association_rules(...)` path is correct, but future changes could make the two implementations disagree or leave the reproducibility note stale.

**Action:** Add exact formula/invariant tests for support, confidence, lift, boundary thresholds, and tie ordering; add a lightweight browser execution test or shared generated result artifact for Python/browser output parity; and update the README verification line to report the actual test command/result from the pinned environment. Keep `python scripts/generate_browser_data.py --check` in CI.

## UI/data-science assessment

The page is a strong presentation layer for a small offline lab: it labels the data synthetic, shows denominators beside displayed percentages, explains all three core metrics, updates itemsets/rules from a control, and supports transaction selection. Its main weakness is not lack of polish but incomplete analytical affordance. It currently explores prevalence and a broad co-occurrence context; it does not yet let a user vary confidence, inspect effective count thresholds, evaluate stability, or see rules triggered by the selected basket.

## Verification performed

- `python3 scripts/generate_browser_data.py --check`: passed; generated browser data is current.
- Independent source inspection of `data/transactions.csv`, `data/transactions.js`, `analysis.py`, `app.js`, `index.html`, tests, README, and the existing Project 04 screenshot.
- Independent metric/count calculation: 24 baskets, 6 products, 18 frequent itemsets and 15 rules at 25% support / 60% confidence; itemset counts by size are 6 singletons, 9 pairs, and 3 triples.
- Independent Apriori/brute-force parity is already covered by `tests/test_analysis.py:37-40` across 10%, 25%, 30%, 50%, and 70% support.
- `node --check app.js`, `node --check data/transactions.js`, and `python3 -m py_compile ...`: passed.
- `python3 -m pytest -q` could not run in the current system environment because pytest is not installed; no dependency installation was performed.
- No source code, generated artifact, PR, or push was created by this review.

## Implementation follow-up

The prioritized polish items were implemented after this review. The UI now exposes minimum support, minimum confidence, and a minimum absolute support-count floor, reports the effective whole-basket threshold, filters itemsets by size, and shows the complete rule count with sort/expand controls. Rule cards display exploratory/in-sample status plus absolute support, antecedent, and consequent denominators.

The basket explorer now includes a **Rules triggered by this basket** panel: qualifying rules fire when their antecedent is contained in the selected basket, with consequent, confidence, lift, and the exact antecedent denominator shown. The existing `P(candidate | any selected basket item)` bars remain available as a separately labeled context view and are not presented as rule confidence.

Verification was expanded with discrete support-count tests, inconsistent-support invariant checks, and a Node-based browser/Python mining parity test. Generated-data, syntax, compilation, direct analytical, mock-DOM, and browser/Python parity checks pass after regeneration. The full pytest suite is ready to run with the pinned requirements, but this host’s system Python does not currently have the `pytest` module installed.
