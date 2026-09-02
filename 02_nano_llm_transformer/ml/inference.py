"""Deterministic reconstruction and inference for the n-gram artifact."""
from __future__ import annotations
from nano_llm import CharNGram, load_corpus
from .artifacts import load_metrics
from .errors import BackendUnsupported
from .paths import resolve_project_path

def build_model(metrics: dict | None = None) -> CharNGram:
    metrics = metrics or load_metrics()
    if metrics.get("backend") != "stdlib_char_ngram":
        raise BackendUnsupported(f"artifact backend {metrics.get('backend', 'unknown')} has no executable inference adapter; use a stdlib_char_ngram artifact")
    config = metrics.get("config", {})
    text = load_corpus(str(resolve_project_path(config.get("corpus", "data/tiny_corpus.txt"))))
    train = text[: int(metrics["split"]["train_end"])]
    model = CharNGram(order=int(config.get("order", 3)), alpha=float(config.get("alpha", 0.2)))
    model.fit(train)
    return model

def generate(prompt: str, max_new_tokens: int = 16, temperature: float = 0.0) -> dict:
    return build_model().replay(prompt, max_new_tokens=max_new_tokens, temperature=temperature)

def probabilities(context: str) -> list[dict]:
    return build_model().next_distribution(context)
