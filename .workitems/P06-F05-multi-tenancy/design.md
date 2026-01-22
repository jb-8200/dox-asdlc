# Feature Design: P06-F05 Multi-Tenancy Support

## Overview

This feature implements multi-tenancy support across the aSDLC system, enabling isolation between different users or organizations. Tenant context is propagated through all layers, affecting Redis key prefixing, KnowledgeStore collection isolation, and event stream routing.

## Dependencies

- **P06-F01**: Kubernetes base infrastructure
- **P06-F02**: Redis StatefulSet
- **P06-F03**: ChromaDB StatefulSet
- **P06-F04**: Stateless services deployment
- **P01-F03**: KnowledgeStore interface

## Interfaces

### Provided Interfaces

**Tenant Context Module**
Core module for tenant identification and propagation:
```python
# src/core/tenant.py
class TenantContext:
    """Thread-local tenant context for request isolation."""

    @classmethod
    def get_current_tenant(cls) -> str:
        """Get current tenant ID or raise TenantNotSetError."""

    @classmethod
    def set_tenant(cls, tenant_id: str) -> None:
        """Set tenant for current request context."""

    @classmethod
    @contextmanager
    def tenant_scope(cls, tenant_id: str) -> Generator[None, None, None]:
        """Context manager for tenant scope."""
```

**Tenant-Aware Redis Keys**
Redis key prefixing pattern:
```
tenant:{tenant_id}:asdlc:events
tenant:{tenant_id}:asdlc:task:{task_id}
tenant:{tenant_id}:asdlc:session:{session_id}
```

**Tenant-Aware KnowledgeStore**
Collection naming pattern:
```
{tenant_id}_asdlc_documents
{tenant_id}_asdlc_specs
```

**Event Tenant Context**
All events include tenant identification:
```json
{
  "event_id": "...",
  "tenant_id": "acme-corp",
  "event_type": "task_created",
  ...
}
```

### Required Interfaces

**From P06-F04:**
- Running orchestrator, workers, and HITL-UI services

**From P01-F03:**
- KnowledgeStore protocol and implementations

## Technical Approach

### Tenant Identification

Tenants are identified via:
1. HTTP header `X-Tenant-ID` on incoming requests
2. Environment variable `DEFAULT_TENANT_ID` for single-tenant deployments
3. Event payload `tenant_id` field for async processing

### Context Propagation

Tenant context uses Python's `contextvars` for thread-safe propagation:

```python
import contextvars

_tenant_id: contextvars.ContextVar[str] = contextvars.ContextVar('tenant_id')

class TenantContext:
    @classmethod
    def get_current_tenant(cls) -> str:
        try:
            return _tenant_id.get()
        except LookupError:
            raise TenantNotSetError("No tenant set in current context")
```

### Redis Key Prefixing

The Redis client is wrapped to automatically prefix keys:

```python
class TenantAwareRedisClient:
    def _prefix_key(self, key: str) -> str:
        tenant = TenantContext.get_current_tenant()
        return f"tenant:{tenant}:{key}"
```

Alternatively, a tenant-aware factory creates clients with embedded prefixing.

### KnowledgeStore Collection Isolation

Collections are namespaced per tenant:

```python
def get_collection_name(base_name: str) -> str:
    tenant = TenantContext.get_current_tenant()
    return f"{tenant}_{base_name}"
```

The ChromaDB implementation creates collections on-demand with tenant prefix.

### HITL-UI Tenant Selector

The HITL-UI includes a tenant selector component:
- Dropdown populated from configured tenant list
- Selected tenant stored in session
- All API requests include `X-Tenant-ID` header

## File Structure

```
src/core/
├── tenant.py              # Tenant context module
├── config.py              # Modified for tenant config
└── exceptions.py          # TenantNotSetError

src/infrastructure/
├── redis_client.py        # Modified for tenant prefixing
└── knowledge_store/
    └── config.py          # Modified for tenant collections

tests/
├── unit/
│   └── test_tenant.py     # Tenant context tests
└── integration/
    └── test_multi_tenant.py  # Multi-tenant isolation tests
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MULTI_TENANCY_ENABLED` | `false` | Enable multi-tenancy |
| `DEFAULT_TENANT_ID` | `default` | Default tenant for single-tenant mode |
| `ALLOWED_TENANTS` | `*` | Comma-separated tenant allowlist or `*` |

### Helm Values

```yaml
multiTenancy:
  enabled: true
  defaultTenant: "default"
  allowedTenants:
    - "acme-corp"
    - "widgets-inc"
```

## Security Considerations

1. **Tenant validation**: All incoming tenant IDs are validated against allowlist
2. **No cross-tenant access**: Redis keys and collections are strictly prefixed
3. **Audit logging**: All tenant context switches are logged
4. **Header validation**: `X-Tenant-ID` header is validated before processing

## Open Questions

Federation across multiple Kubernetes clusters per tenant is out of scope for this feature.

## Risks

**Risk 1: Tenant context leak**
Mitigation: Use contextvars with strict scoping. Always clear context after request completion.

**Risk 2: Missing tenant validation**
Mitigation: Middleware enforces tenant header presence. Integration tests verify isolation.
