import random
import unittest
from datetime import datetime, timezone

from flowforge import DAG, DependencyError, PipelineContext, Runner, Task
from flowforge.core import DAGError


class FlowForgeTests(unittest.TestCase):
    def test_runs_in_dependency_order_and_exposes_outputs(self):
        dag = DAG()
        dag.add_task(Task("source", lambda ctx: 4))
        dag.add_task(Task("double", lambda ctx: ctx.output("source") * 2, ["source"]))
        dag.add_task(Task("plus_one", lambda ctx: ctx.output("double") + 1, ["double"]))
        context = Runner(dag).run()
        self.assertEqual(context.execution_order, ["source", "double", "plus_one"])
        self.assertEqual(context.output("plus_one"), 9)

    def test_independent_tasks_have_stable_insertion_order(self):
        dag = DAG()
        dag.add_task(Task("a", lambda ctx: "a"))
        dag.add_task(Task("b", lambda ctx: "b"))
        self.assertEqual(dag.topological_order(), ["a", "b"])

    def test_unknown_dependency_is_rejected(self):
        dag = DAG()
        dag.add_task(Task("consumer", lambda ctx: None, ["missing"]))
        with self.assertRaisesRegex(DAGError, "unknown dependencies"):
            dag.validate()

    def test_cycle_is_rejected(self):
        dag = DAG()
        dag.add_task(Task("a", lambda ctx: None, ["b"]))
        dag.add_task(Task("b", lambda ctx: None, ["a"]))
        with self.assertRaisesRegex(DAGError, "cycle detected"):
            dag.validate()

    def test_cycle_diagnostic_excludes_blocked_descendants(self):
        dag = DAG()
        dag.add_task(Task("a", lambda ctx: None, ["b"]))
        dag.add_task(Task("b", lambda ctx: None, ["a"]))
        dag.add_task(Task("c", lambda ctx: None, ["a"]))
        with self.assertRaises(DAGError) as raised:
            dag.validate()
        self.assertIn("involving: ['a', 'b']", str(raised.exception))
        self.assertIn("blocked descendants: ['c']", str(raised.exception))

    def test_task_failure_identifies_task(self):
        dag = DAG()
        dag.add_task(Task("bad_step", lambda ctx: 1 / 0))
        with self.assertRaisesRegex(RuntimeError, "bad_step"):
            Runner(dag).run()

    def test_context_can_be_supplied(self):
        dag = DAG()
        dag.add_task(Task("read_config", lambda ctx: ctx.metadata["value"]))
        context = PipelineContext(metadata={"value": 7})
        self.assertEqual(Runner(dag).run(context).output("read_config"), 7)

    def test_failed_reused_context_clears_stale_outputs_and_history(self):
        dag = DAG()
        dag.add_task(Task("bad_step", lambda ctx: 1 / 0))
        context = PipelineContext(outputs={"bad_step": "stale-from-prior-run"}, execution_order=["bad_step"])
        with self.assertRaisesRegex(RuntimeError, "bad_step"):
            Runner(dag).run(context)
        self.assertEqual(dict(context.outputs), {})
        self.assertEqual(context.execution_order, [])
        self.assertEqual(context.status, "failed")
        with self.assertRaises(KeyError):
            context.output("bad_step")
        self.assertEqual(context.manifest["tasks"]["bad_step"]["status"], "failed")

    def test_undeclared_reads_fail_regardless_of_insertion_order(self):
        for source_first in (True, False):
            dag = DAG()
            if source_first:
                dag.add_task(Task("source", lambda ctx: 4))
                dag.add_task(Task("consumer", lambda ctx: ctx.output("source")))
            else:
                dag.add_task(Task("consumer", lambda ctx: ctx.output("source")))
                dag.add_task(Task("source", lambda ctx: 4))
            with self.subTest(source_first=source_first), self.assertRaisesRegex(RuntimeError, "undeclared input"):
                Runner(dag).run()

    def test_artifacts_capture_lineage_and_protect_payload_from_mutation(self):
        dag = DAG()
        dag.add_task(Task("source", lambda ctx: {"items": [1]}))

        def mutate(ctx):
            value = ctx.output("source")
            value["items"].append(2)
            return value

        dag.add_task(Task("mutate", mutate, ["source"]))
        context = Runner(dag).run(seed=3)
        self.assertEqual(context.output("source"), {"items": [1]})
        self.assertEqual(context.output("mutate"), {"items": [1, 2]})
        source_artifact = context.artifact("source")
        mutate_artifact = context.artifact("mutate")
        self.assertEqual(source_artifact.producer, "source")
        self.assertEqual(source_artifact.run_id, context.run_id)
        self.assertEqual(mutate_artifact.parent_artifact_ids, (source_artifact.artifact_id,))
        with self.assertRaises(TypeError):
            context.outputs["new"] = 1

    def test_seed_and_clock_are_recorded_and_reproduce_random_task(self):
        dag = DAG()
        dag.add_task(Task("random_value", lambda ctx: random.random(), config={"model": "demo"}))
        fixed_clock = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
        first = Runner(dag).run(seed=19, config={"dataset": "tiny"}, clock=fixed_clock)
        second = Runner(dag).run(seed=19, config={"dataset": "tiny"}, clock=fixed_clock)
        self.assertEqual(first.output("random_value"), second.output("random_value"))
        self.assertEqual(first.manifest["seed"], 19)
        self.assertEqual(first.manifest["started_at"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(first.manifest["tasks"]["random_value"]["status"], "succeeded")
        self.assertEqual(first.manifest["tasks"]["random_value"]["config_fingerprint"], second.manifest["tasks"]["random_value"]["config_fingerprint"])
        self.assertNotEqual(first.run_id, second.run_id)

    def test_dependency_input_validation_rejects_malformed_collections(self):
        with self.assertRaisesRegex(DAGError, "not a string"):
            Task("consumer", lambda ctx: None, "source")
        with self.assertRaisesRegex(DAGError, "non-empty string"):
            Task("consumer", lambda ctx: None, ["source", 3])
        with self.assertRaisesRegex(DAGError, "duplicate dependencies"):
            Task("consumer", lambda ctx: None, ["source", "source"])


if __name__ == "__main__":
    unittest.main()
