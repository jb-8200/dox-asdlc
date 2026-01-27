# P06-F09: VictoriaMetrics Metrics Query Fix

**Version:** 1.0
**Date:** January 27, 2026
**Status:** Draft

## Overview

This feature fixes metric name and label mismatches between what the aSDLC services export and what the metrics dashboard queries expect. Currently, the metrics page works in mock mode but shows no data in VictoriaMetrics mode due to query/export misalignment.

### Goals

1. Add CPU metric collection to `ProcessMetricsCollector` (currently only exports memory)
2. Align PromQL queries with actual exported metric names (`asdlc_*` prefix)
3. Correct label selectors from `app=` to `service=` to match scrape.yml configuration
4. Ensure all metrics endpoints work with real VictoriaMetrics data

### Non-Goals

- Adding new metrics beyond CPU (out of scope)
- Changing the scrape.yml label convention (service= is correct)
- Modifying the dashboard frontend (P05 domain)
- Adding histogram support for CPU (counters are sufficient)

## Technical Approach

### Problem Analysis

Three distinct issues prevent real data from appearing:

#### Issue 1: Missing CPU Metric

`ProcessMetricsCollector` (collectors.py:176-222) only exports:
- `asdlc_process_memory_bytes{service, type}` with type=rss/vms

Dashboard queries use `process_cpu_seconds_total` which is never exported.

**Solution:** Add `asdlc_process_cpu_percent{service}` to ProcessMetricsCollector using `psutil.cpu_percent()`.

#### Issue 2: Wrong Metric Names

Queries in `metrics_api.py` and `service_health.py` use standard Prometheus metric names:
- `process_cpu_seconds_total`
- `process_resident_memory_bytes`

But aSDLC exports custom prefixed names:
- `asdlc_process_cpu_percent` (to be added)
- `asdlc_process_memory_bytes`

**Solution:** Update queries to use `asdlc_*` metric names.

#### Issue 3: Wrong Label Selectors

Queries use `app="service_name"` but `scrape.yml` applies:
```yaml
labels:
  service: 'orchestrator'  # Not 'app'
```

**Solution:** Change label selectors from `app=` to `service=`.

### Implementation Details

#### 1. Add CPU Metric to ProcessMetricsCollector

```python
# In collectors.py ProcessMetricsCollector.collect()
# Add after memory collection

# CPU usage gauge (percentage)
cpu = GaugeMetricFamily(
    "asdlc_process_cpu_percent",
    "Process CPU usage percentage",
    labels=["service"],
)
try:
    # Get CPU percent (non-blocking after first call)
    cpu_percent = process.cpu_percent(interval=None)
    cpu.add_metric([self.service_name], cpu_percent)
except Exception as e:
    logger.warning(f"Failed to get CPU metrics: {e}")
    cpu.add_metric([self.service_name], 0.0)
yield cpu
```

Note: `psutil.cpu_percent(interval=None)` returns CPU usage since last call. First call returns 0.0 which is acceptable for our use case.

#### 2. Add CPU Metric Definition

Add to `definitions.py`:

```python
PROCESS_CPU_PERCENT = Gauge(
    "asdlc_process_cpu_percent",
    "Process CPU usage percentage",
    ["service"],
)
```

#### 3. Update metrics_api.py Queries

| Current Query | Fixed Query |
|--------------|-------------|
| `process_cpu_seconds_total{service=...}` | `asdlc_process_cpu_percent{service=...}` |
| `process_resident_memory_bytes{service=...}` | `asdlc_process_memory_bytes{type="rss",service=...}` |
| `{app="..."}` | `{service="..."}` |

Specific changes in `get_cpu_metrics()`:
```python
# Before
query = f'rate(process_cpu_seconds_total{{service="{service}"}}[5m]) * 100'

# After
query = f'asdlc_process_cpu_percent{{service="{service}"}}'
```

Specific changes in `get_memory_metrics()`:
```python
# Before
query = f'process_resident_memory_bytes{{service="{service}"}}'

# After
query = f'asdlc_process_memory_bytes{{type="rss",service="{service}"}}'
```

#### 4. Update service_health.py Queries

Update `SERVICE_POD_LABELS` dict:
```python
# Before
SERVICE_POD_LABELS: dict[str, str] = {
    "hitl-ui": 'app="hitl-ui"',
    ...
}

# After
SERVICE_POD_LABELS: dict[str, str] = {
    "hitl-ui": 'service="hitl-ui"',
    ...
}
```

