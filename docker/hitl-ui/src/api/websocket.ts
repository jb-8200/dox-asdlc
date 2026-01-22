/**
 * WebSocket API wrapper
 * Provides a convenient interface for WebSocket connections using the wsClient utility
 */

import { wsClient } from '@/utils/websocket';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws';

/**
 * Connect to the WebSocket event stream
 * Should be called once on app initialization
 */
export function connectEventStream(): void {
  wsClient.connect(WS_URL);
}

/**
 * Disconnect from the WebSocket event stream
 * Should be called on app unmount or cleanup
 */
export function disconnectEventStream(): void {
  wsClient.disconnect();
}

/**
 * Subscribe to a specific event type
 *
 * @param eventType - Event type to subscribe to (e.g., "agent:completed")
 * @param handler - Handler function to call when event is received
 * @returns Unsubscribe function
 *
 * @example
 * ```ts
 * const unsubscribe = subscribeToEvent('agent:completed', (data) => {
 *   console.log('Agent completed:', data);
 * });
 *
 * // Later, in cleanup:
 * unsubscribe();
 * ```
 */
export function subscribeToEvent(
  eventType: string,
  handler: (data: unknown) => void
): () => void {
  wsClient.subscribe(eventType, handler);

  // Return unsubscribe function
  return () => {
    wsClient.unsubscribe(eventType, handler);
  };
}

/**
 * Check if connected to WebSocket server
 */
export function isConnected(): boolean {
  return wsClient.isConnected();
}

/**
 * Get current reconnection attempt count
 */
export function getReconnectAttempts(): number {
  return wsClient.getReconnectAttempts();
}

/**
 * Common event types for easy reference
 */
export const EventTypes = {
  // Agent events
  AGENT_STARTED: 'agent:started',
  AGENT_COMPLETED: 'agent:completed',
  AGENT_FAILED: 'agent:failed',
  AGENT_TOOL_CALL: 'agent:tool_call',

  // Gate events
  GATE_CREATED: 'gate:created',
  GATE_DECIDED: 'gate:decided',
  GATE_EXPIRED: 'gate:expired',

  // Artifact events
  ARTIFACT_CREATED: 'artifact:created',
  ARTIFACT_UPDATED: 'artifact:updated',
  ARTIFACT_APPROVED: 'artifact:approved',

  // Session events
  SESSION_STARTED: 'session:started',
  SESSION_COMPLETED: 'session:completed',
  SESSION_FAILED: 'session:failed',

  // System events
  SYSTEM_WARNING: 'system:warning',
  SYSTEM_ERROR: 'system:error',
} as const;
