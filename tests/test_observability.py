import unittest

from backend.app.observability import Metrics, TTLCache, should_track_request


class MetricsTests(unittest.TestCase):
    def test_records_request_and_error(self):
        metrics = Metrics()
        metrics.record("GET", 200, 0.025, "/health/db")
        metrics.record("POST", 500, 0.250, "/events")

        snapshot = metrics.snapshot()

        self.assertEqual(snapshot["requests_total"], 2)
        self.assertEqual(snapshot["errors_total"], 1)
        self.assertEqual(snapshot["requests_by_method"]["GET"], 1)
        self.assertEqual(snapshot["requests_by_status"]["500"], 1)
        self.assertEqual(snapshot["requests_by_path"][0]["path"], "/events")
        self.assertEqual(snapshot["requests_last_5m"], 2)
        self.assertEqual(snapshot["latency_buckets"][-1]["count"], 2)

    def test_empty_metrics_have_safe_defaults(self):
        snapshot = Metrics().snapshot()

        self.assertEqual(snapshot["requests_total"], 0)
        self.assertEqual(snapshot["errors_total"], 0)
        self.assertEqual(snapshot["average_latency_ms"], 0)
        self.assertIsNone(snapshot["p95_latency_ms"])

    def test_cache_excludes_internal_and_static_routes(self):
        self.assertFalse(should_track_request("/health"))
        self.assertFalse(should_track_request("/metrics"))
        self.assertFalse(should_track_request("/static/js/app.js"))
        self.assertTrue(should_track_request("/events"))

    def test_ttl_cache_clear(self):
        cache = TTLCache(ttl_seconds=10)
        cache.set("summary", {"events": 2})
        self.assertEqual(cache.get("summary"), {"events": 2})
        cache.clear()
        self.assertIsNone(cache.get("summary"))


if __name__ == "__main__":
    unittest.main()
