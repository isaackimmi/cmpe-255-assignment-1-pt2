# Final Polish Review — Project 02

## Recommendation

**Conditionally ready as a teaching miniature, not ready to present as evidence of chatbot or Transformer quality.** The current baseline pipeline is substantially sound for a strict chronological character-stream experiment: it validates split fractions, fits a train-only vocabulary with `<UNK>`, carries boundary context, reports validation/test metrics, selects the Torch checkpoint on validation, and evaluates test once. The main polish work should make the evaluation protocol and UI tell the same, current story.

Before submission, prioritize the two P1 items below, then address the P2 items if time permits. Keep the limitation explicit: this is an auditable mechanics demo on 360 synthetic characters, not a meaningful language-quality benchmark.

## Verification performed

- `python3 -m unittest discover -v`: **11 tests run; 8 passed; 3 optional Torch tests skipped** because PyTorch is not installed in this environment.
- Baseline reproduction completed and matched the checked-in `metrics.json`: test loss `3.3023`, test perplexity `27.1741`, 36 test targets, one test evaluation.
- Torch behavior was reviewed statically and is covered by Torch-gated tests, but the actual Torch training/evaluation path was not executed locally.
- No source code was modified. This review is the only new project file.

## Prioritized findings

### [P1] The checked-in evidence artifact is stale and contradicts the current run

**Evidence:** `artifacts/run_evidence.svg:1` labels the run as held-out perplexity `22.1789` with `unittest: 3/3 passed`. The current `metrics.json:98-105` reports test perplexity `27.1741` and one test evaluation, while the current test command reports 11 tests, 8 passes, and 3 optional skips. The older `DS_REVIEW.md:5-25` also describes a Transformer with no validation/test evaluation and vocabulary leakage, which are no longer true of `nano_llm.py:297-417` and `nano_llm.py:308-315`.

**Impact:** A reviewer can reasonably treat the repository as internally inconsistent or believe the wrong result. This is an evidence-integrity problem, not merely cosmetic drift.

**Action:** Regenerate `artifacts/run_evidence.svg` from the current baseline, or clearly label it as historical. Update or supersede `DS_REVIEW.md` so it distinguishes resolved findings from remaining risks. Make the checked-in artifact and README reproduce command agree on one canonical run.

### [P1] The UI is interactive at the shell level, but does not interactively expose model behavior

**Evidence:** `index.html:96-109` presents a chat form, but explicitly calls it a curated preview. `src/app.js:11-18` contains a fixed keyword-to-answer library; `src/app.js:71-83` selects a canned response after a timeout and never invokes `nano_llm.py`, reads the generated `sample`, or uses token probabilities. There is no context window, next-character distribution, temperature control, generated-token trace, attention view, or comparison of train/validation/test behavior.

**Impact:** The page is a polished, partially interactive landing page rather than an interactive explanation of why the model produces an output. The disclaimer is honest, which avoids misrepresentation, but the UI does not satisfy the strongest interpretation of “chatbot/model behavior.”

**Action:** Add one small behavior inspector. At minimum, let the user enter a prompt and show the last `order` characters, candidate next characters with smoothed probabilities, selected character, and a step-by-step generated sample. If live Python inference is intentionally out of scope, implement the inspector from a serialized artifact and label it as a deterministic replay. Also expose the validation/test metrics and OOV counts so the UI teaches evaluation rather than only displaying headline numbers.

### [P2] The character split is valid for stream continuation but weak for a conversational claim

**Evidence:** `nano_llm.py:83-92` performs a raw chronological character split. With the checked-in corpus, the 288-character training boundary is inside `user: be concise` (`data/tiny_corpus.txt:7`), and the validation boundary is inside `assistant: Small experiments...` (`data/tiny_corpus.txt:8`). The artifact confirms only 36 characters per validation/test split (`metrics.json:6-19`).

**Impact:** The reported perplexity is meaningful as conditional suffix likelihood, but not as generalization to unseen conversations or complete chatbot turns. The held-out sets are tiny and highly correlated with the preceding text; one OOV character in validation (`metrics.json:86-96`) is mostly a split-boundary artifact.

**Action:** Choose and state one protocol. For a language-model mechanics demo, retain the chronological stream split but show the exact boundary and call the metric “conditional character-stream loss.” For a chatbot claim, split on complete user/assistant turns or conversation IDs, keep held-out turns entirely out of training, and report the number of turns as well as characters.

### [P2] The dashboard misrepresents the three-way split and hardcodes run configuration

**Evidence:** `index.html:90-92` displays only TRAIN and TEST, even though `metrics.json:6-19` contains train/validation/test partitions. `src/app.js:34-36` calculates the bar using only `train + test`, producing an 88.9% train bar for the current 80/10/10 run. The configuration panel is hardcoded as n-gram/order 3/alpha 0.20 at `index.html:112-118`; `src/app.js:23-41` updates only a few fields. If a Torch artifact is loaded, the page can still say “character n-gram” (`index.html:102`) and show the n-gram configuration.

