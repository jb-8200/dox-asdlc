# aSDLC Infrastructure Container
# Redis 7 for event streams and task state caches
# ChromaDB support will be added in P01-F03

FROM redis:7-alpine

# Install health check dependencies
RUN apk add --no-cache curl

# Copy custom Redis configuration
COPY docker/infrastructure/redis.conf /usr/local/etc/redis/redis.conf

# Create data directory for persistence
RUN mkdir -p /data && chown redis:redis /data

# Expose Redis port
EXPOSE 6379

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=5s \
    CMD redis-cli ping | grep -q PONG || exit 1

# Run Redis with custom config
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
