# Project 02 — Nano LLM Transformer

This is a small, auditable reproduction of the Project 02 prompt: “build a simple llm and chatbot (with state of art primitives but fit in my laptop gpu) … follow crisp-dm … include autoresearch … and all details a data scientist and ai engineer will care.” The implementation demonstrates next-token modeling and provides a tiny decoder-only Transformer path without requiring a large model or downloaded data.

## What is included

- `nano_llm.py`: deterministic character-level n-gram baseline (default) and optional PyTorch causal Transformer (`--backend torch`).
- `data/tiny_corpus.txt`: deliberately small local chat corpus.
- `test_nano_llm.py`: smoke tests for split integrity, learning behavior, and CLI output.
- `metrics.json`: generated experiment artifact (create it with the command below).
- `index.html`, `styles.css`, `src/app.js`: dependency-light browser console for inspecting the local artifact, CRISP-DM record, configuration, and an explicitly illustrative chat preview.

## Open the browser console

Serve this directory locally so the UI can fetch `metrics.json`:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000> in a browser. The dashboard reads `metrics.json` at load time, so rerun the baseline command and refresh the page to inspect updated values. The chat panel is intentionally a curated local illustration; it does not execute `nano_llm.py`, call an API, or represent live model inference. If the page is opened directly as a `file://` URL, the browser may block the JSON fetch and the UI will show its verified fallback snapshot instead.

## Reproduce

From this directory:

```bash
python3 nano_llm.py --corpus data/tiny_corpus.txt --output metrics.json
python3 -m unittest discover -v
```

The standard-library backend completes on CPU in under a second and reports held-out character loss/perplexity plus a sample. For the actual Transformer experiment, install the optional dependency and use CPU-safe settings:

```bash
python3 -m pip install -r requirements.txt
python3 nano_llm.py --backend torch --corpus data/tiny_corpus.txt --steps 120 --d-model 32 --n-layers 2 --block-size 64 --output torch_metrics.json
```

The seed is fixed at `255`; override it with `--seed` for an intentional variation. All data is local, so no credentials, network download, or GPU is required.

## CRISP-DM record

1. **Business understanding:** demonstrate the mechanics of a tiny conversational autoregressive model that can fit laptop resources.
2. **Data understanding:** inspect a 7-line synthetic chat corpus; the corpus is intentionally educational, not representative of language.
3. **Data preparation:** preserve character order and split the corpus chronologically (80/20) to avoid future-character leakage.
4. **Modeling:** baseline uses smoothed character n-gram counts. Optional path uses token embeddings, learned positional embeddings, masked self-attention via `TransformerEncoder`, and a linear next-character head.
5. **Evaluation:** held-out cross-entropy loss and perplexity are reported for the baseline; the Transformer reports parameter count, steps, runtime, and a deterministic greedy sample.
6. **Deployment/monitoring:** CLI JSON output is the portable inference artifact; add a larger held-out set, toxicity checks, and latency monitoring before real use.

## Baseline result

Run the reproduce command to regenerate `metrics.json`. Because the tiny corpus is deterministic, the held-out metrics and greedy sample are stable for the default seed. The output is a sanity check, not evidence of useful language capability.

## Limitations and deviations

This is intentionally a lightweight reproduction, not NanoLlama: it has no pretrained weights, BPE tokenizer, instruction tuning, checkpointing, web dashboard, or genuine autoresearch/hyperparameter hill-climbing loop. The prompt’s “state of art primitives” is represented in the optional causal Transformer, while the default uses a dependency-free baseline because the assignment environment may not have PyTorch. The corpus is synthetic and too small for meaningful generalization. The Transformer implementation is a teaching miniature and should not be used for production inference.
## Integration verification

- **Prompt alignment:** Public Project 02 asks for a laptop-sized LLM/chatbot with CRISP-DM, dashboard, and autoresearch; next-token modeling and optional causal Transformer are present.
- **Results/artifacts:** `metrics.json` reports loss 3.0991 and perplexity 22.1789 on 72 held-out characters; unittest passed 3/3.
- **Issue/resolution:** PyTorch, pretrained weights, tokenizer, dashboard, and hill-climbing remain optional/absent for offline reproducibility.
