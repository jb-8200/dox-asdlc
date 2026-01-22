#!/bin/bash
# Migrate filesystem coordination messages to Redis.
#
# Reads existing JSON files from .claude/coordination/messages/
# and imports them into Redis, preserving IDs, timestamps, and ack status.
#
# Usage:
#   ./scripts/coordination/migrate-to-redis.sh [--dry-run]
#
# Options:
#   --dry-run    Show what would be migrated without writing to Redis
#   -h, --help   Show this help
#
# Environment:
#   REDIS_HOST - Redis hostname (default: localhost)
#   REDIS_PORT - Redis port (default: 6379)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COORDINATION_DIR="$PROJECT_ROOT/.claude/coordination"
MESSAGES_DIR="$COORDINATION_DIR/messages"

# Load common helper functions
# shellcheck source=lib/common.sh
if [[ -f "$SCRIPT_DIR/lib/common.sh" ]]; then
    source "$SCRIPT_DIR/lib/common.sh"
fi

# Counters
TOTAL=0
SUCCESS=0
SKIPPED=0
FAILED=0
DRY_RUN=false

usage() {
    echo "Usage: $0 [--dry-run]"
    echo ""
    echo "Migrate filesystem coordination messages to Redis."
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be migrated without writing"
    echo "  -h, --help   Show this help"
    echo ""
    echo "Environment:"
    echo "  REDIS_HOST - Redis hostname (default: localhost)"
    echo "  REDIS_PORT - Redis port (default: 6379)"
}

# Check Redis availability
check_redis() {
    if ! check_redis_available 2>/dev/null; then
        echo "Error: Redis is not available at ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
        echo "Please start Redis or set REDIS_HOST/REDIS_PORT environment variables."
        exit 1
    fi
}

# Check Python coordination module
check_python() {
    if ! python3 -c "from src.infrastructure.coordination import get_coordination_client" 2>/dev/null; then
        echo "Error: Python coordination module not available"
        echo "Make sure PYTHONPATH includes the project root."
        exit 1
    fi
}

