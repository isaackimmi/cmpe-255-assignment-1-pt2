# Reproduction Log

Verification date: 2026-08-30/31 (local time). Commands were run from each project directory. Existing local environments were reused; no heavyweight dependency installation or external dataset download was performed.

| Project | Run/test result | Evidence and issue resolution |
|---|---|---|
| 00 | PASS | Node tests 4/4; static HTML/CSS/JS is the visual artifact. |
| 01 | PASS | Synthetic fallback + validation; 6,000 rows, model MAE 82.045s/RMSE 102.688s/R² 0.6874. |
| 02 | PASS | Standard-library run + unittest 3/3; held-out loss 3.0991, perplexity 22.1789. |
| 03 | PASS | Existing .venv; run + pytest 3/3; k=3, silhouette 0.6696. |
| 04 | PASS | Existing Project 03 .venv supplied pytest; 3/3; 24 baskets, 18 frequent itemsets. |
| 05 | PASS | Standard-library run + unittest 4/4; 23 cleaned rows and deterministic artifacts. |
| 06 | PASS | Existing Project 03 .venv avoided missing packages and Python 3.14 Matplotlib abort; pytest 3/3. |
| 07 | PASS | Existing Project 13 .venv, --no-autogluon; pytest 2/2; sklearn fallback recorded. |
| 08 | PASS | Plot generation + pytest 6/6. Fixed redirected-temp manifest path bug. |
| 09 | PASS | Example + unittest 6/6; deterministic topological execution. |
| 10 | PASS | Existing .venv; run + pytest 3/3; Iris accuracy 0.9333. |
| 11 | PASS (conditional result) | Audit + unittest 3/3; 4 intentional governance failures, release recommendation CONDITIONAL. |
| 12 | PASS | Existing Project 03 .venv avoided missing packages and Python 3.14 Matplotlib abort; pytest 4/4. Seasonal naive beat the fixed model. |
| 13 | PASS | Existing .venv; run, inference CLI, and pytest 4/4; MAE 2.794 minutes/R² 0.892. |

## Remaining blockers

- The source prompts request dashboards, external Kaggle/TLC data, AutoGluon, browser tours, and other production-scale features that are not present in this compact offline checkout; each README records the deviation.
- System Python does not provide all project dependencies. Reproduction should use the documented local environment paths or install the small requirements files in a compatible Python version.
- Python 3.14 Matplotlib aborted while building its font cache in Projects 06 and 12; the same code completed with the existing Python 3.12 scientific environment.

