# User Stories: P06-F05 Multi-Tenancy Support

## US-01: Set Tenant Context for Requests

**As a** service component
**I want** to set and retrieve tenant context
**So that** operations are scoped to the correct tenant

### Acceptance Criteria

The `TenantContext` class provides `set_tenant()` and `get_current_tenant()` methods. Context is thread-safe using `contextvars`. A `tenant_scope()` context manager ensures cleanup. `TenantNotSetError` is raised when accessing context without setting tenant.

### Test Scenarios

**Scenario 1: Set and get tenant**
Given a request handler, when I call `TenantContext.set_tenant("acme")` then `get_current_tenant()` returns "acme".

**Scenario 2: Context isolation**
Given two concurrent requests with different tenants, when processed in parallel, then each sees only its own tenant ID.

**Scenario 3: Missing tenant**
Given no tenant set, when I call `get_current_tenant()`, then `TenantNotSetError` is raised.

---

## US-02: Isolate Redis Data by Tenant

**As a** operator
**I want** Redis keys prefixed by tenant
**So that** tenants cannot access each other's data

### Acceptance Criteria

All Redis keys are prefixed with `tenant:{tenant_id}:`. Event streams are tenant-isolated. Task and session hashes are tenant-isolated. The prefix is applied transparently to existing code.

### Test Scenarios

**Scenario 1: Key prefixing**
Given tenant "acme", when I write to key "asdlc:events", then the actual key is "tenant:acme:asdlc:events".

**Scenario 2: Tenant isolation**
Given data written by tenant "acme", when tenant "widgets" queries the same logical key, then no data is returned.

---

## US-03: Isolate KnowledgeStore Collections by Tenant

**As a** operator
**I want** KnowledgeStore collections namespaced by tenant
**So that** document searches are tenant-scoped

### Acceptance Criteria

Collection names include tenant prefix: `{tenant_id}_asdlc_documents`. Documents indexed by one tenant are invisible to others. Search queries only return results from the current tenant's collection.

### Test Scenarios

**Scenario 1: Collection naming**
Given tenant "acme", when I index a document, then it goes to collection "acme_asdlc_documents".

**Scenario 2: Search isolation**
Given documents indexed by "acme", when "widgets" searches, then no results are returned.

---

## US-04: Include Tenant in Event Payloads

**As a** service component
**I want** all events to include tenant_id
**So that** async processors know which tenant context to use

### Acceptance Criteria

All events published to Redis include `tenant_id` field. Event consumers extract tenant from payload. Consumer sets tenant context before processing. Missing tenant_id events are rejected.

### Test Scenarios

**Scenario 1: Event publishing**
Given tenant "acme", when I publish an event, then the payload includes `"tenant_id": "acme"`.

**Scenario 2: Event consumption**
Given an event with `tenant_id: "acme"`, when consumed, then the handler runs with tenant context "acme".

---

## US-05: Select Tenant in HITL-UI

**As a** user
**I want** to select my tenant in the HITL-UI
**So that** I see only my organization's gate requests

### Acceptance Criteria

A tenant selector dropdown appears in the UI header. Selected tenant is persisted in browser session. All API requests include `X-Tenant-ID` header. Gate requests are filtered by selected tenant.

### Test Scenarios

**Scenario 1: Tenant selection**
Given the HITL-UI, when I select "acme" from the dropdown, then subsequent requests include `X-Tenant-ID: acme`.

**Scenario 2: Data filtering**
Given tenants "acme" and "widgets" with pending gates, when "acme" views the UI, then only "acme" gates are shown.

---

## US-06: Validate Tenant Access

**As a** security engineer
**I want** tenant IDs validated against an allowlist
**So that** unauthorized tenants cannot access the system

### Acceptance Criteria

The `ALLOWED_TENANTS` configuration lists valid tenants. Requests with invalid tenant IDs are rejected with 403. Wildcard `*` allows any tenant (development mode). Invalid tenants are logged for security monitoring.

### Test Scenarios

**Scenario 1: Allowed tenant**
Given `ALLOWED_TENANTS=acme,widgets`, when a request comes with `X-Tenant-ID: acme`, then it is processed.

**Scenario 2: Denied tenant**
Given `ALLOWED_TENANTS=acme,widgets`, when a request comes with `X-Tenant-ID: evil`, then 403 is returned.

**Scenario 3: Wildcard mode**
Given `ALLOWED_TENANTS=*`, when any tenant ID is provided, then it is accepted.
