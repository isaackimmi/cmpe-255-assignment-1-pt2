import unittest

from flowforge import DAG, PipelineContext, Runner, Task
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


if __name__ == "__main__":
    unittest.main()
