# P06-F09: VictoriaMetrics Metrics Query Fix - User Stories

**Version:** 1.0
**Date:** January 27, 2026
**Status:** Draft

## Epic Summary

As a platform operator, I want the metrics dashboard to display real data from VictoriaMetrics so that I can monitor actual service performance instead of mock data.

Currently, the metrics dashboard shows "No data" when switched to VictoriaMetrics mode because:
1. CPU metrics are not exported by services
2. Queries use wrong metric names (standard Prometheus vs asdlc_ prefix)
3. Queries use wrong label selectors (app= vs service=)

This epic fixes the metric export and query alignment to enable real monitoring.

---

## User Story 1: CPU Metrics Export

**As a** platform operator
**I want** services to export CPU usage metrics
**So that** I can monitor CPU utilization across the cluster

### Description

The `ProcessMetricsCollector` currently only exports memory metrics. Add CPU percentage metric so the dashboard can display real CPU data.

### Acceptance Criteria

1. **AC1.1:** Services export `asdlc_process_cpu_percent{service="<name>"}` on /metrics endpoint
2. **AC1.2:** CPU value is a percentage between 0 and 100
3. **AC1.3:** Metric is present when psutil is available
4. **AC1.4:** Graceful degradation when psutil is unavailable (metric omitted, no error)

### Acceptance Tests

```python
def test_process_metrics_collector_exports_cpu():
    """Verify CPU metric is exported."""
    collector = ProcessMetricsCollector("test-service")
    metrics = list(collector.collect())

    cpu_metric = next((m for m in metrics if m.name == "asdlc_process_cpu_percent"), None)
    assert cpu_metric is not None
    assert len(cpu_metric.samples) == 1
    assert cpu_metric.samples[0].labels == {"service": "test-service"}
    assert 0 <= cpu_metric.samples[0].value <= 100

def test_process_metrics_collector_cpu_label():
    """Verify CPU metric has correct service label."""
    collector = ProcessMetricsCollector("orchestrator")
    metrics = list(collector.collect())

    cpu_metric = next((m for m in metrics if m.name == "asdlc_process_cpu_percent"), None)
    assert cpu_metric.samples[0].labels["service"] == "orchestrator"
```

---

## User Story 2: CPU Query Alignment

**As a** platform operator
**I want** CPU queries to use the correct metric name
**So that** the dashboard displays actual CPU data

### Description

Update PromQL queries from `process_cpu_seconds_total` to `asdlc_process_cpu_percent` to match what services export.

### Acceptance Criteria

1. **AC2.1:** `/api/metrics/cpu` queries `asdlc_process_cpu_percent` instead of `process_cpu_seconds_total`
2. **AC2.2:** Service health sparkline CPU queries use `asdlc_process_cpu_percent`
3. **AC2.3:** Queries return data when services are running and scraped
4. **AC2.4:** No rate() needed since metric is already a percentage

### Acceptance Tests

```python
def test_cpu_endpoint_query_uses_correct_metric():
    """Verify CPU endpoint uses asdlc_process_cpu_percent."""
    # Mock VictoriaMetrics response
    mock_response = {
        "data": {
            "result": [{
                "values": [[1706000000, "45.5"]]
            }]
        }
    }

    with patch_victoriametrics(mock_response) as mock:
        response = client.get("/api/metrics/cpu?service=orchestrator")

        # Verify correct metric name in query
        query = mock.last_query
        assert "asdlc_process_cpu_percent" in query
        assert "process_cpu_seconds_total" not in query

def test_cpu_endpoint_returns_data():
    """Verify CPU endpoint returns non-empty data."""
    response = client.get("/api/metrics/cpu")
    assert response.status_code == 200
    data = response.json()
    assert len(data["dataPoints"]) > 0
```

---

## User Story 3: Memory Query Alignment

**As a** platform operator
**I want** memory queries to use the correct metric name and labels
**So that** the dashboard displays actual memory data

### Description

Update PromQL queries from `process_resident_memory_bytes` to `asdlc_process_memory_bytes{type="rss"}` to match what services export.

### Acceptance Criteria

1. **AC3.1:** `/api/metrics/memory` queries `asdlc_process_memory_bytes{type="rss"}`
2. **AC3.2:** Service health sparkline memory queries use correct metric name
3. **AC3.3:** Queries include `type="rss"` label filter
4. **AC3.4:** Queries return data when services are running and scraped

### Acceptance Tests

