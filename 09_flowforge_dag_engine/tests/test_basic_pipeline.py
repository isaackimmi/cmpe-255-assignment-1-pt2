import unittest

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
            [],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(RuntimeError, "data-quality validation failed"):
                Runner(self._pipeline_for(rows)).run(seed=255)


if __name__ == "__main__":
    unittest.main()
