# Project 03 Frontend Architecture Review

## Verdict

**Fixes recommended before final sign-off.** The migration is a genuine React refactor rather than a renamed monolith: `App.jsx` composes feature-level sections, shared controls live under `components/common`, explorer rendering is split across `PointExplorer`, `ScatterPlot`, and `PointInspector`, and MUI is installed and configured through a project theme. The server and ML boundaries are also materially improved. The remaining issues are concentrated in interaction correctness, accessibility, and testability.

## What is working well

- The directory layout follows domain boundaries: `layout/`, `dashboard/`, `explorer/`, `scoring/`, and `common/`.
- `App.jsx` is a composition root and does not contain chart math, API request code, or large presentational fragments.
- `useSegmentationData.js` and `api/segmentationApi.js` establish a clear evidence-loading boundary for the main dashboard.
- `SelectField`, `SectionHeading`, and `MetricCard` are small reusable primitives with focused APIs.
- `PointExplorer` delegates geometry rendering and detail presentation to separate components.
- MUI is declared in `package.json`, supplied through `ThemeProvider`, and used for forms, cards, alerts, progress, chips, and buttons.
- The server now has an application factory, routers, schemas, and artifact/profile services; `server/app.py` is a thin compatibility entrypoint.
- The ML package now exposes a stable facade while separating contracts, preprocessing, and scoring.

## Findings

### P1 — Filtering can leave the inspector showing a customer outside the visible segment

Files: `client/src/App.jsx`, `client/src/components/explorer/PointExplorer.jsx`

`selectedId` is initialized from the complete point collection and is not reconciled when `cluster` changes. `PointExplorer` filters the plotted points into `visible`, but resolves the inspector selection from the unfiltered `points` array. A user can select customer C001 in one segment, filter to another segment, and still see C001 in the inspector even though that customer no longer appears in the plot.

Recommendation: derive the selected point from `visible`, and reset or advance selection when the active filter excludes the current point. Encapsulate this behavior in an explorer-state hook or inside `PointExplorer` so the invariant is owned beside the filtering logic. Add a regression test that changes segment and verifies the inspector and selected plot point remain consistent.

### P1 — The interactive SVG does not expose a robust keyboard/screen-reader interaction model

File: `client/src/components/explorer/ScatterPlot.jsx`

All plotted circles receive `tabIndex="0"`, which creates up to 120 consecutive tab stops. The parent SVG is marked `role="img"` while descendants are assigned `role="button"`; image semantics can flatten descendants in accessibility trees, making the intended buttons unreliable across browser/screen-reader combinations. There is also no roving focus, arrow-key navigation, selected state, or non-visual equivalent.

Recommendation: use one keyboard entry point with roving `tabIndex`, arrow-key navigation, and `aria-selected`, or pair the visualization with a synchronized HTML list/table of points. Avoid an `img` role on a container that owns interactive descendants. Keep Enter/Space activation and expose the current point, segment, and diagnostic values in the accessible alternative.

### P1 — The scoring feature bypasses the documented API/hook boundary

Files: `client/src/components/scoring/ScoringWorkbench.jsx`, `client/src/hooks/useSegmentationData.js`, `client/src/api/segmentationApi.js`, `README.md`

`ScoringWorkbench` imports `segmentationApi` directly and owns request state, errors, and response formatting. This makes a feature-level presentation component difficult to compose or test with alternate data sources, and contradicts the README statement that API orchestration is kept out of presentation components.

Recommendation: move scoring request state into `hooks/useScoreObservation.js` (or inject an `onScore` function and state from the composition root). Keep `ScoringWorkbench` responsible for composing `ScoreForm` and a presentational result component. This also creates a natural unit-test boundary for loading, success, validation failure, and retry behavior.

### P2 — The form does not mirror the server's validation contract

Files: `client/src/components/scoring/ScoreForm.jsx`, `server/schemas.py`

All fields use only `step="any"` and `required`. The API enforces income >= 15, spend score 1–99, purchase frequency >= 0.2, and average order value >= 5. Invalid values are therefore accepted by the browser and fail only after a network round trip.

Recommendation: define shared frontend field metadata with `min`, `max`, labels, helper text, and appropriate step values. Pass those constraints to MUI's numeric inputs and surface field-level errors. Keep server validation authoritative, but align the client contract to prevent avoidable 422 responses.

### P2 — Evidence refreshes have no cancellation or stale-response guard

File: `client/src/hooks/useSegmentationData.js`

The hook starts parallel requests without an `AbortController` or request sequence token. React Strict Mode invokes effects twice in development, and a manual refresh can overlap an in-flight load. An older response can overwrite newer state or set state after unmount.

Recommendation: add request cancellation or a monotonically increasing request id, pass the signal through `segmentationApi`, and ignore superseded completions. Test overlapping refreshes and unmount behavior.

### P2 — Frontend tests validate file presence, not component behavior

Files: `tests/test_server_contract.py`, `client/package.json`

The current contract test counts JSX files, but the client has no component, hook, or accessibility test suite and no `test`/`lint` script. File count cannot establish that components are wired, that filtering preserves selection, that errors render, or that the scoring form submits the expected payload.

Recommendation: add Vitest, React Testing Library, and `@testing-library/jest-dom`; cover the composition root, evidence loading/error states, segment-filter selection behavior, score submission, and keyboard point selection. Add ESLint with React Hooks rules and scripts for `test` and `lint`.

### P3 — Global styling is compressed into a single unformatted stylesheet

File: `client/src/styles.css`

The stylesheet is a single minified line with global class names. It preserves the visual design, but it is difficult to review, diff, or safely evolve alongside the new component boundaries.

Recommendation: format the stylesheet and split it by responsibility (`tokens/base`, `layout`, `dashboard`, `explorer`, `scoring`) or colocate component styles. Prefer theme tokens/MUI `sx` for library-level variants and reserve global CSS for shared layout and SVG classes.

## Suggested acceptance criteria

1. Changing segment never leaves an out-of-filter customer in the inspector.
2. The plot has a documented, tested keyboard model without 120 tab stops and a non-visual equivalent is available.
3. No component under `components/` imports `segmentationApi` directly.
4. Scoring inputs expose the same bounds as `server/schemas.py` and render validation errors clearly.
5. Evidence requests are cancellable or sequenced so stale responses cannot win.
6. `npm test`, `npm run lint`, and `npm run build` all pass with behavioral coverage for the explorer and scoring workflow.

## Overall assessment

The architecture is a strong foundation and the component placement is sensible. Addressing the three P1 findings will make the refactor genuinely robust rather than only structurally decomposed; the P2/P3 items will make it easier to maintain and defend in a frontend code review.
