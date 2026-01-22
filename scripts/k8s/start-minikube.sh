#!/bin/bash
set -euo pipefail

# start-minikube.sh - Initialize minikube cluster for dox-asdlc development
#
# Usage: ./scripts/k8s/start-minikube.sh [options]
#
# Options:
#   --cpus <n>      Number of CPUs (default: 4)
#   --memory <n>    Memory in MB (default: 8192)
#   --driver <name> Minikube driver (default: docker)
#   --reset         Delete existing cluster and start fresh
#   --help          Show this help message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default configuration
PROFILE_NAME="dox-asdlc"
CPUS=4
MEMORY=8192
DRIVER="docker"
RESET=false

# Required minikube addons
REQUIRED_ADDONS=(
    "ingress"
    "metrics-server"
    "storage-provisioner"
)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --driver)
            DRIVER="$2"
            shift 2
            ;;
        --reset)
            RESET=true
            shift
            ;;
        --help|-h)
            head -20 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v minikube &> /dev/null; then
        error "minikube is not installed. Please install minikube first."
        echo "  Visit: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed. Please install kubectl first."
        echo "  Visit: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        error "helm is not installed. Please install helm first."
        echo "  Visit: https://helm.sh/docs/intro/install/"
        exit 1
    fi

    log "All prerequisites met."
}

# Check if cluster exists and is running
cluster_exists() {
    minikube profile list 2>/dev/null | grep -q "$PROFILE_NAME"
}

cluster_running() {
    minikube status -p "$PROFILE_NAME" 2>/dev/null | grep -q "Running"
}

# Delete existing cluster if reset requested
reset_cluster() {
    if cluster_exists; then
        log "Deleting existing cluster '$PROFILE_NAME'..."
        minikube delete -p "$PROFILE_NAME"
        log "Cluster deleted."
    fi
}

# Start or create the cluster
start_cluster() {
    if cluster_running; then
        log "Cluster '$PROFILE_NAME' is already running."
        return 0
    fi

    if cluster_exists; then
        log "Starting existing cluster '$PROFILE_NAME'..."
        minikube start -p "$PROFILE_NAME"
    else
        log "Creating new cluster '$PROFILE_NAME'..."
        minikube start \
            -p "$PROFILE_NAME" \
            --cpus="$CPUS" \
            --memory="$MEMORY" \
            --driver="$DRIVER" \
            --kubernetes-version=stable
    fi

    log "Cluster started successfully."
}

# Enable required addons
enable_addons() {
    log "Enabling required addons..."

    for addon in "${REQUIRED_ADDONS[@]}"; do
        if minikube addons list -p "$PROFILE_NAME" | grep "$addon" | grep -q "enabled"; then
            log "  Addon '$addon' already enabled."
        else
            log "  Enabling addon '$addon'..."
            minikube addons enable "$addon" -p "$PROFILE_NAME"
        fi
    done

    log "All addons enabled."
}

# Configure kubectl context
configure_kubectl() {
    log "Configuring kubectl context..."
    kubectl config use-context "$PROFILE_NAME"
    log "kubectl configured to use '$PROFILE_NAME' context."
}

# Verify cluster health
verify_cluster() {
    log "Verifying cluster health..."

    # Wait for core pods to be ready
    log "  Waiting for kube-system pods..."
    kubectl wait --for=condition=Ready pods --all -n kube-system --timeout=120s 2>/dev/null || {
        log "  Some system pods still starting, this is normal on first boot."
    }

    # Check node status
    log "  Checking node status..."
    kubectl get nodes

    log "Cluster verification complete."
}

# Print summary
print_summary() {
    local minikube_ip
    minikube_ip=$(minikube ip -p "$PROFILE_NAME")

    echo ""
    echo "=========================================="
    echo "  dox-asdlc Minikube Cluster Ready"
    echo "=========================================="
    echo ""
    echo "Profile:     $PROFILE_NAME"
    echo "IP:          $minikube_ip"
    echo "CPUs:        $CPUS"
    echo "Memory:      ${MEMORY}MB"
    echo "Driver:      $DRIVER"
    echo ""
    echo "Enabled addons:"
    for addon in "${REQUIRED_ADDONS[@]}"; do
        echo "  - $addon"
    done
    echo ""
    echo "Next steps:"
    echo "  1. Deploy services: ./scripts/k8s/deploy.sh"
    echo "  2. Check pods:      kubectl get pods -n dox-asdlc"
    echo "  3. Access HITL-UI:  http://$minikube_ip:30000"
    echo ""
    echo "To stop the cluster:"
    echo "  minikube stop -p $PROFILE_NAME"
    echo ""
}

# Main execution
main() {
    log "Starting dox-asdlc minikube cluster initialization..."

    check_prerequisites

    if [ "$RESET" = true ]; then
        reset_cluster
    fi

    start_cluster
    enable_addons
    configure_kubectl
    verify_cluster
    print_summary

    log "Minikube cluster initialization complete."
}

main "$@"
