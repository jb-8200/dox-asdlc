"""Unit tests for metrics query strings.

Tests verify that PromQL queries use correct metric names and labels.
These tests are part of P06-F09: VictoriaMetrics Metrics Query Fix.

Tests verify:
- CPU queries use asdlc_process_cpu_percent metric
- Memory queries use asdlc_process_memory_bytes with type=rss label
- All queries use service= label (not app=)
- SERVICE_POD_LABELS uses service= prefix
"""

from __future__ import annotations

import pytest


class TestMetricsApiQueryStrings:
    """Tests for query strings in metrics_api.py."""

    def test_cpu_query_uses_asdlc_metric_with_service(self) -> None:
        """CPU query with service filter should use asdlc_process_cpu_percent."""
        from src.orchestrator.routes.metrics_api import get_cpu_metrics

        # The function builds a query string - we test the logic by checking
        # the actual function exists and has correct query patterns
        import inspect
        source = inspect.getsource(get_cpu_metrics)

        # Should use asdlc_process_cpu_percent, not process_cpu_seconds_total
        assert "asdlc_process_cpu_percent" in source
        assert "process_cpu_seconds_total" not in source
        # Should not have rate() calculation since metric is already percentage
        assert "rate(asdlc_process_cpu_percent" not in source

    def test_cpu_query_uses_asdlc_metric_aggregate(self) -> None:
        """CPU query without service filter should use avg(asdlc_process_cpu_percent)."""
        from src.orchestrator.routes.metrics_api import get_cpu_metrics

        import inspect
        source = inspect.getsource(get_cpu_metrics)

        # Should use avg(asdlc_process_cpu_percent) for aggregate
        assert "avg(asdlc_process_cpu_percent)" in source

    def test_memory_query_uses_asdlc_metric_with_service(self) -> None:
        """Memory query with service filter should use asdlc_process_memory_bytes."""
        from src.orchestrator.routes.metrics_api import get_memory_metrics

        import inspect
        source = inspect.getsource(get_memory_metrics)

        # Should use asdlc_process_memory_bytes, not process_resident_memory_bytes
        assert "asdlc_process_memory_bytes" in source
        assert "process_resident_memory_bytes" not in source
        # Should include type="rss" label
        assert 'type="rss"' in source

    def test_memory_query_uses_asdlc_metric_aggregate(self) -> None:
        """Memory query without service filter should use sum(asdlc_process_memory_bytes)."""
        from src.orchestrator.routes.metrics_api import get_memory_metrics

        import inspect
        source = inspect.getsource(get_memory_metrics)

        # Should use sum with asdlc_process_memory_bytes for aggregate
        assert 'sum(asdlc_process_memory_bytes{type="rss"})' in source


class TestServiceHealthQueryStrings:
    """Tests for query strings in service_health.py."""

    def test_service_pod_labels_use_service_prefix(self) -> None:
        """SERVICE_POD_LABELS should use service= prefix, not app=."""
        from src.orchestrator.services.service_health import SERVICE_POD_LABELS

        for service_name, label in SERVICE_POD_LABELS.items():
            assert label.startswith('service="'), (
                f"SERVICE_POD_LABELS['{service_name}'] should use service= prefix, "
                f"got: {label}"
            )
            assert 'app="' not in label, (
                f"SERVICE_POD_LABELS['{service_name}'] should not use app= prefix, "
                f"got: {label}"
            )

    def test_fetch_service_health_cpu_query(self) -> None:
        """_fetch_service_health should use asdlc_process_cpu_percent for CPU."""
        from src.orchestrator.services.service_health import ServiceHealthService

        import inspect
        source = inspect.getsource(ServiceHealthService._fetch_service_health)

        # Should use asdlc_process_cpu_percent, not process_cpu_seconds_total
        assert "asdlc_process_cpu_percent" in source
        assert "process_cpu_seconds_total" not in source

    def test_fetch_service_health_memory_query(self) -> None:
        """_fetch_service_health should use asdlc_process_memory_bytes for memory."""
        from src.orchestrator.services.service_health import ServiceHealthService

        import inspect
        source = inspect.getsource(ServiceHealthService._fetch_service_health)

        # Should use asdlc_process_memory_bytes, not process_resident_memory_bytes
        assert "asdlc_process_memory_bytes" in source
        assert "process_resident_memory_bytes" not in source
        # Should include type="rss"
        assert 'type="rss"' in source

    def test_sparkline_query_map_cpu(self) -> None:
        """get_service_sparkline query_map should use asdlc_process_cpu_percent for cpu."""
        from src.orchestrator.services.service_health import ServiceHealthService

        import inspect
        source = inspect.getsource(ServiceHealthService.get_service_sparkline)

        # Check the query_map definition for CPU
        # Should use asdlc_process_cpu_percent
        assert "asdlc_process_cpu_percent" in source
        # Should NOT use process_cpu_seconds_total
        assert "process_cpu_seconds_total" not in source

    def test_sparkline_query_map_memory(self) -> None:
        """get_service_sparkline query_map should use asdlc_process_memory_bytes for memory."""
        from src.orchestrator.services.service_health import ServiceHealthService

        import inspect
        source = inspect.getsource(ServiceHealthService.get_service_sparkline)

        # Check the query_map definition for memory
        # Should use asdlc_process_memory_bytes
        assert "asdlc_process_memory_bytes" in source
        # Should NOT use process_resident_memory_bytes
        assert "process_resident_memory_bytes" not in source
        # Should include type="rss"
        assert 'type="rss"' in source


class TestQueryLabelConsistency:
    """Tests for consistent label usage across all queries."""

    def test_all_service_pod_labels_are_valid_services(self) -> None:
        """All keys in SERVICE_POD_LABELS should be valid services."""
        from src.orchestrator.services.service_health import (
            SERVICE_POD_LABELS,
            VALID_SERVICES,
        )

        for service_name in SERVICE_POD_LABELS.keys():
            assert service_name in VALID_SERVICES, (
                f"SERVICE_POD_LABELS contains unknown service: {service_name}"
            )

    def test_all_valid_services_have_pod_labels(self) -> None:
        """All valid services should have an entry in SERVICE_POD_LABELS."""
        from src.orchestrator.services.service_health import (
            SERVICE_POD_LABELS,
            VALID_SERVICES,
        )

        for service_name in VALID_SERVICES:
            assert service_name in SERVICE_POD_LABELS, (
                f"VALID_SERVICES contains {service_name} but it's missing from "
                "SERVICE_POD_LABELS"
            )
