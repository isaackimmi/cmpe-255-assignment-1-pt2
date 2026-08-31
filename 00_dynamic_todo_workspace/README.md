# Project 00 — Dynamic Todo Workspace

A lightweight runnable workspace for planning data-science-agent work. It combines a project queue, dataset context, task filtering, progress summaries, and a small agent activity feed in one local-first web app.

## Run locally

No package installation is required. From this directory, start any static server:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

The app also works by opening `index.html` directly, although some browsers restrict local storage for `file://` pages. Tasks are saved in the browser's local storage when available.

## Features

- Add, complete, and delete tasks.
- Filter the queue by status, priority, and search text.
- Keep a selected workspace brief visible while tasks are edited.
- View dataset metadata, workflow stages, progress, and agent activity.
- Seeded example tasks demonstrate a typical CRISP-DM/data-science-agent loop.
- Responsive layout for desktop and narrow screens.

## Tests

The pure task/state helpers are covered with Node's built-in test runner:

```bash
node --test tests/state.test.js
```

## Documented deviations

The original Project 00 prompt referenced by the assignment was not available in this checkout. Based on the assignment brief, this implementation intentionally uses a dependency-free vanilla HTML/CSS/JavaScript stack rather than a full backend or framework. It does not provide authentication, multi-user sync, a database, drag-and-drop ordering, or a deployed URL. Those are reasonable next steps if the reference prompt requires production persistence or collaboration.

## Files

- `index.html` — application shell and accessible controls.
- `styles.css` — visual system and responsive layout.
- `src/state.js` — pure state helpers used by the app and tests.
- `src/app.js` — DOM rendering and interaction logic.
- `tests/state.test.js` — executable state/model tests.
- `screenshots/` — optional visual evidence generated during local QA.
## Integration verification

- **Prompt alignment:** Public Project 00 asks for a modern dynamic todo application; this covers local task queue, filtering, persistence, responsive UI, and seeded workspace context.
- **Results/artifacts:** `index.html`, `styles.css`, and `src/` are the visual artifact; Node tests passed 4/4.
- **Issue/resolution:** Dependency-free local-first design intentionally omits authentication, multi-user sync, and deployment.
