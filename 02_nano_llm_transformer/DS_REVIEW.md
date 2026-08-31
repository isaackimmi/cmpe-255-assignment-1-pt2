# Data-Science Robustness Review — Project 02

## Scope and conclusion

This review covers language-model data preparation, train/validation/test separation, causal masking, evaluation, reproducibility, CPU-safe execution, and the meaning of the reported metrics. Source code was not modified. The implementation is a useful teaching miniature and the dependency-free baseline is easy to run, but the Transformer path is not currently an auditable evaluated experiment, and the baseline perplexity is not a fully valid held-out language-model metric for this corpus.

Severity uses `P1` for correctness or validity problems that should be fixed before treating results as evidence, `P2` for important robustness or experimental-design gaps, and `P3` for lower-impact documentation or product limitations.

## Findings

### [P1] The Transformer vocabulary is built with test-set information

Evidence: `nano_llm.py:83-86` splits the text into `train` and `test`, then constructs `chars = sorted(set(text))` from the complete corpus before encoding either split. The test contains an uppercase `S` that does not occur in the training prefix (`data/tiny_corpus.txt`, 360 characters; 80% cut at character 288; the held-out suffix has `S` as a train-unseen character).

Impact: the model knows the identity of test-only characters and allocates output/embedding classes for them. This is vocabulary leakage. It is especially problematic if the Transformer is later given a test loss: the test set has influenced model dimensionality even though its character frequencies are not used.

Fix: split first, fit the vocabulary/tokenizer on training data only, and add an explicit `<UNK>`/OOV symbol. Encode validation and test characters through that frozen training mapping. Record vocabulary size and OOV counts for every split.

### [P1] The Transformer has no validation or held-out evaluation

Evidence: `nano_llm.py:83` creates `train, test`, but the Transformer training loop at `nano_llm.py:100-105` never consumes `test` or a validation split. The returned artifact at `nano_llm.py:110` contains only backend, seed, parameter count, steps, runtime, and a greedy sample; it contains no loss or perplexity. The existing `metrics.json:2-8` is a baseline (`stdlib_char_ngram`) artifact, not a Transformer evaluation.

Impact: there is no validation set for model-selection decisions and no test loss/perplexity for the Transformer. A sample and runtime cannot establish predictive quality, compare configurations, or detect overfitting. The README's statement that the Transformer reports parameter count/steps/runtime/sample (`README.md:46-48`) accurately describes the gap rather than closing it.

Fix: create train/validation/test splits before training, evaluate cross-entropy and perplexity on validation during training, select the final checkpoint using validation only, and evaluate the untouched test set exactly once. Report split sizes, OOV rate, loss, perplexity, and the number of evaluated target characters.

### [P1] Baseline OOV scoring produces a non-normalized probability model

Evidence: `CharNGram.fit` defines `self.vocab` from training text only (`nano_llm.py:34-37`). `CharNGram.evaluate` then assigns `(counts[target] + alpha) / total` to every test target (`nano_llm.py:57-63`) even when `target` is not in `self.vocab`. The current corpus has a train-unseen `S` in the test suffix.

Impact: an unseen target receives a positive pseudo-probability, but it is not included in the denominator's vocabulary mass. Consequently, probabilities over the possible outputs do not sum to one for OOV cases, so the reported `loss=3.0991` and `perplexity=22.1789` are not strictly valid perplexity for the fitted model. Generation also cannot emit an unseen character because `next_char` selects only `self.vocab` (`nano_llm.py:39-46`).

Fix: use a frozen training vocabulary plus an explicit OOV symbol, map unseen test characters to it, and include that symbol in both the denominator and generation vocabulary. Alternatively, report an explicit OOV-aware metric and do not call it ordinary perplexity.

### [P2] The chronological split cuts through a chat record and evaluation drops boundary context

Evidence: `split_corpus` cuts at a raw character offset (`nano_llm.py:23-25`). For the supplied 360-character corpus, the 288-character boundary falls inside `user: be concise`: the training text ends with `user: b` and the test starts with `e concise\nassistant: ...`. In addition, `CharNGram.evaluate` builds each context from the test string alone (`nano_llm.py:57-60`), so the first test characters are scored from an empty/short context rather than from the final training context.

Impact: the test set is not a set of complete conversational examples; it begins mid-utterance and is dominated by one synthetic response. The metric is also not the exact likelihood of the chronological suffix conditioned on the available training prefix. The current context-boundary correction changes the computed result slightly (from the stored 22.1789 to approximately 22.1378 perplexity), but the larger issue is that the evaluation protocol is implicit and hard to interpret.

Fix: define the unit of splitting explicitly. For conversational data, split on complete turns or conversation IDs and keep all text for a held-out conversation out of training. For a strict chronological character stream, carry `train[-order:]` into the first test prediction, then roll forward using only ground-truth prior test characters. Document whether the metric is conditional teacher-forced likelihood or independent-example likelihood.

### [P2] Split arguments allow silently invalid experiments

