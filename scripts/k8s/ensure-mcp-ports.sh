#!/bin/bash
# ensure-mcp-ports.sh - Ensure MCP port-forwards are running for K8s
#
# This script checks if minikube is running and starts port-forwards
# if they're not already active. Safe to run multiple times.
#
# Usage:
#   ./scripts/k8s/ensure-mcp-ports.sh
#
# Add to shell profile for auto-start:
#   echo 'source ~/VSProjects/dox-asdlc/scripts/k8s/ensure-mcp-ports.sh 2>/dev/null' >> ~/.zshrc

NAMESPACE="dox-asdlc"
PROFILE="dox-asdlc"

# Check if minikube cluster is running
if ! minikube status -p "$PROFILE" &>/dev/null; then
    # Minikube not running - use local services or skip
    exit 0
fi

# Check and start Elasticsearch port-forward (for Knowledge Store MCP)
if ! lsof -i :9200 &>/dev/null; then
    echo "[MCP] Starting Elasticsearch port-forward (9200)..."
    kubectl port-forward svc/knowledge-store 9200:9200 -n "$NAMESPACE" &>/dev/null &
    disown
fi

# Check and start Redis port-forward (for Redis MCP sidecar)
if ! lsof -i :9000 &>/dev/null; then
    echo "[MCP] Starting Redis MCP port-forward (9000)..."
    kubectl port-forward svc/dox-asdlc-redis 9000:9000 -n "$NAMESPACE" &>/dev/null &
    disown
fi

# Check and start HITL UI port-forward
if ! lsof -i :3000 &>/dev/null; then
    echo "[MCP] Starting HITL UI port-forward (3000)..."
    kubectl port-forward svc/dox-asdlc-hitl-ui 3000:3000 -n "$NAMESPACE" &>/dev/null &
    disown
fi

echo "[MCP] Port-forwards ready: ES(9200) Redis(9000) HITL(3000)"
