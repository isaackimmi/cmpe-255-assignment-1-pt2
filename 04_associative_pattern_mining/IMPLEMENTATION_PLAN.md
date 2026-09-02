# Implementation Plan — Associative Pattern Mining

## Retrospective scope

This plan documents the offline market-basket reproduction. It uses a compact checked-in transaction fixture instead of silently downloading an unspecified Kaggle dataset, while preserving the Apriori/rule-metric workflow requested by the project.

## Objectives

1. Discover frequent product combinations from transaction baskets.
2. Derive directional association rules and explain their denominators.
3. Distinguish prevalence, conditional frequency, and excess association.
4. Let users change support/confidence/count thresholds, inspect itemsets, sort rules, and explore baskets in an interactive UI.
5. Keep exploratory in-sample findings separate from production recommendations.

## Data and preparation

1. Load one basket per row using the `transaction_id,items` schema.
2. Validate unique non-empty IDs, non-empty trimmed product tokens, and at least one basket.
3. Collapse duplicate product mentions within each basket into sets.
4. Convert percentage support to a whole-basket minimum count with `ceil(min_support × n)` and optionally apply an absolute count floor.
5. Preserve transaction counts and denominators in outputs and API responses.

## Modeling and evaluation

1. Implement Apriori using the anti-monotonic pruning property: an infrequent itemset cannot have a frequent superset.
2. Mine frequent itemsets at configurable support and itemset-size thresholds.
3. Derive directional rules from frequent itemsets.
4. Report support, confidence, and lift for each rule.
5. Explain that confidence is `P(consequent | antecedent)`, while lift compares that value with the consequent base rate; lift above 1 indicates positive association relative to independence.
6. Rank rules with lift/confidence and retain absolute counts; identify holdout-period validation and resampling stability as production follow-ups.

## Application sequence

1. Keep the analytical truth in the ML facade and focused repository, Apriori, serialization, and context modules.
2. Split FastAPI configuration, app factory, routes, schemas, and service layer.
3. Build React/Vite components for layout, section headers, support chart, itemset/rule cards, sliders, select controls, basket explorer, and context panels using Radix UI primitives.
4. Use `useBasketSignals` and a dedicated API service for cancellable, scoped requests.
5. Debounce threshold previews and cache independent transaction/context data so unrelated failures do not blank the dashboard.
6. Keep the dependency-free root HTML artifact viewer for offline comparison.

## Validation criteria

- Python analytical, parity, and API-contract tests pass.
- Browser data and API results agree for the same thresholds.
- Thresholds translate into correct basket counts and no denominator is hidden.
- Itemset-size and sorting controls reload only the evidence they affect.
- Client tests verify debouncing, request scoping, independent recovery, accessibility, and the production build.

## Limitations

The fixture contains 24 synthetic/local transactions, so its rules are teaching evidence, not observed customer behavior. A production system should validate rules on a later time period, assess stability, handle changing catalogs, and connect recommendations to measured business outcomes.
