import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from nano_llm import CharNGram, CORPUS, split_corpus

class NanoTests(unittest.TestCase):
  def test_split_preserves_order_and_content(self):
    a,b = split_corpus(CORPUS, .8)
    self.assertEqual(a + b, CORPUS); self.assertGreater(len(a), len(b))

  def test_ngram_learns_known_prefix(self):
    m = CharNGram(order=2); m.fit("abcabc")
    self.assertEqual(m.next_char("ab"), "c")
    self.assertGreater(m.evaluate("abc")["perplexity"], 0)

  def test_cli_writes_json(self):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "metrics.json"
        subprocess.run([sys.executable, "nano_llm.py", "--output", str(out), "--max-new-tokens", "5"], check=True, capture_output=True, text=True)
        data = json.loads(out.read_text())
        self.assertEqual(data["backend"], "stdlib_char_ngram"); self.assertIn("sample", data)

if __name__ == "__main__": unittest.main()
