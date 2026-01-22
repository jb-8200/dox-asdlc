import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from './client';
import {
  listArtifacts,
  getArtifactDetail,
  getArtifactHistory,
  getArtifactVersion,
  compareArtifactVersions,
  getArtifactProvenance,
  getSpecIndex,
  downloadArtifact,
  submitArtifact,
  regenerateArtifact,
  getArtifactGitUrl,
} from './artifacts';
import type {
  ArtifactDetail,
  ArtifactVersion,
  ArtifactProvenance,
  SpecIndex,
} from './types';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Artifacts API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listArtifacts', () => {
    it('should fetch artifacts list without filters', async () => {
      const mockResponse = {
        artifacts: [
          {
            id: 'artifact-123',
            name: 'PRD.md',
            type: 'file',
            status: 'approved',
            created_at: '2026-01-23T00:00:00Z',
            created_by: 'prd-agent',
            content: '# PRD',
            content_type: 'text/markdown',
            size_bytes: 1024,
          } as ArtifactDetail,
        ],
        total: 1,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await listArtifacts();

      expect(apiClient.get).toHaveBeenCalledWith('/artifacts', {
        params: undefined,
      });
      expect(result).toEqual(mockResponse);
      expect(result.artifacts).toHaveLength(1);
    });

    it('should fetch artifacts list with filters', async () => {
      const mockResponse = { artifacts: [], total: 0 };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const params = {
        epic_id: 'epic-123',
        type: 'file' as const,
        status: 'approved' as const,
      };

      await listArtifacts(params);

      expect(apiClient.get).toHaveBeenCalledWith('/artifacts', { params });
    });
  });

  describe('getArtifactDetail', () => {
    it('should fetch artifact detail', async () => {
      const mockDetail: ArtifactDetail = {
        id: 'artifact-123',
        name: 'PRD.md',
        type: 'file',
        status: 'approved',
        epic_id: 'epic-123',
        created_at: '2026-01-23T00:00:00Z',
        created_by: 'prd-agent',
        approved_at: '2026-01-23T01:00:00Z',
        approved_by: 'human',
        sha: 'abc123',
        content: '# PRD\n\n## Overview',
        content_type: 'text/markdown',
        size_bytes: 2048,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockDetail,
      });

      const result = await getArtifactDetail('artifact-123');

      expect(apiClient.get).toHaveBeenCalledWith('/artifacts/artifact-123');
      expect(result).toEqual(mockDetail);
      expect(result.status).toBe('approved');
    });
  });

  describe('getArtifactHistory', () => {
    it('should fetch artifact version history', async () => {
      const mockHistory: ArtifactVersion[] = [
        {
          version: 2,
          timestamp: '2026-01-23T01:00:00Z',
          author: 'prd-agent',
          sha: 'def456',
          changes_summary: 'Updated requirements section',
        },
        {
          version: 1,
          timestamp: '2026-01-23T00:00:00Z',
          author: 'prd-agent',
          sha: 'abc123',
          changes_summary: 'Initial version',
        },
      ];

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockHistory,
      });

      const result = await getArtifactHistory('artifact-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/history'
      );
      expect(result).toEqual(mockHistory);
      expect(result).toHaveLength(2);
    });
  });

  describe('getArtifactVersion', () => {
    it('should fetch specific artifact version', async () => {
      const mockVersion: ArtifactDetail = {
        id: 'artifact-123',
        name: 'PRD.md',
        type: 'file',
        status: 'draft',
        created_at: '2026-01-23T00:00:00Z',
        created_by: 'prd-agent',
        sha: 'abc123',
        content: '# PRD (v1)',
        content_type: 'text/markdown',
        size_bytes: 1024,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockVersion,
      });

      const result = await getArtifactVersion('artifact-123', 1);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/versions/1'
      );
      expect(result).toEqual(mockVersion);
    });
  });

  describe('compareArtifactVersions', () => {
    it('should compare two versions and return diff', async () => {
      const mockDiff = `--- a/PRD.md
+++ b/PRD.md
@@ -1,1 +1,2 @@
 # PRD
+## Overview`;

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { diff: mockDiff },
      });

      const result = await compareArtifactVersions('artifact-123', 1, 2);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/compare',
        { params: { version_a: 1, version_b: 2 } }
      );
      expect(result).toBe(mockDiff);
      expect(result).toContain('--- a/PRD.md');
    });
  });

  describe('getArtifactProvenance', () => {
    it('should fetch artifact provenance', async () => {
      const mockProvenance: ArtifactProvenance = {
        producing_run_id: 'run-123',
        input_artifacts: [
          { path: 'context.txt', type: 'file' },
        ],
        approving_gate_id: 'gate-456',
        approval_info: {
          approved_by: 'human',
          approved_at: '2026-01-23T01:00:00Z',
          feedback: 'Looks good',
        },
        feedback: ['Great work', 'Clear requirements'],
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockProvenance,
      });

      const result = await getArtifactProvenance('artifact-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/provenance'
      );
      expect(result).toEqual(mockProvenance);
      expect(result.producing_run_id).toBe('run-123');
    });
  });

  describe('getSpecIndex', () => {
    it('should fetch spec index without epic filter', async () => {
      const mockIndex: SpecIndex = {
        discovery: {
          artifacts: [
            { id: 'prd-1', name: 'PRD.md', status: 'approved' },
          ],
          progress: { complete: 1, in_progress: 0, pending: 0, total: 1 },
        },
        design: {
          artifacts: [],
          progress: { complete: 0, in_progress: 0, pending: 1, total: 1 },
        },
        development: {
          artifacts: [],
          progress: { complete: 0, in_progress: 0, pending: 0, total: 0 },
        },
        validation: {
          artifacts: [],
          progress: { complete: 0, in_progress: 0, pending: 0, total: 0 },
        },
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockIndex,
      });

      const result = await getSpecIndex();

      expect(apiClient.get).toHaveBeenCalledWith('/artifacts/spec-index', {
        params: undefined,
      });
      expect(result).toEqual(mockIndex);
      expect(result.discovery.artifacts).toHaveLength(1);
    });

    it('should fetch spec index with epic filter', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: {} as SpecIndex,
      });

      await getSpecIndex('epic-123');

      expect(apiClient.get).toHaveBeenCalledWith('/artifacts/spec-index', {
        params: { epic_id: 'epic-123' },
      });
    });
  });

  describe('downloadArtifact', () => {
    it('should download artifact as blob', async () => {
      const mockBlob = new Blob(['# PRD'], { type: 'text/markdown' });

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockBlob,
      });

      const result = await downloadArtifact('artifact-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/download',
        { responseType: 'blob' }
      );
      expect(result).toBeInstanceOf(Blob);
    });
  });

  describe('submitArtifact', () => {
    it('should submit artifact to gate', async () => {
      const mockResponse = { gate_id: 'gate-789' };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await submitArtifact('artifact-123', 'prd_review');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/artifacts/artifact-123/submit',
        { gate_type: 'prd_review' }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('regenerateArtifact', () => {
    it('should trigger artifact regeneration', async () => {
      const mockResponse = { run_id: 'run-456' };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await regenerateArtifact('artifact-123');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/artifacts/artifact-123/regenerate'
      );
      expect(result).toEqual(mockResponse);
      expect(result.run_id).toBe('run-456');
    });
  });

  describe('getArtifactGitUrl', () => {
    it('should get artifact git URL', async () => {
      const mockUrl = 'https://github.com/org/repo/blob/main/artifacts/PRD.md';

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { url: mockUrl },
      });

      const result = await getArtifactGitUrl('artifact-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/artifacts/artifact-123/git-url'
      );
      expect(result).toBe(mockUrl);
    });
  });
});
