import unittest
import math
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import examples.basic_pipeline as basic_pipeline
from examples.basic_pipeline import clean_data, validate_data
from flowforge import DAG, Runner, Task


class BasicPipelineQualityTests(unittest.TestCase):
    def _pipeline_for(self, rows):
        dag = DAG()
        dag.add_task(Task("load_data", lambda ctx: rows))
        dag.add_task(Task("validate_data", validate_data, ["load_data"]))
        dag.add_task(Task("clean_data", clean_data, ["validate_data"]))
        return dag

    def test_quality_gate_preserves_zero_and_imputation_is_explicit(self):
        rows = [{"age": 0, "score": 80}, {"age": None, "score": 90}]
        context = Runner(self._pipeline_for(rows)).run(seed=255)
        self.assertEqual(context.output("clean_data"), [{"age": 0, "score": 80}, {"age": 0, "score": 90}])

    def test_quality_gate_rejects_malformed_rows(self):
        cases = [
            [{"age": 22, "score": "high"}],
            [{"age": -1, "score": 80}],
            [{"age": 22}],
            [{"age": True, "score": 80}],
            [{"age": math.nan, "score": 80}],
            [{"age": math.inf, "score": 80}],
            [{"age": 22, "score": 80, "segment": "extra"}],
            [],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(RuntimeError, "data-quality validation failed"):
                Runner(self._pipeline_for(rows)).run(seed=255)

    def test_example_manifest_export_round_trips_runner_state(self):
        context = Runner(self._pipeline_for([{"age": 22, "score": 80}])).run(seed=255)
        with TemporaryDirectory() as directory:
            previous = basic_pipeline.ARTIFACT_DIR
            basic_pipeline.ARTIFACT_DIR = Path(directory)
            try:
                path = basic_pipeline.write_manifest(context, "test_manifest.json")
            finally:
                basic_pipeline.ARTIFACT_DIR = previous
            exported = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(exported["status"], "succeeded")
        self.assertEqual(exported["task_order"], ["load_data", "validate_data", "clean_data"])
        self.assertEqual(exported["tasks"]["clean_data"]["output"]["producer"], "clean_data")


if __name__ == "__main__":
    unittest.main()
