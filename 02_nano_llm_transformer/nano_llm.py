#!/usr/bin/env python3
"""Tiny, reproducible causal-language-model experiment.

The default backend is a dependency-free character n-gram model so the project
can be executed in a clean teaching environment.  If PyTorch is installed,
``--backend torch`` trains a small decoder-only Transformer instead.
"""
from __future__ import annotations

import argparse, json, math, random, time
from collections import Counter, defaultdict
from pathlib import Path

SEED = 255
CORPUS = """user: hello\nassistant: Hello! I am Nano, a tiny language model.\nuser: what is machine learning?\nassistant: Machine learning finds patterns in data to make useful predictions.\nuser: explain a transformer\nassistant: A transformer uses attention to mix information across a sequence.\nuser: be concise\nassistant: Small experiments make ideas easier to understand.\n"""

def seed_everything(seed=SEED):
    random.seed(seed)

def load_corpus(path=None):
    return Path(path).read_text(encoding="utf-8") if path else CORPUS

def split_corpus(text, fraction=.8):
    cut = max(1, int(len(text) * fraction))
    return text[:cut], text[cut:]

class CharNGram:
    """A transparent fallback language model using smoothed next-char counts."""
    def __init__(self, order=3, alpha=.2):
        self.order, self.alpha = order, alpha
        self.counts = defaultdict(Counter)
        self.vocab = []

    def fit(self, text):
        self.vocab = sorted(set(text) | set(" \n"))
        for i, ch in enumerate(text):
            self.counts[text[max(0, i-self.order):i]][ch] += 1

    def next_char(self, context, temperature=0.0):
        key = context[-self.order:]
        counts = self.counts.get(key, Counter())
        weights = [counts[c] + self.alpha for c in self.vocab]
        if temperature <= 0:
            return self.vocab[max(range(len(weights)), key=weights.__getitem__)]
        weights = [math.exp(math.log(w) / temperature) for w in weights]
        return random.choices(self.vocab, weights=weights, k=1)[0]

    def generate(self, prompt, max_new_tokens=100, temperature=0.0):
        out = prompt
        for _ in range(max_new_tokens):
            out += self.next_char(out, temperature)
        return out

    def evaluate(self, text):
        if not text: return {"loss": None, "perplexity": None}
        nll = 0.0
        for i, target in enumerate(text):
            counts = self.counts.get(text[max(0, i-self.order):i], Counter())
            total = sum(counts.values()) + self.alpha * len(self.vocab)
            p = (counts[target] + self.alpha) / total
            nll -= math.log(p)
        loss = nll / len(text)
        return {"loss": round(loss, 4), "perplexity": round(math.exp(loss), 4)}

def run_ngram(args):
    text = load_corpus(args.corpus)
    train, test = split_corpus(text, args.train_fraction)
    model = CharNGram(args.order); model.fit(train)
    metrics = {"backend": "stdlib_char_ngram", "seed": args.seed,
               "train_chars": len(train), "test_chars": len(test),
               **model.evaluate(test)}
    sample = model.generate(args.prompt, args.max_new_tokens, args.temperature)
    metrics["sample"] = sample
    return metrics

def run_torch(args):
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise SystemExit("PyTorch is not installed; use the default backend or install requirements.txt") from exc
    torch.manual_seed(args.seed)
    text = load_corpus(args.corpus); train, test = split_corpus(text, args.train_fraction)
    chars = sorted(set(text)); stoi = {c:i for i,c in enumerate(chars)}; itos = dict(enumerate(chars))
    def enc(s): return torch.tensor([stoi[c] for c in s], dtype=torch.long)
    tr, te = enc(train), enc(test)
    class TinyTransformer(nn.Module):
        def __init__(self):
            super().__init__(); d = args.d_model
            self.tok = nn.Embedding(len(chars), d); self.pos = nn.Embedding(args.block_size, d)
            layer = nn.TransformerEncoderLayer(d, args.n_heads, 4*d, dropout=0.0, batch_first=True)
            self.body = nn.TransformerEncoder(layer, args.n_layers); self.head = nn.Linear(d, len(chars))
        def forward(self, x, y=None):
            t = x.size(1); h = self.tok(x) + self.pos(torch.arange(t, device=x.device))
            mask = torch.triu(torch.ones(t,t,device=x.device), diagonal=1).bool()
            logits = self.head(self.body(h, mask=mask)); loss = None
            if y is not None: loss = nn.functional.cross_entropy(logits.reshape(-1, len(chars)), y.reshape(-1))
            return logits, loss
    model = TinyTransformer(); opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    model.train(); start = time.time()
    for step in range(args.steps):
        if len(tr) <= args.block_size: x = tr[:-1].unsqueeze(0); y = tr[1:].unsqueeze(0)
        else:
            ix = torch.randint(0, len(tr)-args.block_size-1, (args.batch_size,)); x = torch.stack([tr[i:i+args.block_size] for i in ix]); y = torch.stack([tr[i+1:i+args.block_size+1] for i in ix])
        _, loss = model(x, y); opt.zero_grad(); loss.backward(); opt.step()
    model.eval(); ids = enc(args.prompt)
    with torch.no_grad():
        for _ in range(args.max_new_tokens):
            x = ids[-args.block_size:].unsqueeze(0); logits,_ = model(x); ids = torch.cat([ids, logits[0,-1].argmax().view(1)])
    return {"backend":"torch_transformer", "seed":args.seed, "parameters":sum(p.numel() for p in model.parameters()), "steps":args.steps, "seconds":round(time.time()-start,2), "sample":"".join(itos[int(i)] for i in ids)}

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--backend", choices=["ngram","torch"], default="ngram"); p.add_argument("--corpus"); p.add_argument("--prompt", default="user: explain a transformer\nassistant:"); p.add_argument("--max-new-tokens", type=int, default=80); p.add_argument("--temperature", type=float, default=0); p.add_argument("--seed", type=int, default=SEED); p.add_argument("--train-fraction", type=float, default=.8); p.add_argument("--order", type=int, default=3); p.add_argument("--steps", type=int, default=120); p.add_argument("--batch-size", type=int, default=8); p.add_argument("--block-size", type=int, default=64); p.add_argument("--d-model", type=int, default=32); p.add_argument("--n-heads", type=int, default=4); p.add_argument("--n-layers", type=int, default=2); p.add_argument("--lr", type=float, default=3e-3); p.add_argument("--output", default="metrics.json"); args = p.parse_args(); seed_everything(args.seed)
    result = run_torch(args) if args.backend == "torch" else run_ngram(args)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8"); print(json.dumps(result, indent=2))

if __name__ == "__main__": main()
