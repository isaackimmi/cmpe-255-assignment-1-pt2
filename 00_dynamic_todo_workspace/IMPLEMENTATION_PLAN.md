# Implementation Plan — Dynamic Todo Workspace

## Retrospective scope

This plan documents the implementation that was produced for Project 00: a local-first workspace for planning data-science-agent work. It is intentionally a planning and governance application, not a forecasting or modeling application.

## Objectives

1. Represent a DS project as an explicit CRISP-DM workflow.
2. Let a user add, complete, delete, search, and filter tasks.
3. Show project context, dataset-readiness checks, workflow-stage evidence, and activity history in one dashboard.
4. Keep planned work separate from measured results so the UI cannot imply that an unrun model produced metrics.
5. Provide both a dependency-free static fallback and a polished React/FastAPI demo.

## Implementation sequence

1. Define the planning domain: workspace brief, seeded tasks, priorities, statuses, CRISP-DM stages, readiness checks, and activity events.
2. Build pure state helpers for task normalization, filtering, ID migration, and local-storage safety. Cover them with Node tests.
3. Build the E2E backend as a thin FastAPI composition root over typed schemas, a thread-safe in-memory repository, and task/workspace services.
4. Expose typed workspace, readiness, task CRUD, and simulated agent-check endpoints.
5. Build the React client with a Vite entrypoint, Radix UI interaction primitives, a responsive shell, reusable metric cards, task board/row/form components, workflow navigation, and evidence panels.
6. Add cancellable workspace loading, normalized API errors, single-flight mutation handling, loading/error/empty states, and accessible keyboard behavior.
7. Preserve the root `index.html` app as a dependency-free static fallback with its own state and contract tests.
8. Validate the API contract, client behavior, production build, and honest-data boundary; document the limitations and manual run paths.

## Validation criteria

- Task mutations update the server-backed workspace and refresh visible state.
- Filters and search affect only the task view, not the project’s claimed evidence.
- Invalid task payloads and unknown IDs return clear validation/404 responses.
- Loading and API failure states are visible and recoverable.
- No screen displays fabricated forecast, confidence, time-saved, or model metrics.
- React tests, Node fallback tests, API contract tests, and `npm run build` pass.

## Known boundaries

The implementation uses an in-memory repository for the E2E demo; it does not provide authentication, durable database persistence, multi-user synchronization, or a real retail dataset/model. The agent-check action records a simulation only.
