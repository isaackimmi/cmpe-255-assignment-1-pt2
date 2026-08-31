#!/usr/bin/env python3
"""Tiny, reproducible causal-language-model experiment.

The default backend is a dependency-free character n-gram model so the project
can be executed in a clean teaching environment. If PyTorch is installed,
``--backend torch`` trains a small decoder-only Transformer instead.

Both backends use a strict chronological character split. Validation and test
targets are teacher-forced with the preceding ground-truth characters, so the
first prediction in each suffix is conditioned on the available prefix.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

SEED = 255
UNK_TOKEN = "<UNK>"
CORPUS = """user: hello
assistant: Hello! I am Nano, a tiny language model.
user: what is machine learning?
assistant: Machine learning finds patterns in data to make useful predictions.
user: explain a transformer
assistant: A transformer uses attention to mix information across a sequence.
user: be concise
assistant: Small experiments make ideas easier to understand.
"""


def seed_everything(seed=SEED, torch_module=None):
    """Seed Python and, when available, all relevant Torch RNGs."""
    random.seed(seed)
    if torch_module is not None:
        torch_module.manual_seed(seed)
        if torch_module.cuda.is_available():
            torch_module.cuda.manual_seed_all(seed)
        if hasattr(torch_module, "use_deterministic_algorithms"):
            torch_module.use_deterministic_algorithms(True, warn_only=True)
        if hasattr(torch_module.backends, "cudnn"):
            torch_module.backends.cudnn.deterministic = True
            torch_module.backends.cudnn.benchmark = False


def load_corpus(path=None):
    return Path(path).read_text(encoding="utf-8") if path else CORPUS


def _validate_split_fractions(train_fraction, validation_fraction=0.1):
    values = (train_fraction, validation_fraction)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("train and validation fractions must be finite numbers")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be strictly between 0 and 1")
    if not 0 <= validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train_fraction + validation_fraction must be less than 1")


def split_corpus(text, fraction=.8):
    """Return a validated chronological train/test character split.

    This two-way helper is retained for callers of the original teaching API.
    The experiment uses :func:`split_train_validation_test` below.
    """
    _validate_split_fractions(fraction, 0.0)
    if len(text) < 2:
        raise ValueError("corpus must contain at least two characters")
    cut = int(len(text) * fraction)
    if cut <= 0 or cut >= len(text):
        raise ValueError("split must leave non-empty train and test partitions")
    return text[:cut], text[cut:]


def split_train_validation_test(text, train_fraction=.8, validation_fraction=.1):
    """Return non-empty chronological train, validation, and test suffixes."""
    _validate_split_fractions(train_fraction, validation_fraction)
    if len(text) < 3:
        raise ValueError("corpus must contain at least three characters")
    train_end = int(len(text) * train_fraction)
    validation_end = int(len(text) * (train_fraction + validation_fraction))
    if train_end <= 0 or validation_end <= train_end or validation_end >= len(text):
        raise ValueError("corpus is too short for the requested three-way split")
    return text[:train_end], text[train_end:validation_end], text[validation_end:]


def _hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_metadata(train, validation, test, train_fraction, validation_fraction):
    return {
        "protocol": "strict_chronological_character_split",
        "train_fraction": train_fraction,
        "validation_fraction": validation_fraction,
        "test_fraction": round(1 - train_fraction - validation_fraction, 10),
        "train_start": 0,
        "train_end": len(train),
        "validation_start": len(train),
        "validation_end": len(train) + len(validation),
        "test_start": len(train) + len(validation),
        "test_end": len(train) + len(validation) + len(test),
        "train_chars": len(train),
        "validation_chars": len(validation),
        "test_chars": len(test),
    }


class CharNGram:
    """A transparent fallback language model using smoothed next-char counts."""

    def __init__(self, order=3, alpha=.2):
        if order < 0:
            raise ValueError("order must be non-negative")
        if not math.isfinite(alpha) or alpha <= 0:
            raise ValueError("alpha must be a positive finite number")
        self.order, self.alpha = order, alpha
        self.counts = defaultdict(Counter)
        self.vocab = []

    def _encode(self, text):
        return [ch if ch in self.vocab else UNK_TOKEN for ch in text]

    def fit(self, text):
        if not text:
            raise ValueError("cannot fit an empty corpus")
        self.vocab = sorted(set(text) | {" ", "\n", UNK_TOKEN})
        encoded = self._encode(text)
        for i, target in enumerate(encoded):
            self.counts[tuple(encoded[max(0, i - self.order):i])][target] += 1

    def next_char(self, context, temperature=0.0):
        if not self.vocab:
            raise RuntimeError("fit the model before generating")
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("temperature must be a non-negative finite number")
        encoded_context = self._encode(context)
        key = tuple(encoded_context[-self.order:]) if self.order else ()
        counts = self.counts.get(key, Counter())
        weights = [counts[c] + self.alpha for c in self.vocab]
        if temperature == 0:
            return self.vocab[max(range(len(weights)), key=weights.__getitem__)]
        weights = [math.exp(math.log(weight) / temperature) for weight in weights]
        return random.choices(self.vocab, weights=weights, k=1)[0]

    def generate(self, prompt, max_new_tokens=100, temperature=0.0):
        if max_new_tokens < 0:
            raise ValueError("max_new_tokens must be non-negative")
        out = prompt
        for _ in range(max_new_tokens):
            out += self.next_char(out, temperature)
        return out

    def evaluate(self, text, context=""):
        """Score ``text`` conditioned on ``context`` and prior test characters."""
        if not text:
            return {"loss": None, "perplexity": None, "target_chars": 0,
                    "oov_count": 0, "oov_rate": None}
        if not self.vocab:
            raise RuntimeError("fit the model before evaluating")
        encoded_context = self._encode(context)
        encoded_text = self._encode(text)
        sequence = encoded_context + encoded_text
        nll = 0.0
        oov_count = 0
        context_length = len(encoded_context)
        for i, target in enumerate(encoded_text):
            position = context_length + i
            key = tuple(sequence[max(0, position - self.order):position]) if self.order else ()
            counts = self.counts.get(key, Counter())
            total = sum(counts.values()) + self.alpha * len(self.vocab)
            probability = (counts[target] + self.alpha) / total
            nll -= math.log(probability)
            oov_count += target == UNK_TOKEN
        loss = nll / len(encoded_text)
        return {
            "loss": round(loss, 4),
            "perplexity": round(math.exp(loss), 4),
            "target_chars": len(encoded_text),
            "oov_count": oov_count,
            "oov_rate": round(oov_count / len(encoded_text), 4),
        }


def _base_metadata(args, text, train, validation, test):
    return {
        "seed": args.seed,
        "corpus_sha256": _hash_text(text),
        "vocabulary_policy": "fit_on_train_only_with_explicit_<UNK>",
        "split": _split_metadata(train, validation, test, args.train_fraction, args.validation_fraction),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "config": vars(args).copy(),
    }


def run_ngram(args):
    text = load_corpus(args.corpus)
    train, validation, test = split_train_validation_test(
        text, args.train_fraction, args.validation_fraction
    )
    model = CharNGram(args.order, args.alpha)
    model.fit(train)
    validation_metrics = model.evaluate(validation, context=train[-args.order:])
    test_metrics = model.evaluate(
        test, context=(train + validation)[-args.order:]
    )
    metrics = {
        "backend": "stdlib_char_ngram",
        **_base_metadata(args, text, train, validation, test),
        "device": "cpu",
        "torch_version": None,
        "vocabulary": model.vocab,
        "vocab_size": len(model.vocab),
        "oov_counts": {
            "train": 0,
            "validation": validation_metrics["oov_count"],
            "test": test_metrics["oov_count"],
        },
        "validation": validation_metrics,
        "test": test_metrics,
        "test_evaluations": 1,
        # Keep the original top-level fields used by the existing dashboard.
        "train_chars": len(train),
        "test_chars": len(test),
        "loss": test_metrics["loss"],
        "perplexity": test_metrics["perplexity"],
    }
    metrics["sample"] = model.generate(args.prompt, args.max_new_tokens, args.temperature)
    return metrics


def make_causal_mask(size, device, torch_module):
    """Return a boolean mask where True entries block future attention."""
    return torch_module.triu(
        torch_module.ones(size, size, device=device, dtype=torch_module.bool),
        diagonal=1,
    )


def build_tiny_transformer(vocab_size, d_model, n_heads, n_layers, block_size,
                           torch_module, nn_module):
    """Build the optional model separately so its causal behavior is testable."""
    class TinyTransformer(nn_module.Module):
        def __init__(self):
            super().__init__()
            self.tok = nn_module.Embedding(vocab_size, d_model)
            self.pos = nn_module.Embedding(block_size, d_model)
            layer = nn_module.TransformerEncoderLayer(
                d_model, n_heads, 4 * d_model, dropout=0.0, batch_first=True
            )
            self.body = nn_module.TransformerEncoder(layer, n_layers)
            self.head = nn_module.Linear(d_model, vocab_size)

        def forward(self, x, y=None):
            length = x.size(1)
            positions = torch_module.arange(length, device=x.device)
            hidden = self.tok(x) + self.pos(positions)
            mask = make_causal_mask(length, x.device, torch_module)
            logits = self.head(self.body(hidden, mask=mask))
            loss = None
            if y is not None:
                loss = nn_module.functional.cross_entropy(
                    logits.reshape(-1, vocab_size), y.reshape(-1)
                )
            return logits, loss

    return TinyTransformer()


def run_torch(args):
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise SystemExit(
            "PyTorch is not installed; use the default backend or install requirements.txt"
        ) from exc

    if args.d_model <= 0 or args.n_heads <= 0 or args.n_layers <= 0:
        raise ValueError("d_model, n_heads, and n_layers must be positive")
    if args.d_model % args.n_heads:
        raise ValueError("d_model must be divisible by n_heads")
    if args.block_size <= 0 or args.batch_size <= 0 or args.steps <= 0:
        raise ValueError("block_size, batch_size, and steps must be positive")
    if args.lr <= 0 or not math.isfinite(args.lr):
        raise ValueError("lr must be a positive finite number")

    seed_everything(args.seed, torch)
    text = load_corpus(args.corpus)
    train, validation, test = split_train_validation_test(
        text, args.train_fraction, args.validation_fraction
    )
    if len(train) < args.block_size + 1:
        raise ValueError(
            f"training split has {len(train)} characters; block_size requires at least "
            f"{args.block_size + 1}"
        )

    chars = sorted(set(train) | {" ", "\n", UNK_TOKEN})
    stoi = {char: index for index, char in enumerate(chars)}
    itos = dict(enumerate(chars))

    def enc(value):
        return torch.tensor([stoi.get(char, stoi[UNK_TOKEN]) for char in value], dtype=torch.long)

    tr, va, te = enc(train), enc(validation), enc(test)
    requested_device = args.device
    if requested_device == "auto":
        requested_device = "cuda" if torch.cuda.is_available() else "cpu"
    if requested_device == "cuda" and not torch.cuda.is_available():
        raise ValueError("--device cuda requested, but CUDA is not available")
    device = torch.device(requested_device)

    model = build_tiny_transformer(
        len(chars), args.d_model, args.n_heads, args.n_layers,
        args.block_size, torch, nn
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    def evaluate_tokens(targets, context):
        """Teacher-force target tokens while scoring only target positions."""
        full = torch.cat((context, targets)).to(device)
        context_length = len(context)
        nll = 0.0
        with torch.no_grad():
            for index in range(len(targets)):
                position = context_length + index
                start = max(0, position - args.block_size)
                inputs = full[start:position].unsqueeze(0)
                logits, _ = model(inputs)
                target = full[position].view(1)
                nll += float(nn.functional.cross_entropy(logits[0, -1], target))
        loss = nll / len(targets)
        oov_count = int((targets == stoi[UNK_TOKEN]).sum().item())
        return {
            "loss": round(loss, 4),
            "perplexity": round(math.exp(loss), 4),
            "target_chars": len(targets),
            "oov_count": oov_count,
            "oov_rate": round(oov_count / len(targets), 4),
        }

    best_state = None
    best_validation = None
    best_step = None
    start_time = time.time()
    model.train()
    valid_start_count = len(tr) - args.block_size
    for step in range(1, args.steps + 1):
        starts = torch.randint(0, valid_start_count, (args.batch_size,))
        x = torch.stack([tr[index:index + args.block_size] for index in starts]).to(device)
        y = torch.stack([tr[index + 1:index + args.block_size + 1] for index in starts]).to(device)
        _, loss = model(x, y)
        opt.zero_grad()
        loss.backward()
        opt.step()

        if step % args.eval_interval == 0 or step == args.steps:
            model.eval()
            validation_metrics = evaluate_tokens(va, tr[-args.block_size:])
            if best_validation is None or validation_metrics["loss"] < best_validation["loss"]:
                best_validation = validation_metrics
                best_state = copy.deepcopy(model.state_dict())
                best_step = step
            model.train()

    if best_state is None:
        raise RuntimeError("no validation checkpoint was produced")
    model.load_state_dict(best_state)
    model.eval()
    # Test is evaluated once, after selecting the checkpoint using validation only.
    test_metrics = evaluate_tokens(te, torch.cat((tr, va))[-args.block_size:])

    ids = enc(args.prompt).to(device)
    prompt_length = len(ids)
    with torch.no_grad():
        for _ in range(args.max_new_tokens):
            if len(ids) == 0:
                ids = tr[-1:].to(device)
            inputs = ids[-args.block_size:].unsqueeze(0)
            logits, _ = model(inputs)
            ids = torch.cat((ids, logits[0, -1].argmax().view(1)))

    oov_counts = {
        "train": 0,
        "validation": sum(stoi.get(char, stoi[UNK_TOKEN]) == stoi[UNK_TOKEN] for char in validation),
        "test": sum(stoi.get(char, stoi[UNK_TOKEN]) == stoi[UNK_TOKEN] for char in test),
    }
    return {
        "backend": "torch_transformer",
        **_base_metadata(args, text, train, validation, test),
        "vocabulary": chars,
        "vocab_size": len(chars),
        "oov_counts": oov_counts,
        "device": str(device),
        "torch_version": torch.__version__,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "steps": args.steps,
        "best_validation_step": best_step,
        "checkpoint_identifier": f"validation_best_step_{best_step}",
        "seconds": round(time.time() - start_time, 2),
        "validation": best_validation,
        "test": test_metrics,
        "train_chars": len(train),
        "test_chars": len(test),
        "loss": test_metrics["loss"],
        "perplexity": test_metrics["perplexity"],
        "test_evaluations": 1,
        "sample": args.prompt + "".join(
            itos[int(index)] for index in ids[prompt_length:].detach().cpu()
        ),
    }


def positive_int(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["ngram", "torch"], default="ngram")
    parser.add_argument("--corpus")
    parser.add_argument("--prompt", default="user: explain a transformer\nassistant:")
    parser.add_argument("--max-new-tokens", type=nonnegative_int, default=80)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--train-fraction", type=float, default=.8)
    parser.add_argument("--validation-fraction", type=float, default=.1)
    parser.add_argument("--order", type=nonnegative_int, default=3)
    parser.add_argument("--alpha", type=float, default=.2)
    parser.add_argument("--steps", type=positive_int, default=120)
    parser.add_argument("--eval-interval", type=positive_int, default=20)
    parser.add_argument("--batch-size", type=positive_int, default=8)
    parser.add_argument("--block-size", type=positive_int, default=64)
    parser.add_argument("--d-model", type=positive_int, default=32)
    parser.add_argument("--n-heads", type=positive_int, default=4)
    parser.add_argument("--n-layers", type=positive_int, default=2)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", default="metrics.json")
    args = parser.parse_args()
    seed_everything(args.seed)
    if not math.isfinite(args.temperature) or args.temperature < 0:
        parser.error("--temperature must be a non-negative finite number")
    try:
        result = run_torch(args) if args.backend == "torch" else run_ngram(args)
    except ValueError as exc:
        parser.error(str(exc))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
