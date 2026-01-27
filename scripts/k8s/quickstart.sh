#!/bin/bash
set -euo pipefail

# quickstart.sh - Single script to start minikube, build images, and deploy
#
# Usage: ./scripts/k8s/quickstart.sh [options]
#
# Options:
#   --reset           Clean up existing cluster and start fresh
#   --skip-build      Skip image build (use existing images)
#   --skip-deploy     Stop after building images
#   --cpus <n>        Number of CPUs for minikube (default: 4)
#   --memory <n>      Memory in MB for minikube (default: 8192)
#   --wait            Wait for all pods to be ready after deploy
#   --help            Show this help message
#
# Notes:
#   This script is designed to work without Docker Desktop on Apple Silicon.
#   It uses minikube with the qemu2 driver and builds images directly inside
#   the minikube VM using 'minikube image build'.
#
#   On Intel Macs or when Docker is available, it will use the docker driver.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
PROFILE_NAME="dox-asdlc"
RESET=false
SKIP_BUILD=false
SKIP_DEPLOY=false
CPUS=4
MEMORY=8192
WAIT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --wait)
            WAIT=true
            shift
            ;;
        --help|-h)
            head -25 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log() {
    echo ""
    echo "========================================"
    echo "  $*"
    echo "========================================"
    echo ""
}

info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Detect if we need to use in-minikube builds (no Docker daemon)
detect_build_mode() {
    # Check if Docker daemon is available
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "docker"
    else
        echo "in-minikube"
    fi
}

# Detect the driver that will be used
detect_driver() {
    local arch
    arch=$(uname -m)

    if [[ "$arch" == "arm64" ]]; then
        echo "qemu2"
    else
        echo "docker"
    fi
}

# Check if cluster is already running
cluster_running() {
    minikube status -p "$PROFILE_NAME" 2>/dev/null | grep -q "Running"
}

# Step 1: Start minikube
step_start_minikube() {
    log "Step 1: Starting minikube cluster"

    local start_args=(
        --cpus "$CPUS"
        --memory "$MEMORY"
    )

    if [ "$RESET" = true ]; then
        start_args+=(--reset)
    fi

    if cluster_running && [ "$RESET" = false ]; then
        info "Minikube cluster '$PROFILE_NAME' is already running."
        info "Use --reset to start fresh."
    else
        "$SCRIPT_DIR/start-minikube.sh" "${start_args[@]}"
    fi
}

# Step 2: Build images
step_build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        info "Skipping image build (--skip-build specified)"
        return 0
    fi

    log "Step 2: Building Docker images"

    local build_mode
    build_mode=$(detect_build_mode)

    if [ "$build_mode" = "in-minikube" ]; then
        info "Docker daemon not available - building images inside minikube"
        "$PROJECT_ROOT/scripts/build-images.sh" --in-minikube --profile "$PROFILE_NAME"
    else
        info "Docker daemon available - building locally and loading into minikube"
        "$PROJECT_ROOT/scripts/build-images.sh" --minikube --profile "$PROFILE_NAME"
    fi
}

# Step 3: Deploy to Kubernetes
step_deploy() {
    if [ "$SKIP_DEPLOY" = true ]; then
        info "Skipping deployment (--skip-deploy specified)"
        return 0
    fi

    log "Step 3: Deploying to Kubernetes"

    local deploy_args=()

    if [ "$WAIT" = true ]; then
        deploy_args+=(--wait)
    fi

    "$SCRIPT_DIR/deploy.sh" "${deploy_args[@]}"
}

# Step 4: Setup host entries
step_setup_hosts() {
    log "Step 4: Setting up /etc/hosts entry"

    local minikube_ip
    minikube_ip=$(minikube ip -p "$PROFILE_NAME" 2>/dev/null || echo "")

    if [[ -z "$minikube_ip" ]]; then
        warn "Could not get minikube IP - skipping hosts setup"
        return 0
    fi

    # Check if entry already exists
    if grep -q "dox.local" /etc/hosts 2>/dev/null; then
        # Update existing entry if IP changed
        local current_ip
        current_ip=$(grep "dox.local" /etc/hosts | awk '{print $1}' | head -1)
        if [[ "$current_ip" != "$minikube_ip" ]]; then
            info "Updating /etc/hosts entry (IP changed from $current_ip to $minikube_ip)"
            sudo sed -i.bak "s/.*dox.local.*/$minikube_ip dox.local/" /etc/hosts
        else
            info "Host entry already exists: $minikube_ip dox.local"
        fi
    else
        info "Adding /etc/hosts entry: $minikube_ip dox.local"
        echo "$minikube_ip dox.local" | sudo tee -a /etc/hosts > /dev/null
    fi
}

# Print final summary
print_summary() {
    local driver
    driver=$(detect_driver)

    local build_mode
    build_mode=$(detect_build_mode)

    local minikube_ip
    minikube_ip=$(minikube ip -p "$PROFILE_NAME" 2>/dev/null || echo "N/A")

    echo ""
    echo "=========================================="
    echo "  dox-asdlc Quickstart Complete"
    echo "=========================================="
    echo ""
    echo "Cluster:     $PROFILE_NAME"
    echo "Driver:      $driver"
    echo "Build mode:  $build_mode"
    if [[ "$minikube_ip" != "N/A" ]]; then
        echo "IP:          $minikube_ip"
    fi
    echo ""
    echo "Service Access:"
    echo "  HITL UI:           http://dox.local/"
    echo "  Orchestrator API:  http://dox.local/api/"
    echo "  API Docs:          http://dox.local/docs"
    if [[ "$minikube_ip" != "N/A" ]]; then
        echo ""
        echo "  Elasticsearch:     http://$minikube_ip:30920"
        echo "  ES MCP Sidecar:    http://$minikube_ip:30921"
        echo "  Redis:             $minikube_ip:30637"
        echo "  Redis MCP Sidecar: http://$minikube_ip:30900"
    fi
    echo ""
    echo "Useful commands:"
    echo "  Check pods:        kubectl get pods -n dox-asdlc"
    echo "  View logs:         kubectl logs -n dox-asdlc <pod-name>"
    echo "  Helm status:       helm status dox-asdlc -n dox-asdlc"
    echo ""
    echo "To stop the cluster:"
    echo "  minikube stop -p $PROFILE_NAME"
    echo ""
    echo "To clean up completely:"
    echo "  ./scripts/k8s/teardown.sh"
    echo "  minikube delete -p $PROFILE_NAME"
    echo ""
}

# Main execution
main() {
    local driver
    driver=$(detect_driver)

    local build_mode
    build_mode=$(detect_build_mode)

    echo ""
    echo "=========================================="
    echo "  dox-asdlc Kubernetes Quickstart"
    echo "=========================================="
    echo ""
    echo "This script will:"
    echo "  1. Start minikube cluster (driver: $driver)"
    echo "  2. Build Docker images (mode: $build_mode)"
    echo "  3. Deploy to Kubernetes via Helm"
    echo "  4. Setup /etc/hosts entry for dox.local"
    echo ""

    if [ "$build_mode" = "in-minikube" ]; then
        echo "Note: No Docker daemon detected."
        echo "      Images will be built directly inside minikube."
        echo ""
    fi

    step_start_minikube
    step_build_images
    step_deploy
    step_setup_hosts
    print_summary

    info "Quickstart complete!"
}

main "$@"
