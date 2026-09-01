# Final Frontend Review — Project 04

## Verdict

**Structurally sound, with targeted fixes recommended.** The React refactor is genuine rather than cosmetic: `App.jsx` is a thin composition root, domain sections are separated from reusable UI primitives, `useBasketSignals` owns request/state orchestration, and `services/api.js` owns transport details. Radix Select and Slider are declared runtime dependencies and are actually used. The server and ML layers are also meaningfully modularized behind thin compatibility facades.

No P0 issues were found. Address the P1 request-amplification issue before calling the frontend robust under repeated interaction; the P2 items would materially improve recoverability and test confidence.

## Findings

### P1 — Slider interaction amplifies into repeated four-request dashboard reloads

Files: `client/src/components/ui/RangeControl.jsx`, `client/src/hooks/useBasketSignals.js`, `client/src/services/api.js`

`RangeControl` commits every `onValueChange` event directly into `filters`. Each intermediate slider value reruns the dashboard effect, and `getDashboard` issues four requests (`summary`, `itemsets`, `rules`, and `transactions`). Although `AbortController` prevents stale client state, already-dispatched server work is still created, and the invariant transaction list is fetched again for every support/confidence/count adjustment.

Recommendation: separate draft control values from applied query values, debounce support/confidence/count changes, or commit on Radix `onValueCommit`. Fetch transactions once in a separate effect/cache. Keep itemset-size changes scoped to the itemset request rather than reloading summary, rules, and transactions.

### P2 — Dashboard and context failures share one sticky error channel

File: `client/src/hooks/useBasketSignals.js`

Both effects write to the same `error`, but only the dashboard effect clears it. A failed context request can leave the global status in an error state even after a later context request succeeds. Conversely, a dashboard refresh can clear a still-relevant context failure. The UI cannot identify which surface failed.

Recommendation: maintain separate `dashboardError` and `contextError` state, clear each at the start/success of its own request, and derive section-level status from the corresponding error. This also enables the basket explorer to fail independently without making the complete dashboard look unavailable.

### P2 — Errors are only exposed in the top-bar status and have no recovery action

Files: `client/src/components/layout/AppShell.jsx`, `client/src/App.jsx`, `client/src/hooks/useBasketSignals.js`

The status badge is the only error presentation. Failed sections otherwise render empty or stale content, and the user has no retry action. A long API error message can also become an awkward top-bar label.

Recommendation: return explicit retry callbacks from the hook and add a reusable inline `AsyncState`/`ErrorPanel` component near the affected dashboard or context section. Keep the top-bar badge concise and put diagnostic detail in the section alert using `role="alert"`.

### P2 — Frontend tests verify file contents, not React behavior

File: `tests/test_e2e_contract.py`

The composition test counts JSX files and searches source strings. It does not render the component tree or verify that Radix controls update filters, loading/error states render correctly, aborted responses cannot overwrite current state, or server payloads appear in cards and lists.

Recommendation: add Vitest plus React Testing Library/MSW (or a lightweight fetch mock) and cover at least: initial loading/success, API failure and retry, threshold commit/debounce, sort/size selection, context selection, and stale-request cancellation. Keep the existing static contract as a low-cost architecture guard, not the primary frontend test.

### P3 — Global styling is compact but tightly coupled and remotely hosted fonts weaken offline behavior

Files: `client/src/styles.css`, `client/src/radix.css`

Most presentation rules remain in one minified global stylesheet, making component ownership and future deletion harder to reason about. It also imports Google Fonts at runtime, creating a network dependency for an otherwise local evidence workbench.

Recommendation: split design tokens/base styles from layout and domain-section styles (or use CSS modules colocated with components), and use a system/local font stack or checked-in font assets. Keep `radix.css` as the focused primitive adapter.

## What is working well

- `App.jsx` is a clean composition root and does not contain presentation implementation.
- Component placement is understandable: `layout/`, `sections/`, `data/`, and `ui/` distinguish page structure from reusable primitives.
- `RangeControl`, `SelectField`, `MetricCard`, `SectionHeader`, and `BarList` are useful reusable components with narrow prop surfaces.
- Radix primitives provide keyboard/focus foundations; the custom focus-visible styling is explicit.
- `AbortController` guards against stale client updates, and API query construction is centralized.
- Analytical denominators and non-causal framing remain visible in the UI.
- The server uses a thin ASGI entrypoint, application factory, router, schemas, and service layer. The ML package separates repository access, mining, context, and serialization while retaining `ml.pipeline` as a stable facade.

## Suggested implementation order

1. Fix request amplification and invariant transaction refetching.
2. Separate dashboard/context error state and add section-level retry UI.
3. Add behavioral component tests.
4. Improve stylesheet ownership and remove the remote font dependency.
