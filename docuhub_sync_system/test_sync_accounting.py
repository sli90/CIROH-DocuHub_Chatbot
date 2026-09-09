import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sync_accounting import (
    UsageAccumulator,
    aggregate_usage,
    build_synchronization_report,
)


class SyncAccountingTests(unittest.TestCase):
    def test_responses_usage_tracks_cached_and_reasoning_tokens(self):
        response = SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=1000,
                input_tokens_details=SimpleNamespace(
                    cached_tokens=200, cache_write_tokens=0
                ),
                output_tokens=100,
                output_tokens_details=SimpleNamespace(reasoning_tokens=40),
                total_tokens=1100,
            )
        )
        tracker = UsageAccumulator("summarization", "gpt-5.2")
        tracker.record_request()
        tracker.add_response(response)
        report = tracker.report()

        self.assertEqual(800, report["uncached_input_tokens"])
        self.assertEqual(200, report["cached_input_tokens"])
        self.assertEqual(40, report["reasoning_tokens"])
        self.assertAlmostEqual(0.002835, report["estimated_cost_usd"])

    def test_embedding_usage_and_environment_price_override(self):
        response = SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=2000, total_tokens=2000)
        )
        with patch.dict(
            os.environ,
            {"OPENAI_EMBEDDING_INPUT_USD_PER_1M": "0.20"},
            clear=False,
        ):
            tracker = UsageAccumulator("embeddings", "text-embedding-3-large")
            tracker.record_request()
            tracker.add_response(response)
            report = tracker.report()

        self.assertEqual(2000, report["input_tokens"])
        self.assertEqual(0, report["output_tokens"])
        self.assertAlmostEqual(0.0004, report["estimated_cost_usd"])

    def test_aggregate_usage_combines_operation_costs(self):
        summary = UsageAccumulator("summarization", "gpt-5.2").report()
        embedding = UsageAccumulator(
            "embeddings", "text-embedding-3-large"
        ).report()
        combined = aggregate_usage([summary, embedding])
        self.assertEqual(0, combined["total_tokens"])
        self.assertEqual(0, combined["estimated_cost_usd"])
        self.assertEqual(2, len(combined["operations"]))
        flattened = aggregate_usage([combined])
        self.assertEqual(2, len(flattened["operations"]))
        self.assertEqual(0, flattened["total_tokens"])

    def test_synchronization_report_includes_additional_stage_usage(self):
        repository_usage = UsageAccumulator(
            "github_repository_summarization", "gpt-5.2"
        )
        repository_usage.record_request()
        repository_usage.add_response(
            SimpleNamespace(
                usage=SimpleNamespace(
                    input_tokens=100,
                    output_tokens=10,
                    total_tokens=110,
                )
            )
        )
        report = build_synchronization_report(
            sync_id="test",
            mode="test",
            started_at="2026-09-01T00:00:00+00:00",
            completed_at="2026-09-01T00:00:01+00:00",
            status="completed",
            additional_usage_reports=[repository_usage.report()],
        )
        self.assertEqual(110, report["openai_usage"]["total_tokens"])
        self.assertEqual(
            "github_repository_summarization",
            report["openai_usage"]["operations"][0]["operation"],
        )


if __name__ == "__main__":
    unittest.main()
