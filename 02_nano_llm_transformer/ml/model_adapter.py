"""Small model adapter shared by the FastAPI service and offline tests."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

from nano_llm import CharNGram, UNK_TOKEN, load_corpus, split_train_validation_test

ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "metrics.json"
CORPUS_PATH = ROOT / "data" / "tiny_corpus.txt"


class ArtifactError(Exception):
    """Safe, typed error raised when an inference artifact cannot be trusted."""

    code = "artifact_error"
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ArtifactMissing(ArtifactError):
    code = "artifact_missing"
    status_code = 503


class ArtifactInvalid(ArtifactError):
    code = "artifact_invalid"
    status_code = 500


class ArtifactMismatch(ArtifactError):
    code = "artifact_mismatch"
    status_code = 409


class BackendUnsupported(ArtifactError):
    code = "backend_unsupported"
    status_code = 501


def load_metrics() -> dict:
    try:
        payload = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactMissing("metrics.json is not available; regenerate the canonical artifact") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactInvalid("metrics.json is unreadable or invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ArtifactInvalid("metrics.json must contain a JSON object")
    validate_artifact(payload)
    payload["artifact_backend"] = payload.get("backend", "unknown")
    payload["inference_backend"] = "stdlib_char_ngram" if payload.get("backend") == "stdlib_char_ngram" else "unsupported"
    return payload


def _mismatch(message: str):
    raise ArtifactMismatch(message)


def validate_artifact(metrics: dict) -> None:
    """Verify the artifact still describes the local corpus and model contract."""
    config = metrics.get("config")
    split = metrics.get("split")
    vocabulary = metrics.get("vocabulary")
    if not isinstance(config, dict) or not isinstance(split, dict) or not isinstance(vocabulary, list):
        raise ArtifactInvalid("metrics.json is missing config, split, or vocabulary metadata")
    try:
        corpus_path = (ROOT / config.get("corpus", "data/tiny_corpus.txt")).resolve()
        if ROOT not in corpus_path.parents:
            raise ArtifactInvalid("configured corpus path must remain inside the project")
        text = load_corpus(str(corpus_path))
    except FileNotFoundError as exc:
        raise ArtifactMissing("configured corpus file is not available") from exc
    except OSError as exc:
        raise ArtifactInvalid("configured corpus file could not be read") from exc
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if metrics.get("corpus_sha256") != digest:
        _mismatch("corpus hash does not match metrics.json")
    try:
        train_fraction = float(split["train_fraction"])
        validation_fraction = float(split["validation_fraction"])
        train, validation, test = split_train_validation_test(text, train_fraction, validation_fraction)
        expected_offsets = {
            "train_start": 0, "train_end": len(train),
            "validation_start": len(train), "validation_end": len(train) + len(validation),
            "test_start": len(train) + len(validation), "test_end": len(text),
        }
        for key, expected in expected_offsets.items():
            if split.get(key) != expected:
                _mismatch(f"split offset {key} does not match the corpus")
        if [split.get(f"{name}_chars") for name in ("train", "validation", "test")] != [len(train), len(validation), len(test)]:
            _mismatch("split character counts do not match the corpus")
    except (KeyError, TypeError, ValueError) as exc:
        raise ArtifactInvalid("split metadata is malformed") from exc
    if metrics.get("vocabulary_policy") != "fit_on_train_only_with_explicit_<UNK>":
        _mismatch("unsupported vocabulary policy in metrics.json")
    order = int(config.get("order", 3))
    alpha = float(config.get("alpha", 0.2))
    model = CharNGram(order=order, alpha=alpha)
    model.fit(train)
    if model.vocab != vocabulary or UNK_TOKEN not in vocabulary:
        _mismatch("recorded vocabulary does not match the train-only vocabulary")
    if metrics.get("vocab_size") != len(vocabulary):
        _mismatch("recorded vocabulary size does not match vocabulary")


def build_model(metrics: dict | None = None) -> CharNGram:
    metrics = metrics or load_metrics()
    if metrics.get("backend") != "stdlib_char_ngram":
        raise BackendUnsupported(
            f"artifact backend {metrics.get('backend', 'unknown')} has no executable inference adapter; use a stdlib_char_ngram artifact"
        )
    split = metrics["split"]
    text = load_corpus(str(CORPUS_PATH))
    train = text[: int(split["train_end"])]
    config = metrics.get("config", {})
    model = CharNGram(order=int(config.get("order", 3)), alpha=float(config.get("alpha", 0.2)))
    model.fit(train)
    return model


def generate(prompt: str, max_new_tokens: int = 16, temperature: float = 0.0) -> dict:
    return build_model().replay(prompt, max_new_tokens=max_new_tokens, temperature=temperature)


def probabilities(context: str) -> list[dict]:
    return build_model().next_distribution(context)
