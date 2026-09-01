# Project 02 — Nano LLM Transformer

This is a small, auditable reproduction of the Project 02 prompt: “build a simple llm and chatbot (with state of art primitives but fit in my laptop gpu) … follow crisp-dm … include autoresearch … and all details a data scientist and ai engineer will care.” The implementation demonstrates next-token modeling and provides a tiny decoder-only Transformer path without requiring a large model or downloaded data.

## What is included

- `nano_llm.py`: deterministic character-level n-gram baseline (default) and optional PyTorch causal Transformer (`--backend torch`). Both fit vocabulary on training data only and use an explicit `<UNK>` token.
- `data/tiny_corpus.txt`: deliberately small local chat corpus.
- `test_nano_llm.py`: smoke tests for split integrity, learning behavior, and CLI output.
- `metrics.json`: generated experiment artifact (create it with the command below).
- `ml/`: modular model boundary split across artifact loading, validation, deterministic inference, typed errors, and project-safe path resolution. `model_adapter.py` remains a compatibility façade.
- `server/`: FastAPI service composed from an application factory, feature routers, Pydantic schemas, error handlers, and evidence/inference services.
- `client/`: React + Vite evidence studio using Radix Themes, feature components, shared UI primitives, an API service, and an async state hook.
- `test_nano_llm.py` and `tests/`: DS-core, API-contract, and client-wiring tests.

## Run the E2E application

From this directory, generate the default artifact and install the two small runtime environments:

```bash
python3 nano_llm.py --corpus data/tiny_corpus.txt --output metrics.json
python3 -m pip install -r server/requirements.txt
cd client && npm install
```

Run the API and client in separate terminals:

```bash
# terminal 1
cd server
python3 -m uvicorn main:app --host 127.0.0.1 --port 8002

# terminal 2
cd client
npm run dev
```

Open <http://127.0.0.1:5175/>. Vite proxies `/api` to FastAPI. The client displays explicit API loading/error states and requests metrics, behavior metadata, generation traces, and probability distributions from the server. No model training occurs in a request; the API rebuilds the deterministic default adapter from the local corpus and recorded chronological training boundary.

### Frontend composition

- `src/components/layout/`: `AppShell`, navigation, and footer composition.
- `src/components/evidence/`: metric cards, evidence metrics, corpus split, and run manifest views.
- `src/components/playground/`: generation form, probability panel/list, behavior inspector, and trace list.
- `src/components/ui/`: shared `Panel`, `SectionHeader`, and `StatusPill` primitives built on Radix Themes.
- `src/api/` and `src/hooks/`: transport errors, endpoint functions, loading state, and generation orchestration.
- `src/styles/`: design tokens, responsive layout, and component styling with no remote font dependency.

The FastAPI entrypoint is intentionally thin; routes, schemas, services, and exception handling are separately testable. The ML façade similarly delegates to focused artifact, validation, path, error, and inference modules.

For a production-like static client build, run `npm run build` in `client/`; the generated `client/dist/` can be served behind an API reverse proxy.

Run the frontend behavior and accessibility suite without starting either local service:

```bash
cd client
npm test
npm run build
```

The Vitest/React Testing Library suite renders the application and covers connected, partial, unavailable, and retry states; form validation and pending/error behavior; API payload/error mapping; latest-generation cancellation; probability/trace semantics; and basic `jest-axe` scans. Evidence loading uses independently tracked resources, while generation errors remain local to the playground.

## Reproduce

From this directory:

```bash
python3 nano_llm.py --corpus data/tiny_corpus.txt --output metrics.json
python3 -m unittest discover -v
python3 -m unittest discover -s tests -v
```

The standard-library backend completes on CPU in under a second and reports validation and untouched held-out test character loss/perplexity plus OOV counts, split metadata, and a serialized behavior trace. The default protocol is a strict chronological 80/10/10 character split. Boundary context is carried from the preceding ground-truth prefix into each suffix; targets within a suffix are teacher-forced. The test suffix is scored only after training/model selection. The displayed perplexity is a conditional character-stream metric over 36 test targets, not a conversational quality score.

