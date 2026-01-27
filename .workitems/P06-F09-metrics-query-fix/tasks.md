# P06-F09: VictoriaMetrics Metrics Query Fix - Tasks

**Version:** 1.0
**Date:** January 27, 2026
**Status:** Draft

## Task Overview

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: CPU Metric Export | T01-T03 | 1.5 hours |
| Phase 2: Query Fixes | T04-T07 | 2 hours |
| Phase 3: Testing | T08-T10 | 1.5 hours |

**Total Estimated Time:** 5 hours

---

## Phase 1: CPU Metric Export

### T01: Add CPU Metric Definition

**Description:** Add `PROCESS_CPU_PERCENT` gauge to definitions.py

**File:** `src/infrastructure/metrics/definitions.py`

**Changes:**
1. Add import if needed
2. Add PROCESS_CPU_PERCENT Gauge definition with service label
3. Add to __all__ exports

**Acceptance Criteria:**
- Gauge defined with name `asdlc_process_cpu_percent`
- Label `service` defined
- Exported in __all__

**Estimate:** 15 minutes

**Dependencies:** None

**Status:** [x] Completed

---

### T02: Add CPU Collection to ProcessMetricsCollector

**Description:** Extend ProcessMetricsCollector.collect() to yield CPU metric

**File:** `src/infrastructure/metrics/collectors.py`

**Changes:**
1. In `collect()` method, after memory collection:
   - Create GaugeMetricFamily for `asdlc_process_cpu_percent`
   - Get CPU percent using `process.cpu_percent(interval=None)`
   - Add metric with service label
   - Yield the gauge
2. Handle exceptions gracefully (log warning, yield 0.0)

**Code Pattern:**
```python
# CPU usage gauge (percentage)
cpu = GaugeMetricFamily(
    "asdlc_process_cpu_percent",
    "Process CPU usage percentage",
    labels=["service"],
)
try:
    cpu_percent = process.cpu_percent(interval=None)
    cpu.add_metric([self.service_name], cpu_percent)
except Exception as e:
    logger.warning(f"Failed to get CPU percent: {e}")
    cpu.add_metric([self.service_name], 0.0)
yield cpu
```

**Acceptance Criteria:**
- `asdlc_process_cpu_percent` metric yielded from collect()
- Service label correctly applied
- Graceful handling of errors

**Estimate:** 30 minutes

**Dependencies:** T01

**Status:** [x] Completed

---

### T03: Unit Test CPU Metric Export

**Description:** Add unit tests for CPU metric collection

**File:** `tests/unit/infrastructure/metrics/test_collectors.py`

**Tests to Add:**
1. `test_process_metrics_collector_exports_cpu` - Verify metric is yielded
2. `test_process_metrics_collector_cpu_has_service_label` - Verify label
3. `test_process_metrics_collector_cpu_value_range` - Verify 0-100 range

**Acceptance Criteria:**
- All tests pass
- Coverage for CPU metric code path
- Edge cases handled (psutil unavailable)

**Estimate:** 45 minutes

**Dependencies:** T02

**Status:** [x] Completed

---

## Phase 2: Query Fixes

### T04: Fix CPU Queries in metrics_api.py

**Description:** Update CPU queries to use correct metric name

**File:** `src/orchestrator/routes/metrics_api.py`

**Changes:**
1. In `get_cpu_metrics()`:
   - Change query from `rate(process_cpu_seconds_total...` to `asdlc_process_cpu_percent{...}`
   - Remove `* 100` since metric is already percentage
   - Update service filter to use `service=` label

**Before:**
```python
query = f'rate(process_cpu_seconds_total{{service="{service}"}}[5m]) * 100'
```

**After:**
```python
query = f'asdlc_process_cpu_percent{{service="{service}"}}'
```

**Acceptance Criteria:**
- Query uses `asdlc_process_cpu_percent`
- Service filter uses `service=` label
- No rate() calculation needed

**Estimate:** 20 minutes

**Dependencies:** T02

**Status:** [x] Completed

---

### T05: Fix Memory Queries in metrics_api.py

**Description:** Update memory queries to use correct metric name and type label

**File:** `src/orchestrator/routes/metrics_api.py`

**Changes:**
1. In `get_memory_metrics()`:
   - Change metric name from `process_resident_memory_bytes` to `asdlc_process_memory_bytes`
   - Add `type="rss"` filter
   - Update service filter to use `service=` label

**Before:**
```python
query = f'process_resident_memory_bytes{{service="{service}"}}'
```

**After:**
```python
query = f'asdlc_process_memory_bytes{{type="rss",service="{service}"}}'
```

**Acceptance Criteria:**
- Query uses `asdlc_process_memory_bytes`
- Includes `type="rss"` label
- Service filter uses `service=` label

**Estimate:** 20 minutes

**Dependencies:** None

**Status:** [x] Completed

---

### T06: Fix SERVICE_POD_LABELS in service_health.py

**Description:** Update label mappings from app= to service=

**File:** `src/orchestrator/services/service_health.py`

**Changes:**
1. Update `SERVICE_POD_LABELS` dict:
   ```python
   SERVICE_POD_LABELS: dict[str, str] = {
       "hitl-ui": 'service="hitl-ui"',
       "orchestrator": 'service="orchestrator"',
       "workers": 'service="workers"',
       "redis": 'service="redis"',
       "elasticsearch": 'service="elasticsearch"',
   }
   ```

