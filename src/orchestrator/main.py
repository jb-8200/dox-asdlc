"""aSDLC Orchestrator Service Entry Point.

Runs the orchestrator/governance service with health endpoints.
Full implementation in P02 (Orchestration Core).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Any

from src.core.config import get_config
from src.infrastructure.health import get_health_checker, HealthChecker
from src.infrastructure.redis_streams import initialize_consumer_groups

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""

    health_checker: HealthChecker = None

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use Python logging."""
        logger.debug(f"HTTP: {format % args}")

    def _send_json_response(self, data: dict, status: int = 200) -> None:
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/health/live":
            self._handle_liveness()
        elif self.path == "/health/ready":
            self._handle_readiness()
        else:
            self._send_json_response({"error": "Not Found"}, 404)

    def _handle_health(self) -> None:
        """Handle /health endpoint."""
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                self.health_checker.check_health()
            )
            self._send_json_response(
                response.to_dict(), response.http_status_code()
            )
        finally:
            loop.close()

    def _handle_liveness(self) -> None:
        """Handle /health/live endpoint."""
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                self.health_checker.check_liveness()
            )
            self._send_json_response(
                response.to_dict(), response.http_status_code()
            )
        finally:
            loop.close()

    def _handle_readiness(self) -> None:
        """Handle /health/ready endpoint."""
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                self.health_checker.check_health(include_dependencies=True)
            )
            self._send_json_response(
                response.to_dict(), response.http_status_code()
            )
        finally:
            loop.close()


async def initialize_infrastructure() -> None:
    """Initialize Redis streams and consumer groups."""
    logger.info("Initializing infrastructure...")
    try:
        results = await initialize_consumer_groups()
        for group, created in results.items():
            status = "created" if created else "exists"
            logger.info(f"Consumer group '{group}': {status}")
    except Exception as e:
        logger.error(f"Failed to initialize infrastructure: {e}")
        raise


def run_health_server(host: str, port: int, checker: HealthChecker) -> HTTPServer:
    """Start the health check HTTP server."""
    HealthHandler.health_checker = checker
    server = HTTPServer((host, port), HealthHandler)
    logger.info(f"Health server running on {host}:{port}")
    return server


def main() -> None:
    """Main entry point for orchestrator service."""
    logger.info("Starting aSDLC Orchestrator Service")

    try:
        config = get_config()
        service_name = config.service.name
        port = config.service.port
        host = config.service.host
    except Exception as e:
        logger.warning(f"Config error, using defaults: {e}")
        service_name = os.getenv("SERVICE_NAME", "orchestrator")
        port = int(os.getenv("SERVICE_PORT", "8080"))
        host = os.getenv("SERVICE_HOST", "0.0.0.0")

    # Initialize health checker
    health_checker = get_health_checker(service_name)

    # Initialize infrastructure
    try:
        asyncio.get_event_loop().run_until_complete(initialize_infrastructure())
    except Exception as e:
        logger.warning(f"Infrastructure init failed (non-fatal): {e}")

    # Start health server
    server = run_health_server(host, port, health_checker)

    # Handle shutdown signals
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        server.shutdown()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info(f"Orchestrator service ready on {host}:{port}")
    logger.info(f"Health check: http://localhost:{port}/health")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Orchestrator service stopped")


if __name__ == "__main__":
    main()