Evidence: the CLI accepts any numeric `--train-fraction` without validation (`nano_llm.py:113`), while `split_corpus` clamps the cut to at least one character but does not enforce an upper bound (`nano_llm.py:23-25`). In verification, `--train-fraction 1` and `1.5` exited successfully with `train_chars=360`, `test_chars=0`, and null loss/perplexity; `--train-fraction 0` trained on one character and scored the remaining 359 characters.

Impact: a typo can produce a successful-looking artifact with no test evaluation or an unusable training set. The Transformer path has additional edge cases: when `len(train) == block_size + 1`, its sampling range at `nano_llm.py:104` is empty and training fails; generally, the final valid window is excluded.

Fix: validate `0 < train_fraction < 1`, require non-empty splits and minimum sequence lengths, and fail fast with a clear error. Compute the valid start count as `len(train) - block_size` and sample from that range; add tests for exact-boundary and too-short corpora.

### [P2] Reproducibility provenance is incomplete

Evidence: the baseline seeds Python's `random` (`nano_llm.py:17-18`) and the Transformer calls `torch.manual_seed` (`nano_llm.py:82`), but the artifact does not record the corpus hash, split boundary, full hyperparameter configuration, vocabulary, library versions, or training/evaluation protocol. `metrics.json:1-8` records only backend, seed, train/test character counts, baseline metrics, and sample. The dependency is also open-ended (`requirements.txt:2`, `torch>=2.0`).

Impact: the same seed is reproducible for the current baseline invocation, but the JSON artifact alone cannot reconstruct the Transformer run or establish that the input data and dependency versions were unchanged. Cross-version/device reproducibility is not guaranteed by `torch.manual_seed` alone.

Fix: record resolved CLI arguments, corpus SHA-256, split indices or record IDs, vocabulary/OOV policy, Python and PyTorch versions, device, optimizer settings, and final checkpoint identifier. Pin or lock dependencies for a graded reproduction, and enable/document deterministic Torch settings where supported. Keep the test set and final evaluation separate from any tuning loop.

### [P2] The optional Transformer path is not covered by the test suite

Evidence: `test_nano_llm.py:5-20` tests only split concatenation, a small n-gram behavior check, and baseline CLI JSON output. No test imports or runs `run_torch`, checks the mask, checks test evaluation, or exercises short sequences.

Impact: regressions in the optional path can pass CI unnoticed. In the current environment PyTorch is not installed, so the Transformer path could not be executed here; its review is static.

Fix: add a Torch-gated test job that verifies: future-token perturbations cannot change earlier logits; the mask has the expected upper-triangular blocked positions; train/validation/test tensors use a frozen training vocabulary; and evaluation returns finite metrics. If Torch is intentionally optional, report the skip explicitly rather than presenting the Transformer as tested.

### [P3] “GPU” support is described more broadly than implemented

Evidence: `requirements.txt:1` describes an “Optional GPU/Transformer backend,” and the README frames the experiment as laptop-GPU-friendly (`README.md:3`, `README.md:34-39`), but `run_torch` never selects a device or moves tensors/model parameters to CUDA (`nano_llm.py:76-110`).

Impact: the path is CPU-safe when PyTorch is installed, but it is not a GPU execution path. This is a capability/documentation mismatch rather than a correctness defect for the standard-library fallback.

Fix: either document the Torch path as CPU-only, or add explicit device selection, CPU fallback, and recorded device metadata. Keep the dependency-free n-gram backend documented as the guaranteed fallback.

## What passed / what is currently meaningful

- The causal mask implementation is structurally appropriate: `nano_llm.py:94-96` creates an upper-triangular boolean mask with the diagonal unmasked and passes it to `TransformerEncoder`. Under PyTorch's boolean attention-mask semantics, `True` positions are blocked, so future positions are masked. This is a static assessment because PyTorch is unavailable in the review environment; it is not backed by a regression test.
- The default backend is genuinely CPU-safe and dependency-free. Running `python3 nano_llm.py --backend torch --steps 1 --max-new-tokens 1` in this environment exits cleanly with an actionable “PyTorch is not installed” message, while the default backend runs without Torch.
- `python3 -m py_compile nano_llm.py test_nano_llm.py` passed.
- `python3 -m unittest discover -v` passed all 3 tests.
- Two default baseline runs with the same arguments produced byte-identical JSON. This supports reproducibility of the current standard-library sample, but it does not resolve the metric-validity and provenance findings above.
- The README is appropriately candid that the corpus is synthetic and the result is a sanity check rather than evidence of useful language capability (`README.md:50-56`). The stored 72-character test result should therefore be treated as a smoke test, not a model-quality claim.

## Recommended order of remediation

1. Establish record-aware train/validation/test splits and a train-only vocabulary with explicit OOV handling.
2. Add Transformer validation/test loss and perplexity, with a frozen test set and split/config metadata in the artifact.
3. Correct the n-gram boundary/OOV evaluation and validate CLI parameters and short-sequence sampling.
4. Add Torch-specific causality/evaluation tests and pin the execution environment for reproducible comparisons.
