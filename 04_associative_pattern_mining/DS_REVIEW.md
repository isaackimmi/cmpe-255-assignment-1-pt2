# Project 04 data-science robustness review

## Scope and verdict

Reviewed transaction construction, Python and browser Apriori implementations, support/confidence/lift calculations, threshold behavior, tests, reproducibility claims, and UI semantics. No numerical Apriori or association-metric error was found for the checked-in data: an independent brute-force implementation matched Python at five thresholds, and the Python/browser transaction contents matched.

The project is suitable as a small, transparent educational demonstration. It is not yet robust enough to support claims about customer behavior or stable recommendation signals. The main risks are metric interpretation, sample validation, duplicated data sources, and a stale UI metadata label.

Severity: **High** = can materially invalidate the analysis; **Medium** = materially misleading or limits defensibility; **Low** = robustness/maintenance gap with limited impact on the checked-in example.

## Findings

### [Medium] UI reports inconsistent product metadata

**Evidence:** `data/transactions.csv:2-25` contains six distinct products: bread, milk, eggs, butter, jam, and coffee. `index.html:45` hardcodes `5` and lists only `bread · milk · eggs · coffee · jam`, omitting butter. `app.js:99-100` later replaces only the number with the computed six, leaving the stale footnote in place. The rendered screenshot therefore shows `6` alongside a five-product list.

**Impact:** The headline summary is internally inconsistent and undermines confidence in the displayed dataset description. The static HTML is also wrong before JavaScript runs.

**Fix:** Generate both the count and product list from the same runtime dataset, or update the footnote dynamically from `itemUniverse`. Add a UI/data-contract check that asserts the displayed product metadata equals the CSV-derived metadata.

### [Medium] “Co-pick context” is not the metric the UI says it is

**Evidence:** `app.js:147-150` computes, for each candidate product, the fraction of candidate-containing baskets that contain *at least one* product from the selected basket:

`count(candidate and any selected-basket item) / count(candidate)`.

This is neither the share of selected-basket products that co-occur, nor `P(candidate | selected basket)`, nor a standard rule confidence/lift. For T001, an independent calculation gives 100% for each of butter, coffee, and jam, so the displayed bars cannot distinguish those candidates. The surrounding copy calls this “the strongest co-pick context” (`index.html:88`, `index.html:97-99`).

**Impact:** Users can interpret the bars as recommendation strength or product-specific association when they are only measuring overlap with any member of the selected basket. The result is especially uninformative for baskets containing common products.

**Fix:** Choose and name one estimand explicitly. Good options are per-item `P(candidate | basket item)` with a clear denominator, whole-basket support/confidence, or candidate lift against each basket item. Display the numerator and denominator (absolute counts) and avoid “strongest” unless the ranking metric actually supports that claim.

### [Medium] Threshold sensitivity is exposed but not validated

**Evidence:** `analysis.py:72-75` uses fixed `min_support=0.25` and `min_confidence=0.60`; `index.html:72-78` exposes only an interactive support slider. On the 24-row sample, the observed counts are:

| Minimum support | Frequent itemsets | Rules at 60% confidence |
|---:|---:|---:|
| 10% | 27 | 23 |
| 25% | 18 | 15 |
| 30% | 9 | 7 |
| 50% | 7 | 6 |
| 55% | 2 | 0 |

At the selected 25% threshold, the highest-lift rule (`bread + jam -> butter`) is supported by only 6 of 24 baskets, with confidence 1.0 and lift about 1.846. The UI copy says “Higher = fewer, stronger patterns” (`index.html:75`), but a higher support threshold means more prevalent patterns, not necessarily stronger associations by confidence, lift, effect size, or predictive utility.

**Impact:** Small threshold changes create large discontinuities, while the interface provides no stability or selection criterion. A user may mistake prevalence and an in-sample ranking for validated recommendation strength.

**Fix:** Report absolute support counts alongside percentages; require a minimum count for rules; describe the slider as a prevalence filter. Add bootstrap or repeated-resampling stability, and if real timestamps become available, select thresholds on a training period and evaluate rules on a later holdout period. For this synthetic demo, label the output exploratory and show the small denominators prominently.

