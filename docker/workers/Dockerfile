# aSDLC Workers Container
# Container 2: Stateless agent worker pool
# Runs Claude Agent SDK queries with read-only workspace access
# No protected branch write access

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -s /bin/bash asdlc && \
    mkdir -p /app/workspace && \
    chown -R asdlc:asdlc /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ /app/src/

# Set ownership
RUN chown -R asdlc:asdlc /app

# Switch to non-root user
USER asdlc

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME=workers \
    SERVICE_PORT=8081 \
    GIT_WRITE_ACCESS=false

# Expose health check port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8081/health || exit 1

# Start the worker service
CMD ["python", "-m", "src.workers.main"]
