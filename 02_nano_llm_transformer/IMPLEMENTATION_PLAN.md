# Implementation Plan — Nano LLM Transformer

## Retrospective scope

This plan documents the small, auditable character-level language-model reproduction. The default backend is a deterministic smoothed n-gram model; an optional CPU/GPU-safe causal Transformer path demonstrates the requested neural architecture without requiring a large downloaded model.

## Objectives

1. Demonstrate next-character prediction and chatbot-style generation on a laptop-sized corpus.
2. Make the full causal data and inference path inspectable: corpus, vocabulary, split, context, probabilities, and generated trace.
3. Prevent vocabulary and evaluation leakage.
4. Expose loss/perplexity and generation behavior through an evidence dashboard.
5. Keep autoresearch-style iteration reproducible through explicit configuration and artifacts.

## Data and preparation

1. Use the checked-in tiny chat corpus as the default offline dataset.
2. Split the corpus chronologically into train, validation, and test suffixes.
3. Fit the vocabulary on training text only and include an explicit `<UNK>` token.
4. Build causal context/target pairs in which each target character is predicted only from preceding characters.
5. Record corpus fingerprints, split boundaries, vocabulary metadata, backend, seed, and configuration in `metrics.json`.

## Modeling and evaluation

1. Implement a smoothed character n-gram baseline for fast deterministic runs and learning-behavior tests.
2. Provide an optional tiny decoder-only causal Transformer adapter when PyTorch is available.
3. Evaluate held-out cross-entropy/loss and perplexity; interpret lower perplexity as less surprise on unseen characters.
4. Generate one character at a time from normalized next-character probabilities.
5. Make temperature explicit and retain a generation trace containing context, probabilities, selected character, and continuation.
6. Never train or silently mutate the model during an API request; inference uses the local corpus and recorded boundary.

## Application sequence

1. Keep `nano_llm.py` as the experiment CLI and split the ML boundary into artifact loading, validation, path resolution, deterministic inference, and typed errors.
2. Split FastAPI app construction, schemas, feature routers, exception handling, evidence services, and inference services.
3. Build the React/Vite evidence studio with Radix Themes, shared panels/status primitives, metric cards, corpus-split and manifest views, generation form, probability panel, behavior inspector, and trace list.
4. Track evidence resources independently from generation state so a playground error does not blank the entire dashboard.
5. Add accessible form validation, retry/error states, request cancellation, and deterministic temperature-zero behavior.

## Validation criteria

- Chronological split and training-only vocabulary tests pass.
- The baseline shows measurable learning behavior and deterministic generation.
- API contracts validate metrics, behavior metadata, traces, and probability distributions.
- UI tests cover connected/unavailable/retry states, pending/error behavior, cancellation, semantic evidence, and accessibility.
- Standard-library reproduction and optional Transformer branches behave honestly when dependencies are unavailable.

## Limitations and next steps

The corpus is intentionally tiny and does not establish production language quality. A larger study should use a documented corpus, stronger train/validation design, checkpointed experiments, broader quality metrics, and safety evaluation.
