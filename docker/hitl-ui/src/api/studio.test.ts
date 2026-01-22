import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from './client';
import {
  sendChatMessage,
  getWorkingOutline,
  saveDraftOutline,
  generatePRDPreview,
  queryContextPack,
  addContextToSession,
  submitArtifactToGate,
  getChatHistory,
} from './studio';
import type {
  StudioChatRequest,
  StudioChatResponse,
  WorkingOutline,
  ContextPack,
} from './types';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Studio API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('sendChatMessage', () => {
    it('should send chat message and receive response', async () => {
      const request: StudioChatRequest = {
        session_id: 'session-123',
        message: 'Create a PRD for user authentication',
      };

      const mockResponse: StudioChatResponse = {
        message: {
          id: 'msg-1',
          role: 'assistant',
          content: 'Sure, let me help you with that...',
          timestamp: '2026-01-23T00:00:00Z',
        },
        outline_update: {
          sections: [
            { name: 'Overview', status: 'in_progress' },
          ],
          completeness: 10,
        },
      };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await sendChatMessage(request);

      expect(apiClient.post).toHaveBeenCalledWith('/studio/chat', request);
      expect(result).toEqual(mockResponse);
      expect(result.message.role).toBe('assistant');
    });

    it('should handle chat with context pack', async () => {
      const contextPack: ContextPack = {
        files: [
          { path: 'src/auth.ts', relevance_score: 0.95, tokens: 500 },
        ],
        total_tokens: 500,
        cost_estimate_usd: 0.01,
      };

      const request: StudioChatRequest = {
        session_id: 'session-123',
        message: 'Analyze this code',
        context_pack: contextPack,
      };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { message: { id: 'msg-1', role: 'assistant', content: 'Analysis...', timestamp: '2026-01-23T00:00:00Z' } },
      });

      await sendChatMessage(request);

      expect(apiClient.post).toHaveBeenCalledWith('/studio/chat', request);
    });
  });

  describe('getWorkingOutline', () => {
    it('should fetch working outline for session', async () => {
      const mockOutline: WorkingOutline = {
        sections: [
          { name: 'Overview', status: 'complete', content: 'Overview content' },
          { name: 'Requirements', status: 'in_progress' },
          { name: 'Scope', status: 'pending' },
        ],
        completeness: 40,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockOutline,
      });

      const result = await getWorkingOutline('session-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/studio/sessions/session-123/outline'
      );
      expect(result).toEqual(mockOutline);
      expect(result.sections).toHaveLength(3);
      expect(result.completeness).toBe(40);
    });
  });

  describe('saveDraftOutline', () => {
    it('should save draft outline', async () => {
      const outline: WorkingOutline = {
        sections: [{ name: 'Overview', status: 'complete' }],
        completeness: 20,
      };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: {},
      });

      await saveDraftOutline('session-123', outline);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/studio/sessions/session-123/outline/draft',
        outline
      );
    });
  });

  describe('generatePRDPreview', () => {
    it('should generate PRD preview', async () => {
      const mockContent = '# Product Requirements Document\n\n## Overview\n...';

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { content: mockContent },
      });

      const result = await generatePRDPreview('session-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/studio/sessions/session-123/prd-preview'
      );
      expect(result).toBe(mockContent);
      expect(result).toContain('Product Requirements Document');
    });
  });

  describe('queryContextPack', () => {
    it('should query for context pack', async () => {
      const mockContextPack: ContextPack = {
        files: [
          { path: 'src/auth.ts', relevance_score: 0.95, tokens: 500 },
          { path: 'src/user.ts', relevance_score: 0.85, tokens: 300 },
        ],
        total_tokens: 800,
        cost_estimate_usd: 0.016,
      };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockContextPack,
      });

      const result = await queryContextPack('session-123', 'authentication');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/studio/sessions/session-123/context-query',
        { query: 'authentication' }
      );
      expect(result).toEqual(mockContextPack);
      expect(result.files).toHaveLength(2);
      expect(result.total_tokens).toBe(800);
    });
  });

  describe('addContextToSession', () => {
    it('should add context pack to session', async () => {
      const contextPack: ContextPack = {
        files: [{ path: 'src/auth.ts', relevance_score: 0.95, tokens: 500 }],
        total_tokens: 500,
        cost_estimate_usd: 0.01,
      };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: {},
      });

      await addContextToSession('session-123', contextPack);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/studio/sessions/session-123/context',
        contextPack
      );
    });
  });

  describe('submitArtifactToGate', () => {
    it('should submit artifact to gate', async () => {
      const mockResponse = { gate_id: 'gate-456' };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await submitArtifactToGate(
        'session-123',
        'artifact-789',
        'prd_review'
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        '/studio/sessions/session-123/artifacts/artifact-789/submit',
        { gate_type: 'prd_review' }
      );
      expect(result).toEqual(mockResponse);
      expect(result.gate_id).toBe('gate-456');
    });
  });

  describe('getChatHistory', () => {
    it('should fetch chat history', async () => {
      const mockHistory: StudioChatResponse[] = [
        {
          message: {
            id: 'msg-1',
            role: 'user',
            content: 'Hello',
            timestamp: '2026-01-23T00:00:00Z',
          },
        },
        {
          message: {
            id: 'msg-2',
            role: 'assistant',
            content: 'Hi! How can I help?',
            timestamp: '2026-01-23T00:00:01Z',
          },
        },
      ];

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockHistory,
      });

      const result = await getChatHistory('session-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/studio/sessions/session-123/history'
      );
      expect(result).toEqual(mockHistory);
      expect(result).toHaveLength(2);
    });
  });
});
