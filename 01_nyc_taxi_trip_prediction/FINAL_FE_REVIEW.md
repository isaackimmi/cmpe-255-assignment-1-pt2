# Project 01 Frontend Architecture Review

## Verdict

**Fixes recommended.** The client is now a genuine React/Vite application rather than a renamed monolith. `App.jsx` composes domain-level sections, feature components are grouped by concern, API access lives behind `services/api.js`, server state is handled in hooks, and MUI is both declared and actually used. The server and ML layers also have sensible compatibility facades over focused modules. The primary remaining risks are weak behavioral test coverage, async request lifecycle handling, incomplete data-visualization semantics, and a global CSS layer that still couples otherwise reusable components.

## Findings

### P1 — The React component behavior is not tested

`tests/test_e2e_static_contract.py` verifies dependency names, directory existence, endpoint strings, and component names in `App.jsx`, but it never renders a component or exercises an interaction. A broken MUI prop, missing callback, stale request, inaccessible form, or failed retry could pass the current suite. This is particularly risky for `SliceExplorer`, `TripEstimator`, and the initial evidence-loading path, which contain the important UI behavior introduced by this refactor.

**Recommendation:** add Vitest + React Testing Library and a fetch mock layer (MSW or focused `vi.stubGlobal("fetch", ...)` helpers). Cover at minimum:

- loading → success and loading → retryable error in `App`/`useExperimentData`;
- slice and population changes producing the expected query parameters;
- aborted slice requests not replacing newer results;
- estimator validation/submission, disabled state, error state, and result rendering;
- keyboard-accessible navigation and form labels.

Relevant files: `client/package.json`, `client/src/App.jsx`, `client/src/hooks/useExperimentData.js`, `client/src/hooks/usePredictionSlice.js`, `client/src/components/estimator/TripEstimator.jsx`, `tests/test_e2e_static_contract.py`.

### P2 — Initial evidence requests are not abortable or protected from stale completion

`useExperimentData` starts two requests in `Promise.all` without an `AbortController` or mounted/request-generation guard. React Strict Mode intentionally re-runs effects during development, so the app can issue duplicate initial requests. A retry can also race an older request, allowing the older completion to overwrite newer state. `usePredictionSlice` handles cancellation correctly and should be the model for this hook.

**Recommendation:** let `taxiApi.experiment` and `taxiApi.featureImportance` accept a signal, abort the previous load when reloading/unmounting, and ignore abort errors. Alternatively, use a query library consistently if the other projects adopt one.

Relevant files: `client/src/hooks/useExperimentData.js`, `client/src/services/api.js`, `client/src/main.jsx`.

### P2 — Prediction evidence has incomplete accessible semantics

`PredictionTable` uses `role="table"` and `role="row"`, but its children have no `columnheader` or `cell` roles. `ResidualChart` exposes one container label while every bar is an unsemantic `<i>` whose detail is only available through the mouse-oriented `title` attribute. The feature-importance bars similarly put an `aria-label` on a decorative `<i>` without a defined role. Screen-reader and keyboard users cannot inspect the same row/bar evidence as pointer users.

**Recommendation:** prefer a semantic `<table>` for prediction rows. Render residuals as an SVG/chart abstraction with a textual summary or keyboard-focusable points and accessible names; mark purely decorative bars `aria-hidden` when equivalent text is present. Add an accessible list/table representation for feature importance.

Relevant files: `client/src/components/explorer/PredictionTable.jsx`, `client/src/components/explorer/ResidualChart.jsx`, `client/src/components/evidence/FeatureImportance.jsx`.

### P2 — Global styling still couples the new component tree

The component placement is good, but nearly all styling remains in a single minified/global `styles.css`. Broad selectors such as `.metric strong`, `.panel`, `.button`, `small`, and `.dark .MuiCircularProgress-root` create hidden contracts between unrelated components. Direct overrides of generated MUI class names also make upgrades and reuse brittle. The file's one-line/minified layout makes review and future maintenance unnecessarily difficult.

