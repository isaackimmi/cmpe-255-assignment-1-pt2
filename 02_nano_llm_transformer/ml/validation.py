"""Integrity checks for the checked-in language-model evidence artifact."""
from __future__ import annotations
import hashlib
from nano_llm import CharNGram, UNK_TOKEN, load_corpus, split_train_validation_test
from .errors import ArtifactInvalid, ArtifactMismatch, ArtifactMissing
from .paths import resolve_project_path

def _mismatch(message: str) -> None:
    raise ArtifactMismatch(message)

def validate_artifact(metrics: dict) -> None:
    config, split, vocabulary = metrics.get("config"), metrics.get("split"), metrics.get("vocabulary")
    if not isinstance(config, dict) or not isinstance(split, dict) or not isinstance(vocabulary, list):
        raise ArtifactInvalid("metrics.json is missing config, split, or vocabulary metadata")
    try:
        text = load_corpus(str(resolve_project_path(config.get("corpus", "data/tiny_corpus.txt"))))
    except FileNotFoundError as exc:
        raise ArtifactMissing("configured corpus file is not available") from exc
    except (OSError, ValueError) as exc:
        raise ArtifactInvalid("configured corpus path or file is invalid") from exc
    if metrics.get("corpus_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
        _mismatch("corpus hash does not match metrics.json")
    try:
        train, validation, test = split_train_validation_test(text, float(split["train_fraction"]), float(split["validation_fraction"]))
        expected_offsets = {"train_start": 0, "train_end": len(train), "validation_start": len(train), "validation_end": len(train) + len(validation), "test_start": len(train) + len(validation), "test_end": len(text)}
        for key, expected in expected_offsets.items():
            if split.get(key) != expected:
                _mismatch(f"split offset {key} does not match the corpus")
        if [split.get(f"{name}_chars") for name in ("train", "validation", "test")] != [len(train), len(validation), len(test)]:
            _mismatch("split character counts do not match the corpus")
    except (KeyError, TypeError, ValueError) as exc:
        raise ArtifactInvalid("split metadata is malformed") from exc
    if metrics.get("vocabulary_policy") != "fit_on_train_only_with_explicit_<UNK>":
        _mismatch("unsupported vocabulary policy in metrics.json")
    model = CharNGram(order=int(config.get("order", 3)), alpha=float(config.get("alpha", 0.2)))
    model.fit(train)
    if model.vocab != vocabulary or UNK_TOKEN not in vocabulary:
        _mismatch("recorded vocabulary does not match the train-only vocabulary")
    if metrics.get("vocab_size") != len(vocabulary):
        _mismatch("recorded vocabulary size does not match vocabulary")
