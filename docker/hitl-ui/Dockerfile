# aSDLC HITL Web UI Container
# Container 4: Human-in-the-Loop Web Interface
# Gate request viewer and evidence explorer
# Approval pushes responses back to Redis Streams

FROM node:20-alpine

# Install health check dependencies
RUN apk add --no-cache wget

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN addgroup -S asdlc && adduser -S asdlc -G asdlc && \
    chown -R asdlc:asdlc /app

# Environment variables
ENV NODE_ENV=production \
    SERVICE_NAME=hitl-ui \
    SERVICE_PORT=3000

# Copy package files first for better caching
# Note: In prototype phase, we create a minimal server
# Full UI will be implemented in P05-F01
COPY docker/hitl-ui/package.json /app/
COPY docker/hitl-ui/server.js /app/

# Install dependencies
RUN npm install --omit=dev 2>/dev/null || echo "No package.json yet, creating minimal server"

# Set ownership
RUN chown -R asdlc:asdlc /app

# Switch to non-root user
USER asdlc

# Expose web port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD wget -q --spider http://localhost:3000/health || exit 1

# Start the server
CMD ["node", "server.js"]
