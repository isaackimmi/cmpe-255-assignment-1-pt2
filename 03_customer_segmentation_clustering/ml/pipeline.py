"""ML adapter used by the API; the canonical experiment remains src/experiment.py."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.experiment import FEATURES, SEED, make_dataset, fit_segmenter, run  # noqa: E402

def score_observation(values: dict[str, float]) -> dict:
    frame = pd.DataFrame([values], columns=FEATURES)
    summary = run(ROOT / "artifacts") if not (ROOT / "artifacts/manifest.json").exists() else __import__("json").loads((ROOT / "artifacts/summary.json").read_text())
    fitted = fit_segmenter(make_dataset(seed=SEED), summary["selected_preprocessing"], int(summary["selected_k"]))
    cluster = int(fitted["model"].predict(fitted["scaler"].transform(frame[FEATURES]))[0])
    return {"cluster": cluster, "preprocessing": summary["selected_preprocessing"], "k": int(summary["selected_k"]), "note": "Geometry assignment from the reproducible fitted model; not a behavioral probability."}
