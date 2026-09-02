# Data-Science Robustness Review — Project 02

## Current disposition

The project is a reproducible teaching miniature for causal next-character modeling. The checked-in baseline uses a strict chronological 80/10/10 character-stream protocol: the vocabulary is fitted on the training prefix with an explicit `<UNK>`, validation and test suffixes receive preceding ground-truth boundary context, and the test suffix is evaluated once after model selection. The result is useful for auditing mechanics, not for claiming conversational quality.

## Findings resolved in this polish pass

- **Evidence integrity:** `artifacts/run_evidence.svg` and `metrics.json` now describe the same current baseline run and verification snapshot. The historical held-out value is no longer presented.
- **Interactive model explanation:** the baseline artifact serializes normalized next-character distributions for each observed context plus a deterministic replay trace. `src/app.js` uses those data directly, so the browser can accept a prompt and show its context window, candidate probabilities, selected character, and step-by-step generation without pretending to run Python.
- **Three-way split visibility:** the UI renders train, validation, and test sizes from `metrics.split`, including validation/test OOV counts and rates. It does not collapse validation into train or omit the checkpoint-selection split.
- **Truthful configuration:** backend, context size/order, split fractions, smoothing or learning rate, seed, device, vocabulary size, and test-evaluation count are read from the artifact rather than hardcoded in the page.
- **Stale documentation:** the corpus is consistently described as eight physical lines/four dialogue pairs, and the dashboard is described as an artifact inspector rather than a live inference service.

## Remaining limitations

1. The 360-character corpus has only 36 validation targets and 36 test targets. The split intentionally cuts through chat text, so the metric should be read as conditional character-stream loss/perplexity, not unseen-turn or chatbot quality.
2. The optional Torch path is implemented and Torch-gated tests cover causality and evaluation, but no Torch artifact is checked in unless that path has actually been executed in the environment. The standard-library run is the canonical evidence artifact.
3. There is no bounded hyperparameter sweep or autoresearch loop. If that is a graded requirement, add a validation-selected trial table while keeping the test suffix untouched until the final run.
4. The dependency-free replay inspector supports arbitrary prompts from serialized n-gram context distributions. A Torch artifact currently exposes its serialized canonical generation trace; a new trace should be generated when changing its prompt or configuration.

## Verification scope

The local verification command is:

```text
python3 -m unittest discover -v
```

The checked-in artifact records the result of the current local suite as metadata. Optional Torch tests remain explicitly skipped when PyTorch is unavailable; this status is not inferred from the model score.

## Recommendation

Present the work as an auditable CRISP-DM mechanics demonstration. Keep the small-data warning beside the test metric and show the serialized replay when demonstrating the UI. Do not describe the baseline perplexity as a benchmark or the browser panel as a production chatbot.
