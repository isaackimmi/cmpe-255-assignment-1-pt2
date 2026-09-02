import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from nano_llm import (
    CORPUS,
    UNK_TOKEN,
    CharNGram,
    build_tiny_transformer,
    make_causal_mask,
    run_torch,
    split_corpus,
    split_train_validation_test,
)

PROJECT_DIR = Path(__file__).resolve().parent


class NanoTests(unittest.TestCase):
    def test_split_preserves_order_and_content(self):
        train, test = split_corpus(CORPUS, .8)
        self.assertEqual(train + test, CORPUS)
        self.assertGreater(len(train), len(test))

    def test_three_way_split_is_nonempty_and_ordered(self):
        train, validation, test = split_train_validation_test(CORPUS, .8, .1)
        self.assertEqual(train + validation + test, CORPUS)
        self.assertTrue(train and validation and test)
        self.assertEqual(len(train), 288)
        self.assertEqual(len(validation), 36)
        self.assertEqual(len(test), 36)

    def test_invalid_split_fails_fast(self):
        for fraction in (0, 1, 1.5, -0.1):
            with self.subTest(fraction=fraction):
                with self.assertRaises(ValueError):
                    split_corpus(CORPUS, fraction)
        with self.assertRaises(ValueError):
            split_train_validation_test(CORPUS, .9, .1)

    def test_ngram_learns_known_prefix(self):
        model = CharNGram(order=2)
        model.fit("abcabc")
        self.assertEqual(model.next_char("ab"), "c")
        self.assertGreater(model.evaluate("abc")["perplexity"], 0)

    def test_ngram_uses_explicit_oov_and_normalized_probability_mass(self):
        model = CharNGram(order=1, alpha=.2)
        model.fit("aaaa")
        result = model.evaluate("z", context="a")
        self.assertIn(UNK_TOKEN, model.vocab)
        self.assertEqual(result["oov_count"], 1)
        self.assertEqual(result["oov_rate"], 1.0)
        probabilities = [
            (model.counts[tuple("a")][token] + model.alpha)
            / (sum(model.counts[tuple("a")].values()) + model.alpha * len(model.vocab))
            for token in model.vocab
        ]
        self.assertAlmostEqual(sum(probabilities), 1.0)

    def test_ngram_evaluation_carries_boundary_context(self):
        model = CharNGram(order=1, alpha=.2)
        model.fit("ab")
        without_context = model.evaluate("b")
        with_context = model.evaluate("b", context="a")
        self.assertNotEqual(without_context["loss"], with_context["loss"])

    def test_ngram_replay_serializes_normalized_probabilities_and_trace(self):
        model = CharNGram(order=2, alpha=.2)
        model.fit("ababca")
        distribution = model.next_distribution("ab")
        self.assertAlmostEqual(sum(item["probability"] for item in distribution), 1.0, places=6)
        replay = model.replay("ab", max_new_tokens=3)
        self.assertTrue(replay["deterministic"])
        self.assertEqual(len(replay["trace"]), 3)
        self.assertEqual(replay["trace"][0]["selected"], replay["trace"][0]["candidates"][0]["token"])

    def test_cli_artifact_contains_three_way_split_and_behavior_inspector(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "metrics.json"
            subprocess.run(
                [sys.executable, "nano_llm.py", "--output", str(output), "--max-new-tokens", "3"],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            data = json.loads(output.read_text())
            self.assertEqual(data["split"]["train_chars"] + data["split"]["validation_chars"] + data["split"]["test_chars"], 360)
            self.assertEqual(data["oov_counts"]["validation"], data["validation"]["oov_count"])
            self.assertEqual(data["behavior"]["kind"], "deterministic_replay")
            self.assertIn("default_distribution", data["behavior"])
            self.assertIn("trace", data["behavior"])

    def test_cli_writes_auditable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "metrics.json"
            subprocess.run(
                [sys.executable, "nano_llm.py", "--output", str(output), "--max-new-tokens", "5"],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            data = json.loads(output.read_text())
            self.assertEqual(data["backend"], "stdlib_char_ngram")
            self.assertIn("sample", data)
            self.assertEqual(data["vocabulary_policy"], "fit_on_train_only_with_explicit_<UNK>")
            self.assertEqual(data["test"]["target_chars"], data["test_chars"])
            self.assertIn("corpus_sha256", data)
            self.assertIn("config", data)
            self.assertTrue(math.isfinite(data["test"]["perplexity"]))

    def test_cli_rejects_invalid_fraction(self):
        completed = subprocess.run(
            [sys.executable, "nano_llm.py", "--train-fraction", "1"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("strictly between 0 and 1", completed.stderr)

    def test_causal_mask_blocks_only_future_positions(self):
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch is optional and is not installed")
        mask = make_causal_mask(4, torch.device("cpu"), torch)
        expected = torch.tensor(
            [[False, True, True, True], [False, False, True, True],
             [False, False, False, True], [False, False, False, False]]
        )
        self.assertTrue(torch.equal(mask, expected))

    def test_torch_future_tokens_do_not_change_earlier_logits(self):
        try:
            import torch
            import torch.nn as nn
        except ImportError:
            self.skipTest("PyTorch is optional and is not installed")
        torch.manual_seed(255)
        model = build_tiny_transformer(8, 8, 2, 1, 8, torch, nn).eval()
        original = torch.tensor([[1, 2, 3, 4]])
        altered_future = torch.tensor([[1, 2, 7, 6]])
        with torch.no_grad():
            original_logits, _ = model(original)
            altered_logits, _ = model(altered_future)
        self.assertTrue(torch.allclose(original_logits[:, :2], altered_logits[:, :2]))

    def test_torch_run_reports_finite_validation_and_test_metrics(self):
        try:
            import torch  # noqa: F401
        except ImportError:
            self.skipTest("PyTorch is optional and is not installed")
        args = SimpleNamespace(
            seed=255, corpus=None, train_fraction=.8, validation_fraction=.1,
            order=3, alpha=.2, prompt="user:", max_new_tokens=0,
            temperature=0.0, d_model=8, n_heads=2, n_layers=1,
            block_size=16, batch_size=2, steps=2, eval_interval=1,
            lr=3e-3, device="cpu",
        )
        result = run_torch(args)
        self.assertEqual(result["vocabulary_policy"], "fit_on_train_only_with_explicit_<UNK>")
        self.assertIn(UNK_TOKEN, result["vocabulary"])
        self.assertTrue(math.isfinite(result["validation"]["perplexity"]))
        self.assertTrue(math.isfinite(result["test"]["perplexity"]))
        self.assertEqual(result["test_evaluations"], 1)


if __name__ == "__main__":
    unittest.main()