Update `_fetch_service_health()` queries:
```python
# CPU query - before
cpu_query = f'rate(process_cpu_seconds_total{{{label}}}[5m]) * 100'
# CPU query - after
cpu_query = f'asdlc_process_cpu_percent{{{label}}}'

# Memory query - before
memory_query = f'process_resident_memory_bytes{{{label}}} / container_spec_memory_limit_bytes{{{label}}} * 100'
# Memory query - after
memory_query = f'asdlc_process_memory_bytes{{type="rss",{label}}} / 1073741824 * 100'  # /1GB for percentage estimate
```

Update `get_service_sparkline()` query_map:
```python
query_map = {
    "cpu": f'asdlc_process_cpu_percent{{{label}}}',
    "memory": f'asdlc_process_memory_bytes{{type="rss",{label}}} / 1024 / 1024',  # MB
    ...
}
```

## Interfaces and Dependencies

### Upstream Dependencies

| Dependency | Purpose | Status |
|------------|---------|--------|
| psutil | CPU/memory metrics | Already installed |
| VictoriaMetrics | TSDB storage | P06-F06 complete |
| Prometheus client | Metric exposition | Already installed |

### Downstream Consumers

| Consumer | Impact |
|----------|--------|
| Metrics Dashboard (P05-F10) | Will display real data |
| Service Health Dashboard (P06-F07) | Will display real data |

### Affected Files

```
src/infrastructure/metrics/collectors.py    # Add CPU metric
src/infrastructure/metrics/definitions.py   # Add CPU definition
src/orchestrator/routes/metrics_api.py      # Fix queries
src/orchestrator/services/service_health.py # Fix queries
```

## Architecture Decisions

### ADR-1: Use cpu_percent Instead of cpu_times

**Decision:** Use `psutil.cpu_percent()` instead of `cpu_times()`.

**Rationale:**
- `cpu_percent()` returns a ready-to-use percentage value
- Dashboard expects percentage, not raw seconds
- Avoids complex rate() calculations in PromQL
- Simpler mental model for operators

**Tradeoff:** `cpu_percent(interval=None)` requires two calls to get a meaningful value; first call returns 0.0. This is acceptable because:
- Metrics are scraped every 15s
- After first scrape, all subsequent values are accurate
- Mock fallback handles the rare 0.0 case

### ADR-2: Keep asdlc_ Prefix Convention

**Decision:** Continue using `asdlc_` prefix for all custom metrics.

**Rationale:**
- Consistent with existing metrics (asdlc_http_requests_total, etc.)
- Clear namespace separation from standard Prometheus metrics
- Follows Prometheus naming best practices
- Already documented in definitions.py header

### ADR-3: Fix Queries Not Labels

**Decision:** Update queries to match existing label scheme (`service=`) rather than changing scrape.yml.

**Rationale:**
- scrape.yml already uses `service=` consistently
- Changing labels would require re-scraping all historical data
- Queries are easier to update than infrastructure config
- `service=` is semantically appropriate for this use case

## Testing Strategy

### Unit Tests

1. **ProcessMetricsCollector CPU test**
   - Verify `asdlc_process_cpu_percent` is yielded
   - Verify service label is correctly applied
   - Verify graceful handling when psutil unavailable

2. **Query string tests**
   - Verify correct metric names in query strings
   - Verify correct label selectors

### Integration Tests

1. **Metrics endpoint test**
   - Scrape /metrics endpoint
   - Verify `asdlc_process_cpu_percent` is present
   - Verify `asdlc_process_memory_bytes` has type=rss label

2. **VictoriaMetrics query test**
   - Query VictoriaMetrics with fixed queries
   - Verify non-empty results for running services

### Manual Verification

1. Start services with docker-compose
2. Wait for 2-3 scrape intervals (30-45s)
3. Open metrics dashboard
4. Toggle from Mock to VictoriaMetrics backend
5. Verify CPU and memory charts show real data

## File Structure

### Modified Files

```
src/infrastructure/metrics/collectors.py    # Add CPU collection
src/infrastructure/metrics/definitions.py   # Add PROCESS_CPU_PERCENT
src/orchestrator/routes/metrics_api.py      # Fix metric names and labels
src/orchestrator/services/service_health.py # Fix metric names and labels
```

### Test Files

```
tests/unit/infrastructure/metrics/test_collectors.py  # Add CPU tests
tests/integration/test_metrics_api.py                 # Add query tests
```

## Rollout Plan

1. Update collectors.py to add CPU metric export
2. Update definitions.py with CPU metric definition
3. Update metrics_api.py queries
4. Update service_health.py queries
5. Run tests to verify fixes
6. Manual verification with docker-compose