### [Medium] The browser and Python have two sources of truth

**Evidence:** Python reads `data/transactions.csv` (`analysis.py:9-14`), while the browser embeds a second copy in `app.js:3-31`. `README.md:25` documents that duplication, but `tests/test_analysis.py:6-21` has no parity test. A manual comparison currently passes for all 24 rows and six products, so this is a drift risk rather than a present data mismatch.

**Impact:** Editing the CSV can silently leave the UI analyzing/displaying old data while the Python report uses new data. That breaks reproducibility and makes the source reference in `index.html:60` potentially misleading.

**Fix:** Establish one source of truth: generate the browser data from the CSV as a documented build step, or serve the CSV/JSON through a documented local server. Add an automated test that compares IDs and item lists across the two paths and fails on drift.

### [Low] Transaction parsing accepts malformed data silently

**Evidence:** `analysis.py:12-14` splits the item field without trimming whitespace, rejecting blank tokens, validating required columns, checking duplicate transaction IDs, or checking that each row has at least one product. Duplicate product mentions are collapsed by `frozenset`, which `README.md:35` says is intentional, but no validation distinguishes intentional duplicates from malformed input. `support` can divide by zero on an empty transaction list (`analysis.py:16-17`); only `apriori` guards its own empty-input path (`analysis.py:21-22`).

**Impact:** The current clean fixture is unaffected, but a changed CSV can create phantom items such as `""` or whitespace variants, silently change denominators, or fail with an unhelpful exception.

**Fix:** Validate the CSV at load time: required schema, unique/non-empty IDs, non-empty item strings, normalized tokens, and an explicit duplicate policy. Raise clear `ValueError`s for invalid inputs and make `support`/`association_rules` validate their public arguments consistently.

### [Low] Tests establish only narrow regression coverage

**Evidence:** `tests/test_analysis.py:6-21` checks row count/first row, two support values plus one absent itemset, and broad rule metric ranges. It does not test exact confidence/lift formulas, candidate completeness against a reference implementation, invalid thresholds, empty/malformed transactions, duplicate policy, threshold boundaries, or Python/browser parity. `association_rules` (`analysis.py:37-51`) also has no explicit validation for `min_confidence` or for missing antecedent/consequent supports.

**Impact:** The current tests can pass while an implementation returns incomplete itemsets, uses the wrong denominator, or diverges from the browser calculation.

**Fix:** Add small hand-computable fixtures and an independent brute-force oracle; assert exact support, confidence, and lift values; test invalid inputs and boundary thresholds; and include a data-parity test. Add a CI command using a pinned or explicitly supported Python/pytest range.

## Checks run

- `python3 analysis.py`: passed; printed 24 transactions and 18 frequent itemsets; regenerated the checked-in support plot.
- `node --check app.js`: passed.
- `python3 -m py_compile analysis.py tests/test_analysis.py`: passed.
- Manual invocation of the three test functions: passed 3/3.
- Independent brute-force frequent-itemset comparison: passed at support thresholds 0.10, 0.25, 0.30, 0.50, and 0.70.
- Independent support/confidence/lift invariant checks: passed.
- Python CSV versus browser-embedded CSV parity: passed for all 24 rows.
- Threshold itemset counts were monotone as support increased, but showed the sensitivity cliff documented above.
- `pytest -q` and `python3 -m pytest -q`: not runnable in the review environment because `pytest` is not installed. `requirements.txt:1` specifies an unpinned `pytest>=7.0`; the README claim that pytest passed (`README.md:44-48`) could not be independently reproduced here without installing dependencies.

No source code was modified and no PR or push was created.

## Implementation follow-up

The findings above are retained as the baseline review. The subsequent implementation now derives the product metadata from the browser dataset, separates rule-triggered basket suggestions from the explicitly named context estimand, exposes confidence and absolute support-count controls, and adds itemset-size and rule visibility/sort controls. The test suite now also checks discrete threshold counts, metric invariants, and Python/browser mining parity.
