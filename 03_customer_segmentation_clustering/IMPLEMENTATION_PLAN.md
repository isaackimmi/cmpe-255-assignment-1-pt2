# Implementation Plan — Customer Segmentation Clustering

## Retrospective scope

This plan documents the unsupervised customer-segmentation experiment and its API-backed interactive explorer. It uses deterministic synthetic customer data so the complete pipeline can run offline and the cluster geometry can be inspected.

## Objectives

1. Discover behavioral/value customer groups without pretending that labels or business personas are known.
2. Compare candidate cluster counts and preprocessing choices.
3. Evaluate separation, stability, and point-level assignment ambiguity.
4. Provide a browser dashboard with a PCA visualization, semantic evidence table, selected-point inspector, and new-customer scorer.
5. Keep business interpretation separate from geometric model evidence.

## Data and preparation

1. Generate or load four numeric behavioral/value features under a documented schema and bounds.
2. Validate finite values, feature ranges, and artifact integrity.
3. Optionally apply `log1p` to monetary features as a measured preprocessing comparison.
4. Fit `StandardScaler` separately within each training/repeated-validation partition so feature scale does not dominate Euclidean distance.
5. Export browser-ready point data and a manifest containing configuration, hashes, and metric agreement.

## Modeling and evaluation

1. Fit K-Means for predeclared candidate `k` values 2–7 with multiple initializations.
2. Select using repeated held-out silhouette means and uncertainty rather than relying on one fit.
3. Measure partition stability with repeated Adjusted Rand Index.
4. Report descriptive full-sample inertia/silhouette separately from validation evidence.
5. Compute each point’s nearest and second-nearest centroid distances, margin, and confidence proxy.
6. Use PCA only for visualization; do not describe its coordinates as predictions or probabilities.

## Application sequence

1. Keep the analytical experiment and artifact validator independent from HTTP.
2. Split the server into app factory, routers, schemas, artifact services, and profile derivation services, retaining the stable ASGI entrypoint.
3. Keep `ml/pipeline.py` as a compatibility facade over focused preprocessing, scoring, contract, and artifact modules.
4. Build React/MUI components for layout, filters, metric cards, PCA/SVG explorer, semantic table, point inspector, profile panels, and estimator form.
5. Reconcile selected points when filters change and use roving keyboard focus so the chart has an accessible table-equivalent path.

## Validation criteria

- Repeated validation and stability outputs are reproducible from a fixed seed.
- Scaling/log-transform comparisons are measured, not asserted.
- Artifact schemas, hashes, selected labels, and metric values agree across Python and API layers.
- Filtered point selection cannot show a customer outside the active filter.
- Client tests, lint, build, and API/experiment suites pass.

## Limitations and responsible use

Synthetic clusters may overstate separability; K-Means assumes roughly spherical Euclidean groups, and internal metrics do not establish business value or fairness. Before deployment, validate on longitudinal real transactions, compare alternative algorithms, add outcomes, monitor drift, and never use segments to deny service or infer sensitive traits.