For the actual Transformer experiment, install the optional dependency and use CPU-safe settings:

```bash
python3 -m pip install -r requirements.txt
python3 nano_llm.py --backend torch --corpus data/tiny_corpus.txt --steps 120 --d-model 32 --n-layers 2 --block-size 64 --output torch_metrics.json
```

The seed is fixed at `255`; override it with `--seed` for an intentional variation. `--device auto` selects CUDA when available and otherwise CPU; use `--device cpu` for a stable CPU reproduction. The Torch artifact records the resolved device, PyTorch version, corpus hash, split offsets, complete configuration, frozen vocabulary, OOV counts, validation checkpoint metrics, and one final test evaluation. All data is local, so no credentials or network download is required.

## CRISP-DM record

1. **Business understanding:** demonstrate the mechanics of a tiny conversational autoregressive model that can fit laptop resources.
2. **Data understanding:** inspect an 8-line/four-pair synthetic chat corpus; the corpus is intentionally educational, not representative of language.
3. **Data preparation:** preserve character order and split the corpus chronologically (80/10/10) to avoid future-character leakage; the vocabulary is fit on training characters only and unseen characters map to `<UNK>`.
4. **Modeling:** baseline uses smoothed character n-gram counts. Optional path uses token embeddings, learned positional embeddings, masked self-attention via `TransformerEncoder`, and a linear next-character head.
5. **Evaluation:** validation loss/perplexity is used for Transformer checkpoint selection; the untouched test suffix is then scored once. Both backends report loss, perplexity, target count, and OOV rate for validation/test.
6. **Deployment/monitoring:** CLI JSON output is the portable inference artifact; add a larger held-out set, toxicity checks, and latency monitoring before real use.

## Baseline result

Run the reproduce command to regenerate `metrics.json`. Because the tiny corpus is deterministic, the held-out metrics and greedy sample are stable for the default seed (within the recorded Python/runtime environment). The output is a sanity check, not evidence of useful language capability.

## Limitations and deviations

This is intentionally a lightweight reproduction, not NanoLlama: it has no pretrained weights, BPE tokenizer, instruction tuning, or genuine autoresearch/hyperparameter hill-climbing loop. The prompt’s “state of art primitives” is represented in the optional causal Transformer, while the default uses a dependency-free baseline because the assignment environment may not have PyTorch. The corpus is synthetic and too small for meaningful generalization. The Transformer implementation is a teaching miniature and should not be used for production inference. The Torch path is optional and CPU-safe; it is not presented as a pretrained or production GPU model.
## E2E and DS contracts

- **Prompt alignment:** Public Project 02 asks for a laptop-sized LLM/chatbot with CRISP-DM, dashboard, and autoresearch; next-token modeling and optional causal Transformer are present.
- **Results/artifacts:** `metrics.json` records train/validation/test sizes, a train-only vocabulary with OOV accounting, validation/test metrics, corpus hash, split offsets, runtime configuration, environment metadata, and serialized replay distributions/traces; the unittest suite covers split validation, OOV normalization, boundary context, replay serialization, CLI validation, and the causal mask when Torch is installed.
- **API boundary:** FastAPI validates prompt length, generation length, temperature, and probability contexts. API responses preserve normalized candidate probabilities and deterministic temperature-zero traces.
- **Client boundary:** The Vite client calls `/api/metrics`, `/api/behavior`, `/api/generate`, and `/api/probabilities`; rendered React tests verify loading, partial evidence, retry, generation, latest-request protection, semantic lists/meters, and accessibility behavior.
- **Issue/resolution:** PyTorch, pretrained weights, tokenizer, and hill-climbing remain optional/absent for offline reproducibility. The default API backend is a transparent n-gram adapter, while the optional Transformer remains explicitly labeled.
