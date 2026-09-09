import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sync_pipeline import (
    SyncStep,
    SyncStepError,
    generation_step,
    github_repository_database_step,
    github_repository_generation_step,
    repository_sync_steps,
    run_sync_steps,
)


class SyncPipelineTests(unittest.TestCase):
    def test_runner_executes_steps_in_order_and_emits_callbacks(self):
        executed = []
        started = []
        completed = []
        steps = [
            SyncStep(1, "one", "One", lambda: executed.append("one")),
            SyncStep(2, "two", "Two", lambda: executed.append("two")),
        ]

        results = run_sync_steps(
            steps,
            on_step_start=lambda step: started.append(step.key),
            on_step_complete=lambda result: completed.append(result.key),
        )

        self.assertEqual(["one", "two"], executed)
        self.assertEqual(["one", "two"], started)
        self.assertEqual(["one", "two"], completed)
        self.assertEqual(["one", "two"], [result.key for result in results])

    def test_runner_stops_after_failure(self):
        executed = []

        def fail():
            raise RuntimeError("boom")

        steps = [
            SyncStep(1, "one", "One", lambda: executed.append("one")),
            SyncStep(2, "two", "Two", fail),
            SyncStep(3, "three", "Three", lambda: executed.append("three")),
        ]

        with self.assertRaises(SyncStepError) as raised:
            run_sync_steps(steps)

        self.assertEqual(2, raised.exception.step.number)
        self.assertEqual(["one"], executed)

    @patch("sync_pipeline.subprocess.run")
    def test_repository_commands_are_defined_once(self, run):
        run.return_value = SimpleNamespace(returncode=0)
        run_sync_steps(repository_sync_steps(python_executable="python"))
        commands = [call.args[0] for call in run.call_args_list]

        self.assertEqual(["python", "download_repo.py"], commands[0])
        self.assertEqual(
            ["python", "local_change_dashboard/check_changes.py"], commands[1]
        )
        self.assertIn("--download-changed", commands[2])

    @patch("sync_pipeline.subprocess.run")
    def test_generation_step_resolves_mixed_docs_lazily(self, run):
        run.return_value = SimpleNamespace(returncode=0)
        state = {"mixed_docs": "fresh/path"}
        step = generation_step(
            mixed_docs=lambda: state["mixed_docs"],
            output_dir="formatted",
            summarize=False,
            python_executable="python",
        )
        run_sync_steps([step])
        command = run.call_args.args[0]
        self.assertEqual(
            [
                "python",
                "dashboard/generate_formatted_files.py",
                "--mixed-docs",
                "fresh/path",
                "--output",
                "formatted",
            ],
            command,
        )

    @patch("sync_pipeline.subprocess.run")
    def test_github_repository_step_is_explicitly_guarded(self, run):
        run.return_value = SimpleNamespace(returncode=0)
        step = github_repository_generation_step(
            python_executable="python", summarize=True
        )
        run_sync_steps([step])
        self.assertEqual(
            ["python", "run_github_repository_sync.py", "--execute"],
            run.call_args.args[0],
        )

    @patch("sync_pipeline.subprocess.run")
    def test_github_repository_database_step_is_scoped_and_incremental(self, run):
        run.return_value = SimpleNamespace(returncode=0)
        step = github_repository_database_step(
            8, root="system", python_executable="python"
        )
        run_sync_steps([step])
        command = run.call_args.args[0]
        self.assertIn("--expected-artifact-type", command)
        self.assertIn("--reconcile-snapshot-artifact-type", command)
        self.assertIn("--ensure-repository-chunk-types", command)
        self.assertIn("--require-summaries", command)
        self.assertIn("github_repository_db_update_result.json", command)


if __name__ == "__main__":
    unittest.main()
