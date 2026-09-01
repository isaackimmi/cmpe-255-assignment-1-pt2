# Final Frontend Review — Project 05

## Verdict

**Fixes required before frontend sign-off.** The migration is real rather than cosmetic: Vite mounts a React 18 application, Material UI is declared and used, `App.jsx` composes domain components, API access is isolated in `api/labApi.js`, state orchestration lives in `hooks/useLabData.js`, and the server/ML layers have been split into routers, services, schemas, artifact loading, contracts, and a compatibility facade. The remaining issues are primarily async correctness, control-to-view integrity, accessibility, and test coverage.

## Findings

### P1 — Overlapping requests can commit stale module or filter results

`client/src/hooks/useLabData.js:39-68` uses one `loading` flag and allows module and filter requests to overlap without cancellation or request identity. A slow response from an earlier module selection can overwrite `moduleData` after the user selects a later module. Two rapid filter changes can similarly render an older `rowsResult`, and either request can set `loading` to false while another request is still pending.

**Recommendation:** make `labApi.request` accept an `AbortSignal`, cancel superseded module/filter requests in effect cleanup, or guard commits with monotonically increasing request IDs. Track summary, module, and row pending/error state separately so one request cannot clear another request's loading state. Add a regression test that resolves two module/filter promises out of order and asserts that only the latest selection is rendered.

### P1 — The global filters have no visible analytical effect in most modules

`client/src/App.jsx:20-24` renders `ExplorerFilters` for every active module, but `client/src/components/modules/ModulePanel.jsx:7-13` passes filtered rows only to `ClusteringPanel`. On Overview, Cleaning, Classification, and Regression, changing Plan/Renewal/Cluster performs an API request but does not alter the displayed evidence or expose the filtered row count. This makes a functioning control appear broken and can imply that headline/holdout metrics were recomputed for the selected subgroup when they were not.

**Recommendation:** either scope the filters to a clearly labeled row explorer/Clustering view, or add a reusable `FilteredRowsPanel` to every applicable module while explicitly stating that model metrics remain fixed artifact-level metrics. Include the current filter state and result count near the affected view; do not imply subgroup re-scoring unless the server actually performs it.

### P2 — Frontend behavior is not covered by frontend tests or linting

`client/package.json:6-17` exposes only dev/build/preview scripts. The Python contract test checks filenames and source strings, but it cannot prove that navigation composes the correct panel, filters emit the expected query, retry works, or stale requests are rejected.

**Recommendation:** add Vitest + React Testing Library tests for module navigation, loading/error/retry states, filter query composition, latest-request-wins behavior, and representative panel rendering. Add ESLint with the React Hooks plugin instead of suppressing `react-hooks/exhaustive-deps` in `useLabData.js:37`.

### P2 — Render components trust deep artifact shapes and can crash the whole app

Components dereference nested values without a component error boundary or a client-side response contract. Examples include `metrics.data_quality.clean_rows` in `MetricGrid.jsx`, `classification.confusion_matrix[0][0]` in `ClassificationPanel.jsx`, and `summary.summary.regression_predictions` in `ModulePanel.jsx`. The server validates required top-level sections, but `ml/artifacts.py` does not validate these nested shapes before returning them.

**Recommendation:** strengthen the artifact schema at the server/ML boundary (Pydantic models, dataclasses with validation, or explicit validators) and add an `EvidenceErrorBoundary` around module content. Keep UI components typed with TypeScript or documented PropTypes/JSDoc contracts so their required data is discoverable.

### P2 — Data visualizations need semantic alternatives

The confusion matrix in `ClassificationPanel.jsx` and prediction samples in `RegressionPanel.jsx`/`ClusteringPanel.jsx` are visual `div` grids rather than semantic tables. The regression bar chart has an `aria-label` but no `role`, values, legend, or textual relationship for assistive technology. Wrapping the entire changing module in `aria-live="polite"` (`EvidencePanels.jsx`) can also announce a large amount of content on every navigation.

**Recommendation:** use `<table>` with captions/headers for matrix and row evidence, and use `<figure>`/`<figcaption>` or `role="img"` with an explicit textual comparison for charts. Restrict live announcements to a concise status/result-count region and move focus to the new module heading after navigation.

### P2 — Styling remains a monolithic global surface

`client/src/style.css` contains the whole application stylesheet as one minified line with broad selectors such as `main`, `nav`, `footer`, `.table`, and `.panel`; `mui.css` then overrides Material UI through generated class conventions. This weakens component ownership and makes style collisions more likely as the app grows.

**Recommendation:** split tokens, layout, and feature styles into readable modules co-located with components, or move reusable visual rules into the MUI theme/`styled` API. Keep global CSS limited to reset/tokens. Prefer feature-scoped class names or CSS Modules over generic global names.

### P3 — Two component boundaries add indirection without encapsulating behavior

`EvidencePanels.jsx` only forwards props to `ModulePanel`, while `ModulePanel.jsx` uses an `if` chain and a broad prop bag. This works, but adding a module requires edits in multiple files and makes dependencies less explicit.

**Recommendation:** either merge the pass-through layer into an `EvidenceBoundary` that owns loading/error/live-region behavior, or use a module registry such as `{ cleaning: CleaningPanel, ... }` with per-panel prop selectors. Keep each panel's data contract narrow rather than passing `metrics`, `moduleData`, `summary`, and `rowsResult` through a central catch-all.

### P3 — The ML service mutates `sys.path`

`ml/service.py:3-13` inserts `src/` into `sys.path` to import `skills_lab`. The API/ML split is otherwise sound, but this import side effect makes packaging and test isolation more brittle.

**Recommendation:** package the canonical experiment code as an importable module (for example `src/project05/`) and import it normally. Keep `ml/pipeline.py` as the compatibility facade, but remove runtime path mutation.

## Strengths confirmed

- `App.jsx` is now a small composition root rather than the entire interface.
- Components are grouped by responsibility: `layout`, `navigation`, `metrics`, `filters`, `evidence`, `modules`, and `common`.
- MUI provides accessible Select, Button, Alert, Progress, and Chip primitives while the project retains its visual identity.
- `labApi.js` centralizes response/error handling and supports proxy or `VITE_API_URL` deployment.
- `MetricCard`, `Panel`, `PanelHeader`, `ModuleNav`, and `ExplorerFilters` are reusable, data-driven boundaries.
- FastAPI is split into composition, routers, schemas, and evidence services; ML artifact loading/contracts are no longer buried in one file.

## Recommended implementation order

1. Fix request cancellation/latest-response ownership and add async regression tests.
2. Clarify or redesign filter scope so every visible control has an honest visible effect.
3. Add nested response validation plus an evidence error boundary.
4. Add semantic tables/chart alternatives and focused live-region behavior.
5. Add Vitest/RTL/ESLint, then split the global stylesheet and remove `sys.path` mutation.
