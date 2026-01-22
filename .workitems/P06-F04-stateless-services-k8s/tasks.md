# Tasks: P06-F04 Stateless Services Deployment

## Progress

- Started: 2026-01-22
- Tasks Complete: 10/10
- Percentage: 100%
- Status: COMPLETE
- Blockers: None

## Task List

### T01: Create orchestrator subchart structure
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_orchestrator_chart.py
- [x] Dependencies: P06-F01
- [x] Notes: Created Chart.yaml, values.yaml. Added as umbrella dependency.

### T02: Create orchestrator Deployment template
- [x] Estimate: 1hr
- [x] Tests: tests/unit/test_orchestrator_chart.py::TestOrchestratorDeploymentTemplate
- [x] Dependencies: T01
- [x] Notes: Single replica. Mount Git credentials secret. Configure health probes. Inject Redis/KnowledgeStore URLs.

### T03: Create orchestrator Service and ConfigMap
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_orchestrator_chart.py::TestOrchestratorServiceTemplate, TestOrchestratorConfigMapTemplate
- [x] Dependencies: T01
- [x] Notes: ClusterIP service. ConfigMap with environment variables.

### T04: Create workers subchart structure
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_workers_chart.py
- [x] Dependencies: P06-F01
- [x] Notes: Created Chart.yaml, values.yaml with HPA settings.

### T05: Create workers Deployment template
- [x] Estimate: 1hr
- [x] Tests: tests/unit/test_workers_chart.py::TestWorkersDeploymentTemplate
- [x] Dependencies: T04
- [x] Notes: Stateless deployment. Configure resource limits. Health probes. No Git credentials (governance principle).

### T06: Create workers HPA template
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_workers_chart.py::TestWorkersHPATemplate
- [x] Dependencies: T05
- [x] Notes: HPA with min/max replicas. Target CPU utilization. Behavior tuning for stable scaling.

### T07: Create hitl-ui subchart structure
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_hitl_ui_chart.py
- [x] Dependencies: P06-F01
- [x] Notes: Created Chart.yaml, values.yaml.

### T08: Create hitl-ui Deployment template
- [x] Estimate: 1hr
- [x] Tests: tests/unit/test_hitl_ui_chart.py::TestHitlUIDeploymentTemplate
- [x] Dependencies: T07
- [x] Notes: Node.js container. Health probes. Configure Redis URL for event polling.

### T09: Create hitl-ui Service template
- [x] Estimate: 30min
- [x] Tests: tests/unit/test_hitl_ui_chart.py::TestHitlUIServiceTemplate
- [x] Dependencies: T07
- [x] Notes: NodePort service for external access. Configurable nodePort value (30000).

### T10: Unit tests for all stateless service subcharts
- [x] Estimate: 1.5hr
- [x] Tests: tests/unit/test_orchestrator_chart.py, test_workers_chart.py, test_hitl_ui_chart.py
- [x] Dependencies: T01-T09
- [x] Notes: 105 tests total, all passing. Validates chart structure, values, templates, and helpers.

## Completion Checklist

- [x] All tasks marked complete
- [x] All unit tests pass (105 tests)
- [x] All services configured in umbrella chart
- [x] HPA configured for workers (min=2, max=10, CPU=70%)
- [x] HITL-UI externally accessible via NodePort 30000
- [x] values-minikube.yaml updated with dev settings
- [x] Documentation updated
- [x] Progress: 100%

## Notes

This feature completes the stateless services tier. After this feature, all aSDLC components have Kubernetes configurations.

### Files Created

**Orchestrator Subchart:**
- `helm/dox-asdlc/charts/orchestrator/Chart.yaml`
- `helm/dox-asdlc/charts/orchestrator/values.yaml`
- `helm/dox-asdlc/charts/orchestrator/templates/_helpers.tpl`
- `helm/dox-asdlc/charts/orchestrator/templates/deployment.yaml`
- `helm/dox-asdlc/charts/orchestrator/templates/service.yaml`
- `helm/dox-asdlc/charts/orchestrator/templates/configmap.yaml`

**Workers Subchart:**
- `helm/dox-asdlc/charts/workers/Chart.yaml`
- `helm/dox-asdlc/charts/workers/values.yaml`
- `helm/dox-asdlc/charts/workers/templates/_helpers.tpl`
- `helm/dox-asdlc/charts/workers/templates/deployment.yaml`
- `helm/dox-asdlc/charts/workers/templates/service.yaml`
- `helm/dox-asdlc/charts/workers/templates/configmap.yaml`
- `helm/dox-asdlc/charts/workers/templates/hpa.yaml`

**HITL-UI Subchart:**
- `helm/dox-asdlc/charts/hitl-ui/Chart.yaml`
- `helm/dox-asdlc/charts/hitl-ui/values.yaml`
- `helm/dox-asdlc/charts/hitl-ui/templates/_helpers.tpl`
- `helm/dox-asdlc/charts/hitl-ui/templates/deployment.yaml`
- `helm/dox-asdlc/charts/hitl-ui/templates/service.yaml`
- `helm/dox-asdlc/charts/hitl-ui/templates/configmap.yaml`

**Modified Files:**
- `helm/dox-asdlc/Chart.yaml` - Added all three subchart dependencies
- `helm/dox-asdlc/values.yaml` - Added orchestrator, workers, hitlUI sections
- `helm/dox-asdlc/values-minikube.yaml` - Enabled all services with dev settings

**Tests:**
- `tests/unit/test_orchestrator_chart.py` - 33 tests
- `tests/unit/test_workers_chart.py` - 38 tests
- `tests/unit/test_hitl_ui_chart.py` - 34 tests
