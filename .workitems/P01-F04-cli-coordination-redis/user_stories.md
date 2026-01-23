# User Stories: P01-F04 CLI Coordination Migration to Redis

## Epic Reference

This feature implements infrastructure improvements for the multi-CLI coordination system, migrating from filesystem-based JSON to Redis pub/sub with MCP wrapper.

## User Stories

### US-F04-01: Define Coordination Data Models

**As a** developer
**I want** structured data models for coordination messages
**So that** I have type-safe access to message data across Python and bash

**Acceptance Criteria:**
- [x] `CoordinationMessage` Pydantic model with all message fields
- [x] `MessageQuery` model for query parameters
- [x] `NotificationEvent` model for pub/sub events
- [x] `PresenceInfo` model for instance tracking
- [x] Models support JSON serialization for bash interop
- [x] All 16 message types are enumerated

**Priority:** High

---

### US-F04-02: Add Coordination Exceptions

**As a** developer
**I want** specific exceptions for coordination errors
**So that** I can handle different failure modes appropriately

**Acceptance Criteria:**
- [x] `CoordinationError` base exception exists
- [x] `MessageNotFoundError` for missing messages
- [x] `PublishError` for publishing failures
- [x] `AcknowledgeError` for acknowledgment failures
- [x] `PresenceError` for presence operation failures
- [x] All exceptions include helpful error messages
- [x] Exceptions inherit from `ASDLCError`

**Priority:** Medium

---

### US-F04-03: Implement Atomic Message Publishing

**As a** CLI user
**I want** messages to be published atomically
**So that** concurrent writes never cause race conditions

**Acceptance Criteria:**
- [x] `publish_message()` uses Redis pipeline with transaction
- [x] Message hash, timeline, inbox, and pending set updated atomically
- [x] Pub/sub notification sent within same transaction
- [x] Failed transactions roll back completely
- [x] Duplicate message IDs are rejected
- [x] Message timestamps use UTC

**Priority:** High

---

### US-F04-04: Implement Message Queries

**As a** CLI user
**I want** to query messages with filters
**So that** I can find relevant messages quickly

**Acceptance Criteria:**
- [x] `get_messages()` supports filtering by `to_instance`
- [x] Supports filtering by `from_instance`
- [x] Supports filtering by message `type`
- [x] Supports `pending_only` to show unacked messages
- [x] Supports `since` timestamp filter
- [x] Supports `limit` parameter
- [x] Query latency < 10ms for 100 messages

**Priority:** High

---

### US-F04-05: Implement Message Acknowledgment

**As a** CLI user
**I want** to acknowledge messages
**So that** senders know their messages were received

**Acceptance Criteria:**
- [x] `acknowledge_message()` updates message hash
- [x] Sets `acknowledged=true`, `ack_by`, `ack_timestamp`
- [x] Removes message from pending set
- [x] Optional `comment` field supported
- [x] Acknowledging already-acked message is idempotent
- [x] Returns false if message not found

**Priority:** High

---

### US-F04-06: Implement Real-Time Notifications

**As a** CLI user
**I want** real-time notifications when messages arrive
**So that** I don't have to poll for new messages

**Acceptance Criteria:**
- [x] `subscribe_notifications()` subscribes to instance channel
- [x] Notifications include message ID and type
- [x] Callback invoked within 1 second of publish
- [x] Supports both instance-specific and broadcast channels
- [x] Graceful handling of disconnection/reconnection

**Priority:** Medium

---

### US-F04-07: Implement Instance Presence Tracking

**As an** orchestrator
**I want** to know which CLI instances are active
**So that** I can route messages to available instances

**Acceptance Criteria:**
- [x] `register_instance()` records instance in presence hash
- [x] `heartbeat()` updates last activity timestamp
- [x] `get_presence()` returns all instance statuses
- [x] `unregister_instance()` removes from presence
- [x] Stale instances (no heartbeat in 5 min) marked inactive

