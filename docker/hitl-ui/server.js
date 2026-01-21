/**
 * aSDLC HITL UI Server
 * Minimal prototype server for health checks
 * Full implementation in P05-F01
 */

const http = require('http');

const SERVICE_NAME = process.env.SERVICE_NAME || 'hitl-ui';
const SERVICE_PORT = parseInt(process.env.SERVICE_PORT || '3000', 10);
const REDIS_HOST = process.env.REDIS_HOST || 'infrastructure';
const REDIS_PORT = process.env.REDIS_PORT || '6379';

/**
 * Generate health check response
 * @returns {Object} Health status object
 */
function getHealthStatus() {
    return {
        status: 'healthy',
        service: SERVICE_NAME,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        dependencies: {
            redis: {
                host: REDIS_HOST,
                port: REDIS_PORT,
                status: 'unchecked' // Full check in P05-F01
            }
        }
    };
}

/**
 * Request handler
 */
function requestHandler(req, res) {
    const { method, url } = req;

    // Health check endpoint
    if (url === '/health' && method === 'GET') {
        const health = getHealthStatus();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(health, null, 2));
        return;
    }

    // Root endpoint - placeholder UI
    if (url === '/' && method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>aSDLC HITL Interface</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .status { color: #28a745; }
        code {
            background: #f0f0f0;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>aSDLC HITL Interface</h1>
        <p class="status">Service Status: Healthy</p>
        <p>Full implementation coming in Phase 5 (P05-F01)</p>
        <h2>Endpoints</h2>
        <ul>
            <li><code>GET /health</code> - Health check endpoint</li>
            <li><code>GET /</code> - This page</li>
        </ul>
        <h2>Configuration</h2>
        <ul>
            <li>Service: ${SERVICE_NAME}</li>
            <li>Port: ${SERVICE_PORT}</li>
            <li>Redis: ${REDIS_HOST}:${REDIS_PORT}</li>
        </ul>
    </div>
</body>
</html>
        `);
        return;
    }

    // 404 for unknown routes
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found', path: url }));
}

// Create and start server
const server = http.createServer(requestHandler);

server.listen(SERVICE_PORT, '0.0.0.0', () => {
    console.log(`[${SERVICE_NAME}] Server running on port ${SERVICE_PORT}`);
    console.log(`[${SERVICE_NAME}] Health check: http://localhost:${SERVICE_PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log(`[${SERVICE_NAME}] Received SIGTERM, shutting down gracefully`);
    server.close(() => {
        console.log(`[${SERVICE_NAME}] Server closed`);
        process.exit(0);
    });
});
