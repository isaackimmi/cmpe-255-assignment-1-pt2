# Project 04 — Market Basket Pattern Mining

This project reproduces the Project 04 brief from the original catalog: “associative pattern mining using [a] popular Kaggle data set,” following CRISP-DM and providing data-science/audit detail. The assignment version deliberately uses a compact, checked-in transaction dataset so it runs offline and deterministically.

## Reproduce

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python analysis.py
pytest -q
```

The script prints frequent itemsets and rules, then writes `outputs/support_plot.svg`.

## Method

Transactions are one row per basket with semicolon-separated products. Apriori mines frequent itemsets at minimum support 0.25, using the anti-monotonic property to prune candidates. Rules are retained at minimum confidence 0.60 and reported with support, confidence, and lift. Lift above 1 indicates positive association relative to independence. The chart ranks frequent itemsets by support.

## CRISP-DM notes

**Business understanding:** identify product combinations useful for shelf placement and recommendation candidates. **Data understanding:** inspect basket counts and item co-occurrence. **Data preparation:** parse each basket into a set, intentionally removing duplicate product mentions within a basket. **Modeling:** use transparent Apriori and derive rules. **Evaluation:** use support, confidence, and lift together; confidence alone can over-rank popular products. **Deployment:** export the ranked rules/plot as decision support, with thresholds re-tuned on real production data.

## Deviations and defensible improvement

The original prompt names a popular Kaggle dataset but does not prescribe a URL or schema. To keep the submission reproducible without credentials or network access, this reproduction uses a small synthetic grocery dataset with realistic recurring bundles rather than silently downloading a third-party dataset. It is not a claim about real customer behavior. A defensible improvement is lift-based rule ranking: the top rules are sorted by lift (then confidence), which discounts associations explained only by a very common consequent. For production, the next improvement would be holdout-period validation and business constraints such as minimum absolute basket count.

## Files

`data/transactions.csv` is the immutable input; `analysis.py` contains the standard-library mining implementation and plotting entry point; `tests/test_analysis.py` provides regression tests; `outputs/` contains generated visuals. The SVG chart intentionally requires no plotting library.
## Integration verification

- **Prompt alignment:** Public Project 04 asks for associative mining with CRISP-DM/reporting; Apriori, rule metrics, ranking, and SVG are implemented.
- **Results/artifacts:** 24 transactions produced 18 frequent itemsets; support plot regenerated; pytest passed 3/3 using an existing environment.
- **Issue/resolution:** System Python lacked pytest; existing environment supplied it without installation.
