import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock must be hoisted - use factory that returns fresh mocks
vi.mock('@/utils/websocket', () => ({
  wsClient: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    isConnected: vi.fn(),
    getReconnectAttempts: vi.fn(),
  },
}));

// Import after mock setup
import {
  connectEventStream,
  disconnectEventStream,
  subscribeToEvent,
  isConnected,
  getReconnectAttempts,
  EventTypes,
} from './websocket';
import { wsClient } from '@/utils/websocket';

// Cast for type safety in tests
const mockWsClient = wsClient as {
  connect: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  subscribe: ReturnType<typeof vi.fn>;
  unsubscribe: ReturnType<typeof vi.fn>;
  isConnected: ReturnType<typeof vi.fn>;
  getReconnectAttempts: ReturnType<typeof vi.fn>;
};

describe('WebSocket API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('connectEventStream', () => {
    it('should connect to WebSocket using configured URL', () => {
      connectEventStream();

      expect(mockWsClient.connect).toHaveBeenCalledWith(
        expect.stringContaining('ws://')
      );
    });
  });

  describe('disconnectEventStream', () => {
    it('should disconnect from WebSocket', () => {
      disconnectEventStream();

      expect(mockWsClient.disconnect).toHaveBeenCalled();
    });
  });

  describe('subscribeToEvent', () => {
    it('should subscribe to event and return unsubscribe function', () => {
      const handler = vi.fn();

      const unsubscribe = subscribeToEvent('agent:completed', handler);

      expect(mockWsClient.subscribe).toHaveBeenCalledWith('agent:completed', handler);
      expect(typeof unsubscribe).toBe('function');
    });

    it('should unsubscribe when calling returned function', () => {
      const handler = vi.fn();

      const unsubscribe = subscribeToEvent('agent:completed', handler);
      unsubscribe();

      expect(mockWsClient.unsubscribe).toHaveBeenCalledWith(
        'agent:completed',
        handler
      );
    });

    it('should handle multiple subscriptions', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      subscribeToEvent('agent:started', handler1);
      subscribeToEvent('agent:completed', handler2);

      expect(mockWsClient.subscribe).toHaveBeenCalledTimes(2);
      expect(mockWsClient.subscribe).toHaveBeenCalledWith('agent:started', handler1);
      expect(mockWsClient.subscribe).toHaveBeenCalledWith(
        'agent:completed',
        handler2
      );
    });
  });

  describe('isConnected', () => {
    it('should return true when connected', () => {
      mockWsClient.isConnected.mockReturnValue(true);

      const result = isConnected();

      expect(mockWsClient.isConnected).toHaveBeenCalled();
      expect(result).toBe(true);
    });

    it('should return false when disconnected', () => {
      mockWsClient.isConnected.mockReturnValue(false);

      const result = isConnected();

      expect(result).toBe(false);
    });
  });

  describe('getReconnectAttempts', () => {
    it('should return current reconnect attempt count', () => {
      mockWsClient.getReconnectAttempts.mockReturnValue(3);

      const result = getReconnectAttempts();

      expect(mockWsClient.getReconnectAttempts).toHaveBeenCalled();
      expect(result).toBe(3);
    });

    it('should return 0 when not reconnecting', () => {
      mockWsClient.getReconnectAttempts.mockReturnValue(0);

      const result = getReconnectAttempts();

      expect(result).toBe(0);
    });
  });

  describe('EventTypes', () => {
    it('should export common event type constants', () => {
      expect(EventTypes.AGENT_STARTED).toBe('agent:started');
      expect(EventTypes.AGENT_COMPLETED).toBe('agent:completed');
      expect(EventTypes.AGENT_FAILED).toBe('agent:failed');
      expect(EventTypes.AGENT_TOOL_CALL).toBe('agent:tool_call');

      expect(EventTypes.GATE_CREATED).toBe('gate:created');
      expect(EventTypes.GATE_DECIDED).toBe('gate:decided');
      expect(EventTypes.GATE_EXPIRED).toBe('gate:expired');

      expect(EventTypes.ARTIFACT_CREATED).toBe('artifact:created');
      expect(EventTypes.ARTIFACT_UPDATED).toBe('artifact:updated');
      expect(EventTypes.ARTIFACT_APPROVED).toBe('artifact:approved');

      expect(EventTypes.SESSION_STARTED).toBe('session:started');
      expect(EventTypes.SESSION_COMPLETED).toBe('session:completed');
      expect(EventTypes.SESSION_FAILED).toBe('session:failed');

      expect(EventTypes.SYSTEM_WARNING).toBe('system:warning');
      expect(EventTypes.SYSTEM_ERROR).toBe('system:error');
    });

    it('should allow using EventTypes in subscriptions', () => {
      const handler = vi.fn();

      subscribeToEvent(EventTypes.AGENT_COMPLETED, handler);

      expect(mockWsClient.subscribe).toHaveBeenCalledWith(
        'agent:completed',
        handler
      );
    });
  });
});