**Acceptance Criteria:**
- All values use `service=` prefix
- No `app=` references remain

**Estimate:** 10 minutes

**Dependencies:** None

**Status:** [x] Completed

---

### T07: Fix Metric Queries in service_health.py

**Description:** Update all PromQL queries in service_health.py

**File:** `src/orchestrator/services/service_health.py`

**Changes:**
1. In `_fetch_service_health()`:
   - CPU: `rate(process_cpu_seconds_total...)` -> `asdlc_process_cpu_percent{...}`
   - Memory: `process_resident_memory_bytes` -> `asdlc_process_memory_bytes{type="rss",...}`

2. In `get_service_sparkline()` query_map:
   - cpu: `rate(process_cpu_seconds_total...)` -> `asdlc_process_cpu_percent{...}`
   - memory: `process_resident_memory_bytes` -> `asdlc_process_memory_bytes{type="rss",...}`

**Acceptance Criteria:**
- All CPU queries use `asdlc_process_cpu_percent`
- All memory queries use `asdlc_process_memory_bytes{type="rss"}`
- No `process_cpu_seconds_total` references remain
- No `process_resident_memory_bytes` references remain

**Estimate:** 30 minutes

**Dependencies:** T06

**Status:** [x] Completed

---

## Phase 3: Testing

### T08: Unit Test Query Strings

**Description:** Add unit tests to verify query string correctness

**File:** `tests/unit/orchestrator/test_metrics_queries.py` (new file)

**Tests to Add:**
1. `test_cpu_query_uses_asdlc_metric` - Verify metric name
2. `test_memory_query_uses_asdlc_metric_with_type` - Verify metric + type label
3. `test_service_pod_labels_use_service_prefix` - Verify label mapping
4. `test_queries_use_service_label_not_app` - Verify label selector

**Acceptance Criteria:**
- All query string tests pass
- Tests catch if wrong metric names used
- Tests catch if wrong label prefixes used

**Estimate:** 45 minutes

**Dependencies:** T04, T05, T06, T07

**Status:** [x] Completed

---

### T09: Integration Test with VictoriaMetrics

**Description:** Add integration tests for end-to-end metric flow

**File:** `tests/integration/test_metrics_api.py`

**Tests to Add:**
1. `test_cpu_endpoint_returns_data_from_vm` - Verify API returns real data
2. `test_memory_endpoint_returns_data_from_vm` - Verify API returns real data
3. `test_service_health_returns_data_from_vm` - Verify health endpoint

**Prerequisites:**
- VictoriaMetrics running
- Services scraped at least once

**Acceptance Criteria:**
- Tests pass with docker-compose running
- Tests can be skipped if VM unavailable
- Tests verify non-empty results

**Estimate:** 30 minutes

**Dependencies:** T08

**Status:** [ ] Not Started

---

### T10: Manual Verification

**Description:** Manual end-to-end verification with dashboard

**Steps:**
1. Start docker-compose with all services
2. Wait 30 seconds for scrape
3. Open metrics dashboard
4. Switch backend to VictoriaMetrics
5. Verify CPU chart shows data
6. Verify memory chart shows data
7. Verify service health shows HEALTHY
8. Verify sparklines render

**Document Results:**
- Screenshot or description of working dashboard
- Note any remaining issues

**Acceptance Criteria:**
- Dashboard displays real data in VM mode
- All charts render correctly
- No console errors
- Mock mode still works

**Estimate:** 15 minutes

**Dependencies:** T09

**Status:** [ ] Not Started

---

## Dependency Graph

```
T01 (Definition)
  |
  v
T02 (Collector)
  |
  v
T03 (Unit Test) --> T04 (CPU Query Fix)
                      |
T05 (Memory Query) ---+
                      |
T06 (Label Map) ------+
  |                   |
  v                   v
T07 (Health Queries)  |
  |                   |
  +-------------------+
           |
           v
         T08 (Query Tests)
           |
           v
         T09 (Integration)
           |
           v
         T10 (Manual)
```

## Progress Tracking

| Task | Status | Started | Completed | Notes |
|------|--------|---------|-----------|-------|
| T01 | [x] | 2026-01-27 | 2026-01-27 | PROCESS_CPU_PERCENT gauge added to definitions.py |
| T02 | [x] | 2026-01-27 | 2026-01-27 | CPU metric collection added to ProcessMetricsCollector |
| T03 | [x] | 2026-01-27 | 2026-01-27 | 4 unit tests added and passing |
| T04 | [x] | 2026-01-27 | 2026-01-27 | CPU queries fixed in metrics_api.py |
| T05 | [x] | 2026-01-27 | 2026-01-27 | Memory queries fixed in metrics_api.py |
| T06 | [x] | 2026-01-27 | 2026-01-27 | SERVICE_POD_LABELS updated to service= prefix |
| T07 | [x] | 2026-01-27 | 2026-01-27 | CPU/memory queries fixed in service_health.py |
| T08 | [x] | 2026-01-27 | 2026-01-27 | 11 query string tests added and passing |
| T09 | [ ] | | | |
| T10 | [ ] | | | |

**Overall Progress:** 8/10 tasks complete (80%)