**Impact:** The page can be factually wrong while saying the values are live from the artifact. It also hides the validation set that drives checkpoint selection.

**Action:** Render train, validation, and test from `metrics.split`; render backend and hyperparameters from `metrics.config`; display the resolved device, vocabulary size, OOV rates, best validation step, and test-evaluation count. Make the split visualization use all three partitions and adapt its labels to the loaded backend.

### [P2] The data/metric claims are too small for reliable model-quality interpretation

**Evidence:** `data/tiny_corpus.txt:1-8` contains only eight physical lines/four dialogue pairs and 360 characters. `metrics.json:91-103` evaluates only 36 validation and 36 test target characters. The project correctly warns against capability claims in `README.md:54-58`, but the UI foregrounds “HELD-OUT PERPLEXITY” at `index.html:54-57` without showing target count or the synthetic/censored nature of the estimate.

**Impact:** A single-character change can noticeably move the headline metric, and users may read the number as a model score despite the small denominator.

**Action:** Keep the experiment, but label the metric “36-character test perplexity” or show the target count beside it. Add a trivial baseline (for example, uniform-vocabulary loss) and, if making quality claims, use a larger turn-level holdout and report results across multiple seeds or bootstrap intervals.

### [P2] Reproducibility is good for the baseline but incomplete for comparable Torch experiments

**Evidence:** The artifact records corpus hash, split offsets, config, platform, vocabulary, OOV counts, device, and Torch version (`metrics.json:4-45`, `metrics.json:47-105`), and seeding/deterministic settings are implemented in `nano_llm.py:38-49`. However, `requirements.txt:1-3` permits any Torch `2.x` release, and Torch-specific tests are skipped locally. Checkpoint selection compares the rounded validation loss returned at `nano_llm.py:344-350` before choosing `nano_llm.py:367-374`.

**Impact:** Different Torch versions/devices can still vary, and rounding can select a different checkpoint when raw validation losses are close. The current artifact proves the baseline run, not an executed Torch result.

**Action:** Record the exact resolved dependency/environment for a Torch artifact, retain unrounded loss for checkpoint comparison, and check in one actual Torch artifact only when it has been executed and its tests have run. Keep the current optional-skip status visible in the UI instead of hardcoding a test count.

### [P3] Documentation contains factual drift

**Evidence:** `README.md:46`, `index.html:92`, `index.html:125`, and `src/app.js:16` call the corpus “seven-line,” while `data/tiny_corpus.txt:1-8` has eight lines. `README.md:11` and `README.md:61-62` describe a dashboard, while `README.md:58` says there is no web dashboard. The UI test status is hardcoded at `index.html:135` as “8 passed · 1 optional skip,” which is not the current 8-pass/3-skip result and would be wrong when Torch is installed.

**Action:** Establish one source of truth for corpus line/turn counts and verification status. Replace hardcoded UI copy with artifact metadata or clearly mark it as a static snapshot.

### [P3] The requested autoresearch element remains absent

**Evidence:** `README.md:56-58` explicitly acknowledges there is no genuine autoresearch/hyperparameter hill-climbing loop. The repository contains one baseline artifact and no sweep history or comparison table.

**Action:** If autoresearch is a graded requirement, add a bounded, reproducible sweep over a few declared settings (for example, n-gram order/alpha or Torch learning rate), select on validation only, and record every trial plus the final untouched test result. If it is intentionally out of scope, retain the disclosure and state that in the UI’s limitations.

## What is currently sound

- Train/validation/test split fractions are validated and non-empty (`nano_llm.py:56-92`).
- The vocabulary is fit on training text with an explicit `<UNK>` and used to encode later splits (`nano_llm.py:132-138`, `nano_llm.py:308-315`).
- N-gram evaluation includes the OOV class in the smoothed denominator and carries boundary context (`nano_llm.py:162-189`, `nano_llm.py:212-215`).
- The Torch path uses a future-blocking causal mask (`nano_llm.py:241-274`), validation checkpoint selection, and one post-selection test evaluation (`nano_llm.py:367-417`).
- The README is candid about synthetic data and non-production status (`README.md:54-58`), and the UI explicitly discloses that the chat preview is not live inference (`index.html:99`, `README.md:21`).

## Final disposition

Fix the stale evidence and make the UI’s displayed split/configuration/test status data-driven before submission. Then present the project as a **reproducible teaching experiment for causal next-character modeling**, with the optional Transformer described as an implemented path that still needs an executed Torch artifact in this environment. The work is otherwise a credible small-surface demonstration; its remaining risk is overclaiming through presentation, not a fundamental defect in the current baseline implementation.
