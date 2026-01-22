#!/bin/bash
set -euo pipefail

# build-images.sh - Build Docker images for dox-asdlc services
#
# Usage: ./scripts/build-images.sh [options] [services...]
#
# Services (default: all):
#   orchestrator    Build orchestrator image
#   workers         Build workers image
#   hitl-ui         Build HITL UI image
#
# Options:
#   --tag <tag>       Image tag (default: latest)
#   --registry <reg>  Registry prefix (default: dox-asdlc)
#   --push            Push images to registry after building
#   --minikube        Load images into minikube (for local k8s dev)
#   --no-cache        Build without Docker cache
#   --help            Show this help message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
REGISTRY="dox-asdlc"
TAG="latest"
PUSH=false
MINIKUBE=false
NO_CACHE=false

# Services to build
SERVICES=()

# Available services and their Dockerfile paths
declare -A SERVICE_DOCKERFILES=(
    ["orchestrator"]="docker/orchestrator/Dockerfile"
    ["workers"]="docker/workers/Dockerfile"
    ["hitl-ui"]="docker/hitl-ui/Dockerfile"
)

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

show_help() {
    head -20 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag|-t)
            TAG="$2"
            shift 2
            ;;
        --registry|-r)
            REGISTRY="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --minikube)
            MINIKUBE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            # Service name
            if [[ -n "${SERVICE_DOCKERFILES[$1]:-}" ]]; then
                SERVICES+=("$1")
            else
                error "Unknown service: $1"
                echo "Available services: ${!SERVICE_DOCKERFILES[*]}"
                exit 1
            fi
            shift
            ;;
    esac
done

# Default to all services if none specified
if [ ${#SERVICES[@]} -eq 0 ]; then
    SERVICES=("orchestrator" "workers" "hitl-ui")
fi

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        error "docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker."
        exit 1
    fi

    # Check if minikube is available when --minikube is used
    if [ "$MINIKUBE" = true ]; then
        if ! command -v minikube &> /dev/null; then
            error "minikube is not installed but --minikube was specified."
            exit 1
        fi
        if ! minikube status &> /dev/null; then
            error "minikube is not running. Start it with: minikube start"
            exit 1
        fi
    fi

    log "Prerequisites met."
}

# Build a single image
build_image() {
    local service=$1
    local dockerfile="${SERVICE_DOCKERFILES[$service]}"
    local image_name="${REGISTRY}/${service}:${TAG}"

    log "Building $image_name..."

    local build_args=(
        build
        -f "$PROJECT_ROOT/$dockerfile"
        -t "$image_name"
    )

    if [ "$NO_CACHE" = true ]; then
        build_args+=(--no-cache)
    fi

    # Add build context (project root)
    build_args+=("$PROJECT_ROOT")

    if ! docker "${build_args[@]}"; then
        error "Failed to build $image_name"
        return 1
    fi

    log "Successfully built $image_name"

    # Also tag as latest if using a different tag
    if [ "$TAG" != "latest" ]; then
        docker tag "$image_name" "${REGISTRY}/${service}:latest"
        log "Also tagged as ${REGISTRY}/${service}:latest"
    fi
}

# Push image to registry
push_image() {
    local service=$1
    local image_name="${REGISTRY}/${service}:${TAG}"

    log "Pushing $image_name..."

    if ! docker push "$image_name"; then
        error "Failed to push $image_name"
        return 1
    fi

    log "Successfully pushed $image_name"
}

# Load image into minikube
load_into_minikube() {
    local service=$1
    local image_name="${REGISTRY}/${service}:${TAG}"

    log "Loading $image_name into minikube..."

    if ! minikube image load "$image_name"; then
        error "Failed to load $image_name into minikube"
        return 1
    fi

    log "Successfully loaded $image_name into minikube"
}

# Build all requested services
build_all() {
    local failed=0

    for service in "${SERVICES[@]}"; do
        if ! build_image "$service"; then
            ((failed++))
        fi
    done

    return $failed
}

# Push all images
push_all() {
    local failed=0

    for service in "${SERVICES[@]}"; do
        if ! push_image "$service"; then
            ((failed++))
        fi
    done

    return $failed
}

# Load all images into minikube
load_all_minikube() {
    local failed=0

    for service in "${SERVICES[@]}"; do
        if ! load_into_minikube "$service"; then
            ((failed++))
        fi
    done

    return $failed
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "  Image Build Summary"
    echo "=========================================="
    echo ""
    echo "Registry:  $REGISTRY"
    echo "Tag:       $TAG"
    echo "Services:  ${SERVICES[*]}"
    echo ""
    echo "Images built:"
    for service in "${SERVICES[@]}"; do
        echo "  - ${REGISTRY}/${service}:${TAG}"
    done
    echo ""

    if [ "$MINIKUBE" = true ]; then
        echo "Images loaded into minikube."
        echo ""
    fi

    if [ "$PUSH" = true ]; then
        echo "Images pushed to registry."
        echo ""
    fi

    echo "Next steps:"
    if [ "$MINIKUBE" = true ]; then
        echo "  Deploy to minikube:  ./scripts/k8s/deploy.sh"
    else
        echo "  Load into minikube:  ./scripts/build-images.sh --minikube"
        echo "  Push to registry:    ./scripts/build-images.sh --push --registry <your-registry>"
    fi
    echo ""
}

# Main execution
main() {
    log "Starting image build process..."
    log "Services: ${SERVICES[*]}"
    log "Tag: $TAG"

    check_prerequisites

    if ! build_all; then
        error "Some images failed to build."
        exit 1
    fi

    if [ "$PUSH" = true ]; then
        if ! push_all; then
            error "Some images failed to push."
            exit 1
        fi
    fi

    if [ "$MINIKUBE" = true ]; then
        if ! load_all_minikube; then
            error "Some images failed to load into minikube."
            exit 1
        fi
    fi

    print_summary

    log "Build process complete."
}

main "$@"