# Migrate a single message file
migrate_message() {
    local file="$1"
    local filename
    filename=$(basename "$file")

    # Parse JSON
    local json
    if ! json=$(cat "$file" 2>/dev/null); then
        echo "  [FAIL] Cannot read: $filename"
        ((FAILED++))
        return 1
    fi

    # Validate JSON
    if ! echo "$json" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        echo "  [FAIL] Invalid JSON: $filename"
        ((FAILED++))
        return 1
    fi

    # Extract fields
    local msg_id type from_instance to_instance timestamp requires_ack acknowledged
    local subject description ack_by ack_timestamp ack_comment

    msg_id=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
    type=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('type',''))")
    from_instance=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('from',''))")
    to_instance=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('to',''))")
    timestamp=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('timestamp',''))")
    requires_ack=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('requires_ack',False))")
    acknowledged=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('acknowledged',False))")
    subject=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('payload',{}).get('subject',''))")
    description=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('payload',{}).get('description',''))")
    ack_by=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ack_by',''))")
    ack_timestamp=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ack_timestamp',''))")
    ack_comment=$(echo "$json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ack_comment',''))")

    # Skip if missing required fields
    if [[ -z "$msg_id" || -z "$type" ]]; then
        echo "  [SKIP] Missing ID or type: $filename"
        ((SKIPPED++))
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY] Would migrate: $msg_id ($type from $from_instance)"
        if [[ "$acknowledged" == "True" ]]; then
            echo "        (already acknowledged by $ack_by)"
        fi
        ((SUCCESS++))
        return 0
    fi

    # Import to Redis via Python
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

    local result
    result=$(python3 << PYEOF
import asyncio
import json
import sys
from datetime import datetime, timezone

async def main():
    from src.infrastructure.coordination import get_coordination_client
    from src.infrastructure.coordination.types import MessageType, CoordinationMessage, MessagePayload

    try:
        client = await get_coordination_client()

        # Check if message already exists
        existing = await client.get_message("$msg_id")
        if existing:
            print(json.dumps({"status": "skip", "reason": "already exists"}))
            return

        # Parse timestamp
        try:
            ts = datetime.fromisoformat("$timestamp".replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(timezone.utc)

        # Convert requires_ack to bool
        requires_ack = "$requires_ack" == "True"

        # Create message with original data
        msg = CoordinationMessage(
            id="$msg_id",
            type=MessageType("$type"),
            from_instance="$from_instance",
            to_instance="$to_instance",
            timestamp=ts,
            requires_ack=requires_ack,
            payload=MessagePayload(subject="""$subject""", description="""$description"""),
        )

        # Import message directly to Redis
        # This bypasses the normal publish to preserve original timestamps
        redis = client._redis
        config = client._config

        msg_key = f"{config.key_prefix}msg:{msg.id}"
        timeline_key = f"{config.key_prefix}timeline"
        inbox_key = f"{config.key_prefix}inbox:{msg.to_instance}"
        pending_key = f"{config.key_prefix}pending"

        # Build hash data
        msg_hash = {
            "id": msg.id,
            "type": msg.type.value,
            "from_instance": msg.from_instance,
            "to_instance": msg.to_instance,
            "timestamp": msg.timestamp.isoformat(),
            "requires_ack": str(requires_ack),
            "subject": msg.payload.subject,
            "description": msg.payload.description,
        }

        # Add ack fields if acknowledged
        acknowledged = "$acknowledged" == "True"
        if acknowledged:
            msg_hash["acknowledged"] = "True"
            msg_hash["ack_by"] = "$ack_by"
            if "$ack_timestamp":
                msg_hash["ack_timestamp"] = "$ack_timestamp"
            if "$ack_comment":
                msg_hash["ack_comment"] = """$ack_comment"""
        else:
            msg_hash["acknowledged"] = "False"

        # Store in Redis
        timestamp_unix = msg.timestamp.timestamp()

        async with redis.pipeline(transaction=True) as pipe:
            pipe.hset(msg_key, mapping=msg_hash)
            pipe.expire(msg_key, config.message_ttl_seconds)
            pipe.zadd(timeline_key, {msg.id: timestamp_unix})
            pipe.sadd(inbox_key, msg.id)
            if requires_ack and not acknowledged:
                pipe.sadd(pending_key, msg.id)
            await pipe.execute()

        print(json.dumps({"status": "ok", "id": msg.id}))

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)

asyncio.run(main())
PYEOF
)

    local status
    status=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','error'))")

    case "$status" in
        ok)
            echo "  [OK]   Migrated: $msg_id ($type)"
            ((SUCCESS++))
            ;;
        skip)
            local reason
            reason=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('reason',''))")
            echo "  [SKIP] $msg_id: $reason"
            ((SKIPPED++))
            ;;
        error)
            local error
            error=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error','Unknown error'))")
            echo "  [FAIL] $msg_id: $error"
            ((FAILED++))
            ;;
    esac
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    echo ""
    echo "=== CLI Coordination Migration: Filesystem -> Redis ==="
    echo ""

    # Check prerequisites
    if [[ "$DRY_RUN" != "true" ]]; then
        echo "Checking prerequisites..."
        check_redis
        check_python
        echo "Prerequisites OK"
        echo ""
    else
        echo "[DRY RUN MODE - no changes will be made]"
        echo ""
    fi

    # Check for message files
    if [[ ! -d "$MESSAGES_DIR" ]]; then
        echo "No messages directory found: $MESSAGES_DIR"
        echo "Nothing to migrate."
        exit 0
    fi

    local files
    files=$(find "$MESSAGES_DIR" -name "*.json" 2>/dev/null | sort)

    if [[ -z "$files" ]]; then
        echo "No message files found in $MESSAGES_DIR"
        echo "Nothing to migrate."
        exit 0
    fi

    TOTAL=$(echo "$files" | wc -l | tr -d ' ')
    echo "Found $TOTAL message file(s) to process"
    echo ""

    # Process each file
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        migrate_message "$file"
    done <<< "$files"

    # Summary
    echo ""
    echo "=== Migration Summary ==="
    echo "  Total:   $TOTAL"
    echo "  Success: $SUCCESS"
    echo "  Skipped: $SKIPPED"
    echo "  Failed:  $FAILED"
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "This was a dry run. Run without --dry-run to perform actual migration."
    elif [[ "$FAILED" -gt 0 ]]; then
        echo "Some messages failed to migrate. Check errors above."
        exit 1
    else
        echo "Migration complete!"
    fi
}

main "$@"