```python
def test_memory_endpoint_query_uses_correct_metric():
    """Verify memory endpoint uses asdlc_process_memory_bytes."""
    mock_response = {
        "data": {
            "result": [{
                "values": [[1706000000, "134217728"]]  # 128MB
            }]
        }
    }

    with patch_victoriametrics(mock_response) as mock:
        response = client.get("/api/metrics/memory?service=orchestrator")

        query = mock.last_query
        assert "asdlc_process_memory_bytes" in query
        assert 'type="rss"' in query
        assert "process_resident_memory_bytes" not in query

def test_memory_endpoint_returns_data():
    """Verify memory endpoint returns non-empty data."""
    response = client.get("/api/metrics/memory")
    assert response.status_code == 200
    data = response.json()
    assert len(data["dataPoints"]) > 0
```

---

## User Story 4: Label Selector Correction

**As a** platform operator
**I want** queries to use the correct label selector
**So that** metrics can be filtered by service name

### Description

Update all PromQL queries from `app="service_name"` to `service="service_name"` to match the labels applied in `scrape.yml`.

### Acceptance Criteria

1. **AC4.1:** All queries use `service=` label instead of `app=`
2. **AC4.2:** `SERVICE_POD_LABELS` dict updated to use `service=` prefix
3. **AC4.3:** Service filter parameter works correctly
4. **AC4.4:** Queries match scraped data labels

### Acceptance Tests

```python
def test_service_pod_labels_use_service_label():
    """Verify SERVICE_POD_LABELS uses service= not app=."""
    from src.orchestrator.services.service_health import SERVICE_POD_LABELS

    for service, label in SERVICE_POD_LABELS.items():
        assert label.startswith('service='), f"{service} uses wrong label prefix"
        assert 'app=' not in label, f"{service} should not use app="

def test_cpu_query_with_service_filter():
    """Verify service filter uses correct label."""
    with patch_victoriametrics({}) as mock:
        client.get("/api/metrics/cpu?service=workers")

        query = mock.last_query
        assert 'service="workers"' in query
        assert 'app="workers"' not in query
```

---

## User Story 5: End-to-End Dashboard Verification

**As a** platform operator
**I want** the metrics dashboard to display real data in VictoriaMetrics mode
**So that** I can use the dashboard for actual monitoring

### Description

After all query fixes are applied, verify the complete data flow from service metrics export through VictoriaMetrics to dashboard display.

### Acceptance Criteria

1. **AC5.1:** CPU chart shows non-zero values in VictoriaMetrics mode
2. **AC5.2:** Memory chart shows non-zero values in VictoriaMetrics mode
3. **AC5.3:** Service health shows HEALTHY status with real metrics
4. **AC5.4:** Sparkline charts render with real data points

### Acceptance Tests

```python
@pytest.mark.integration
def test_end_to_end_cpu_metrics():
    """Verify CPU metrics flow from export to query."""
    # 1. Verify service exports CPU metric
    metrics_response = requests.get("http://localhost:8080/metrics")
    assert "asdlc_process_cpu_percent" in metrics_response.text

    # 2. Wait for scrape interval
    time.sleep(20)

    # 3. Query VictoriaMetrics directly
    vm_response = requests.get(
        "http://localhost:8428/api/v1/query",
        params={"query": 'asdlc_process_cpu_percent{service="orchestrator"}'}
    )
    result = vm_response.json()
    assert len(result["data"]["result"]) > 0

    # 4. Query through API
    api_response = requests.get("http://localhost:8080/api/metrics/cpu?service=orchestrator")
    data = api_response.json()
    assert len(data["dataPoints"]) > 0

@pytest.mark.integration
def test_end_to_end_memory_metrics():
    """Verify memory metrics flow from export to query."""
    # 1. Verify service exports memory metric
    metrics_response = requests.get("http://localhost:8080/metrics")
    assert "asdlc_process_memory_bytes" in metrics_response.text
    assert 'type="rss"' in metrics_response.text

    # 2. Wait for scrape interval
    time.sleep(20)

    # 3. Query through API with type filter
    api_response = requests.get("http://localhost:8080/api/metrics/memory?service=orchestrator")
    data = api_response.json()
    assert len(data["dataPoints"]) > 0
    # Memory should be non-zero
    assert any(dp["value"] > 0 for dp in data["dataPoints"])
```

---

## Definition of Done

- [ ] All acceptance tests pass
- [ ] Unit tests added for ProcessMetricsCollector CPU export
- [ ] Integration tests verify query correctness
- [ ] Manual verification: dashboard shows real data in VM mode
- [ ] No regressions in mock mode functionality
- [ ] Code review completed
- [ ] Documentation updated if needed