**Priority:** Low

---

### US-F04-08: Create MCP Server Wrapper

**As a** Claude Code user
**I want** an MCP server for coordination
**So that** Claude can directly interact with the coordination system

**Acceptance Criteria:**
- [x] MCP server exposes `coord_publish_message` tool
- [x] Exposes `coord_check_messages` tool
- [x] Exposes `coord_ack_message` tool
- [x] Exposes `coord_get_presence` tool
- [x] Server runs via stdio transport
- [x] Tool inputs/outputs match bash script interface

**Priority:** Medium

---

### US-F04-09: Update Bash Scripts for Redis Backend

**As a** CLI user
**I want** bash scripts to use Redis for coordination
**So that** I get performance benefits and atomic operations

**Acceptance Criteria:**
- [x] `publish-message.sh` requires Redis
- [x] Fails fast with clear error if Redis unavailable
- [x] `check-messages.sh` uses Redis queries
- [x] `ack-message.sh` uses Redis acknowledgment
- [x] Output format unchanged (backward compatible)

**Priority:** High

**Note:** Filesystem fallback removed in January 2026. Redis is now required.

---

### US-F04-10: Enable Redis AOF Persistence

**As a** system operator
**I want** Redis to persist coordination messages
**So that** messages survive container restarts

**Acceptance Criteria:**
- [x] `appendonly yes` enabled in redis.conf
- [x] `appendfsync everysec` for balance of durability/performance
- [x] RDB snapshots increased frequency
- [x] Max 1 second data loss on crash
- [x] Persistence verified after container restart

**Priority:** High

---

### US-F04-11: Create Migration Script

**As a** system operator
**I want** to migrate existing filesystem messages to Redis
**So that** historical messages are available in the new system

**Acceptance Criteria:**
- [x] Script reads all JSON files from `.claude/coordination/messages/`
- [x] Preserves original message IDs and timestamps
- [x] Preserves acknowledgment status
- [x] Supports dry-run mode for validation
- [x] Reports success/failure counts
- [x] Handles malformed JSON gracefully

**Priority:** Medium

---

### US-F04-12: Create Parity Validation Script

**As a** system operator
**I want** to validate Redis and filesystem are in sync
**So that** I can trust the migration was successful

**Acceptance Criteria:**
- [x] Script compares message counts
- [x] Compares message content
- [x] Reports discrepancies
- [x] Runs automatically after dual-write period
- [x] Returns exit code 0 only if parity achieved

**Priority:** Low

**Note:** Parity validation completed. Filesystem fallback removed in January 2026.

---

## Non-Functional Requirements

### Performance ✅

- Publish operations complete in < 5ms
- Query operations complete in < 10ms for 100 messages
- Real-time notifications delivered in < 1 second
- System handles 10,000+ messages without degradation

### Reliability ✅

- Redis is required; scripts fail fast if unavailable
- No message loss during normal operations
- Max 1 second data loss on Redis crash (AOF)
- Graceful error messages when Redis unavailable

### Compatibility ✅

- Bash script interface unchanged
- Output format backward compatible
- Existing workflows continue to work
- No changes required to CLI identity system

### Maintainability ✅

- Comprehensive test coverage (>80%)
- Single backend (Redis) simplifies codebase
- Factory pattern for dependency injection
- Detailed logging for debugging

## Dependencies

| Story | Depends On |
|-------|-----------|
| US-F04-03 | US-F04-01 |
| US-F04-04 | US-F04-01 |
| US-F04-05 | US-F04-01 |
| US-F04-06 | US-F04-01 |
| US-F04-07 | US-F04-01 |
| US-F04-08 | US-F04-03, US-F04-04, US-F04-05 |
| US-F04-09 | US-F04-03, US-F04-04, US-F04-05 |
| US-F04-11 | US-F04-03 |
| US-F04-12 | US-F04-09 |
