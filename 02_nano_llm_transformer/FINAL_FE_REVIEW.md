# Final Frontend Review — Project 02 Nano LLM

## Verdict

**Fixes recommended before calling the frontend robust.** The refactor is structurally sound: `App.jsx` is a 26-line composition root, feature components are grouped by domain, shared Radix-backed primitives live under `components/ui`, API access is isolated in `api/client.js`, and async orchestration lives in `hooks/useModelEvidence.js`. The FastAPI and ML layers are also meaningfully modular rather than a renamed monolith. No P0 issue was found.

## Findings

### P1 — The frontend tests do not render or exercise the React application

`tests/test_client_contract.py` only checks that files, dependency strings, route strings, and a few error-message strings exist. It would pass if a component had invalid props, a broken event handler, inaccessible markup, or an `App.jsx` composition that failed at runtime. `client/package.json` has no frontend test script or test dependencies.

**Recommendation:** add Vitest, React Testing Library, `user-event`, and `jest-axe` (or equivalent). At minimum, cover:

- `App` loading, connected, unavailable, and partial-evidence states with a mocked `modelApi`;
- `GenerationForm` validation, pending/disabled behavior, success, and request failure;
- `GenerationPlayground` composition and probability/trace rendering;
- keyboard-visible labels, live status announcements, and a basic axe scan;
- an API adapter test that verifies structured errors and the request payload mapping.

Files: `client/package.json`, `tests/test_client_contract.py`, new `client/src/**/*.test.jsx` or `client/tests/`.

### P2 — Initial evidence loading is all-or-nothing and has no recovery path

`useModelEvidence.js` loads metrics and behavior with one `Promise.all`. A failure in either resource discards both, sets a single global error, and leaves the page in `unavailable` until a full reload. The same `error` channel is reused for generation failures, so load health and action health are not independently representable. This makes the hook less reusable and prevents the UI from showing valid metrics when only behavior metadata is unavailable.

**Recommendation:** model `metrics`, `behavior`, and generation as separate async resources, expose distinct `loadError` and `requestError` values, and return a `retryEvidence()` action. Consider `Promise.allSettled` when partial evidence is useful. Keep request failures local to the playground while the top bar reflects service/evidence health.

Files: `client/src/hooks/useModelEvidence.js`, `client/src/App.jsx`, `client/src/components/layout/AppShell.jsx`, `client/src/components/playground/GenerationForm.jsx`.

### P2 — Generation remains actionable while evidence/API health is unresolved

`GenerationForm` disables its button only while a generation request is pending. It remains enabled while the app is `connecting` or `unavailable`, even though the workflow depends on the same API and model metadata. This creates avoidable failed requests and gives the user no explicit retry/reconnect affordance.

**Recommendation:** pass an `enabled` or `serviceStatus` prop from `App` through `GenerationPlayground`, disable generation until the service is connected, and explain the disabled state. Pair this with the retry action above.

Files: `client/src/App.jsx`, `client/src/components/playground/GenerationPlayground.jsx`, `client/src/components/playground/GenerationForm.jsx`.

### P2 — Global CSS selectors weaken component isolation

The stylesheet split is sensible, but `components.css` styles broad selectors such as `dl`, `dt`, `dd`, `pre`, `.panel label`, `.panel input`, and `.panel textarea`; `layout.css` similarly targets every `footer` and `main`. New components placed inside a panel can inherit form or typography rules unintentionally, so the components are composable in JSX but not fully isolated in presentation.

**Recommendation:** scope styles to component classes (`.manifest-list`, `.generation-response pre`, `.app-footer`, `.app-main`) or use CSS Modules. Keep token and layout files global, while feature styles should be feature-scoped.

Files: `client/src/styles/components.css`, `client/src/styles/layout.css`, corresponding component class names.

### P2 — Dynamic status and visual evidence need stronger accessibility semantics

The connection badge changes after load but is not an `aria-live` region. The chronological split uses decorative `<i>` elements with widths but does not expose the three proportions as a grouped meter/progress description. Smooth scrolling is always enabled without a `prefers-reduced-motion` override. Plain navigation links also rely on default focus treatment rather than a deliberate cross-theme focus style.

**Recommendation:** announce connection changes with a polite live region; give the split visualization a textual summary or explicit meter semantics; add `:focus-visible` styles; and disable smooth scrolling under reduced-motion preferences.

Files: `client/src/components/layout/TopBar.jsx`, `client/src/components/evidence/SplitEvidence.jsx`, `client/src/styles/tokens.css`, `client/src/styles/components.css`.

### P3 — A dead alias and mixed export conventions add unnecessary surface area

`components/evidence/MetricGrid.jsx` re-exports `EvidenceMetrics` as `MetricGrid`, but the application imports `EvidenceMetrics` directly. `useModelEvidence.js` also exports the hook both named and as default while callers use the named export. These are small inconsistencies, but they make discovery and future refactors less predictable.

**Recommendation:** remove the unused alias and default export, or adopt barrel exports consistently for each feature folder.

Files: `client/src/components/evidence/MetricGrid.jsx`, `client/src/hooks/useModelEvidence.js`.

### P3 — Reusable component contracts are untyped

Components such as `Panel`, `SectionHeader`, `MetricCard`, and `GenerationPlayground` have useful boundaries, but their accepted props and payload shapes are implicit. The metrics/replay structures are particularly easy to drift from the API response.

**Recommendation:** add TypeScript interfaces or, at minimum, JSDoc typedefs for API payloads and reusable component props. Generate or share types from the FastAPI schemas if the project grows.

Files: `client/src/api/client.js`, `client/src/hooks/useModelEvidence.js`, `client/src/components/ui/*`, feature component props.

## Positive architecture evidence

- `client/src/App.jsx` composes six feature/layout units and contains no raw API or rendering loops.
- `components/layout`, `components/evidence`, `components/playground`, `components/method`, and `components/ui` are cohesive domain boundaries.
- `GenerationPlayground` composes `GenerationForm` and `BehaviorInspector`; the inspector further composes probability and trace components.
- Radix Themes is declared and actually used for theme, cards, badges, buttons, fields, and callouts.
- `server/main.py` is a thin ASGI entrypoint; `app_factory.py`, routers, schemas, services, and typed ML error handling are separate.
- `ml/model_adapter.py` is now a compatibility facade over focused artifact, validation, inference, path, and error modules.

## Recommended implementation order

1. Add real component/hook/accessibility tests (P1).
2. Separate evidence and generation state, add retry, and gate generation on service readiness (P2).
3. Scope CSS and improve live/focus/reduced-motion semantics (P2).
4. Remove dead exports and add typed contracts (P3).
