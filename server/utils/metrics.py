"""Prometheus metrics for episode, step, grader, and error tracking."""

from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

    episodes_total = Counter(
        "openenv_episodes_total",
        "Total episodes started/completed",
        ["domain", "task_id", "status"],
    )

    steps_total = Counter(
        "openenv_steps_total",
        "Total steps taken",
        ["domain", "tool_name"],
    )

    grader_scores = Histogram(
        "openenv_grader_scores",
        "Distribution of grader scores per episode",
        ["domain", "task_id", "difficulty"],
        buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    )

    episode_duration = Histogram(
        "openenv_episode_duration_seconds",
        "Episode wall-clock duration in seconds",
        ["domain"],
        buckets=[1, 5, 10, 30, 60, 120, 300],
    )

    tool_errors_total = Counter(
        "openenv_tool_errors_total",
        "Total tool invocation errors",
        ["domain", "tool_name", "error_type"],
    )

    def get_metrics_response() -> tuple[bytes, str]:
        return generate_latest(), CONTENT_TYPE_LATEST

except ImportError:
    # prometheus_client not installed — provide no-op stubs
    class _NoOpMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, amount=1): pass
        def observe(self, value): pass

    episodes_total = _NoOpMetric()
    steps_total = _NoOpMetric()
    grader_scores = _NoOpMetric()
    episode_duration = _NoOpMetric()
    tool_errors_total = _NoOpMetric()

    def get_metrics_response() -> tuple[bytes, str]:
        return b"# prometheus_client not installed\n", "text/plain"