**Recommendation:** move stable tokens into `theme.js`, use MUI component variants/default props for library-level styling, and use CSS Modules or feature-scoped style files beside `components/evidence`, `components/explorer`, and `components/estimator`. Keep only reset/layout primitives global. Format the CSS as normal source rather than checked-in minified text.

Relevant files: `client/src/styles.css`, `client/src/theme.js`, `client/src/components/common/MetricCard.jsx`, `client/src/components/layout/AppHeader.jsx`.

### P2 — The compact table can be clipped on small screens

The mobile media query collapses major grids but leaves `.tr` as a fixed four-column grid while `main` uses `overflow:hidden`. Long timestamps and numeric cells can therefore be clipped rather than scrollable on a narrow viewport.

**Recommendation:** wrap the table in an explicitly labeled horizontal-scroll container, or switch rows to stacked label/value cards below the mobile breakpoint. Avoid hiding overflow at the `main` boundary when analytical evidence may be wider than the viewport.

Relevant files: `client/src/components/explorer/PredictionTable.jsx`, `client/src/styles.css`.

### P3 — Shared primitives contain project-specific policy

`ErrorState` is located in `components/common`, but it hardcodes “Start FastAPI on port 8001.” That makes the primitive less reusable and causes every API error—including a 400 slice error—to display infrastructure guidance whether or not the server is unavailable.

**Recommendation:** let `ErrorState` render a supplied message/action, and keep port/startup guidance in the page-level evidence or explorer feature that knows the failure context. Use `ApiError.status` to distinguish validation, unavailable-service, and unexpected failures.

Relevant files: `client/src/components/common/AsyncState.jsx`, `client/src/services/api.js`, `client/src/App.jsx`, `client/src/components/explorer/SliceExplorer.jsx`.

### P3 — A compatibility component is dead implementation surface

`components/explorer/PredictionExplorer.jsx` only re-exports `SliceExplorer` and is not used by the current import tree. Unless a documented external import depends on it, it adds a second name for the same feature and weakens naming clarity.

**Recommendation:** remove the compatibility alias or document the compatibility requirement and schedule its removal.

Relevant file: `client/src/components/explorer/PredictionExplorer.jsx`.

### P3 — Component contracts are implicit

The domain components are sensibly sized and placed, but their props are undocumented JavaScript contracts. Components such as `SliceResults`, `EvidenceSection`, and `MetricCard` assume nested response shapes and numeric values. Invalid or partial data will render `NaN`, throw on array operations, or fail deep in a child.

**Recommendation:** add TypeScript types or, at minimum, JSDoc typedefs/PropTypes plus API response normalization at the service boundary. Keep backend response models explicit so the client contract is generated or mirrored deliberately.

Relevant files: `client/src/components/common/MetricCard.jsx`, `client/src/components/evidence/EvidenceSection.jsx`, `client/src/components/explorer/SliceResults.jsx`, `client/src/services/api.js`, `server/schemas.py`.

## Architecture strengths

- `App.jsx` is a small composition root and does not contain feature implementation details.
- `components/layout`, `components/common`, `components/evidence`, `components/explorer`, `components/estimator`, and `components/sections` are clear domain boundaries.
- `SliceExplorer` owns feature-local selection state while `usePredictionSlice` owns server-state lifecycle; this is an appropriate boundary.
- `TripEstimator` composes form and result components instead of mixing both presentations into one file.
- `services/api.js` centralizes base URL selection, response parsing, and typed error metadata.
- MUI is used for controls, cards, feedback, and theming rather than merely listed as a dependency.
- `server/main.py` is now a thin ASGI/backward-compatibility facade over an app factory, router, schemas, and service.
- `ml/model.py` is now a compatibility facade over artifact, slicing, scoring, geographic, numeric, and estimator modules.

## Suggested implementation order

1. Add behavioral React tests around loading, slice requests, cancellation, and estimation.
2. Add cancellation/request-generation protection to `useExperimentData`.
3. Fix semantic table/chart accessibility and mobile overflow.
4. Split global styling into theme tokens and feature-scoped styles.
5. Clean up the project-specific `ErrorState`, dead compatibility alias, and implicit data contracts.
