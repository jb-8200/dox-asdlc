import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from './client';
import {
  listRuns,
  getRunDetail,
  getKPIMetrics,
  getWorkflowGraph,
  getGitStates,
  forceGitSync,
  rerunAgent,
  exportRun,
} from './runs';
import type {
  AgentRun,
  AgentRunDetail,
  KPIMetrics,
  WorkflowGraph,
  GitState,
} from './types';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Runs API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listRuns', () => {
    it('should fetch runs list without filters', async () => {
      const mockResponse = {
        runs: [
          {
            run_id: 'run-123',
            agent_type: 'coder',
            cluster: 'development',
            status: 'completed',
            model: 'sonnet',
            started_at: '2026-01-23T00:00:00Z',
            tokens_used: 1000,
            cost_usd: 0.05,
            input_artifacts: 2,
            output_artifacts: 1,
          } as AgentRun,
        ],
        total: 1,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await listRuns();

      expect(apiClient.get).toHaveBeenCalledWith('/runs', { params: undefined });
      expect(result).toEqual(mockResponse);
      expect(result.runs).toHaveLength(1);
      expect(result.runs[0].run_id).toBe('run-123');
    });

    it('should fetch runs list with filters', async () => {
      const mockResponse = { runs: [], total: 0 };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const params = {
        cluster: 'development',
        status: 'completed' as const,
        limit: 50,
      };

      await listRuns(params);

      expect(apiClient.get).toHaveBeenCalledWith('/runs', { params });
    });
  });

  describe('getRunDetail', () => {
    it('should fetch detailed run information', async () => {
      const mockDetail: AgentRunDetail = {
        run_id: 'run-123',
        agent_type: 'coder',
        cluster: 'development',
        status: 'completed',
        model: 'sonnet',
        started_at: '2026-01-23T00:00:00Z',
        tokens_used: 1000,
        cost_usd: 0.05,
        input_artifacts: 2,
        output_artifacts: 1,
        timeline: [
          {
            id: 'event-1',
            timestamp: '2026-01-23T00:00:00Z',
            event_type: 'start',
            description: 'Run started',
          },
        ],
        inputs: {
          artifacts: [],
          configuration: {},
        },
        outputs: {
          artifacts: [],
        },
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockDetail,
      });

      const result = await getRunDetail('run-123');

      expect(apiClient.get).toHaveBeenCalledWith('/runs/run-123');
      expect(result).toEqual(mockDetail);
      expect(result.timeline).toHaveLength(1);
    });
  });

  describe('getKPIMetrics', () => {
    it('should fetch KPI metrics', async () => {
      const mockKPIs: KPIMetrics = {
        active_runs: 5,
        completed_today: 20,
        success_rate: 0.95,
        avg_duration_ms: 120000,
        total_cost_usd: 5.5,
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockKPIs,
      });

      const result = await getKPIMetrics();

      expect(apiClient.get).toHaveBeenCalledWith('/cockpit/kpis');
      expect(result).toEqual(mockKPIs);
      expect(result.success_rate).toBe(0.95);
    });
  });

  describe('getWorkflowGraph', () => {
    it('should fetch workflow graph data', async () => {
      const mockGraph: WorkflowGraph = {
        nodes: [
          {
            id: 'discovery',
            label: 'Discovery',
            type: 'cluster',
            metrics: { runs: 10, success_rate: 0.9 },
          },
        ],
        edges: [{ from: 'discovery', to: 'design', count: 8 }],
      };

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockGraph,
      });

      const result = await getWorkflowGraph();

      expect(apiClient.get).toHaveBeenCalledWith('/cockpit/workflow');
      expect(result).toEqual(mockGraph);
      expect(result.nodes).toHaveLength(1);
      expect(result.edges).toHaveLength(1);
    });
  });

  describe('getGitStates', () => {
    it('should fetch git states for all environments', async () => {
      const mockStates: GitState[] = [
        {
          environment: 'dev',
          branch: 'main',
          sha: 'abc123',
          pending_commits: 2,
          recent_commits: [
            {
              sha: 'abc123',
              message: 'Test commit',
              author: 'dev',
              timestamp: '2026-01-23T00:00:00Z',
            },
          ],
          drift: false,
        },
      ];

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockStates,
      });

      const result = await getGitStates();

      expect(apiClient.get).toHaveBeenCalledWith('/cockpit/git-states');
      expect(result).toEqual(mockStates);
      expect(result[0].environment).toBe('dev');
    });
  });

  describe('forceGitSync', () => {
    it('should trigger git sync for environment', async () => {
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: {},
      });

      await forceGitSync('dev');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/cockpit/git-states/dev/sync'
      );
    });
  });

  describe('rerunAgent', () => {
    it('should trigger agent rerun', async () => {
      const mockResponse = { run_id: 'run-456' };

      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockResponse,
      });

      const result = await rerunAgent('run-123');

      expect(apiClient.post).toHaveBeenCalledWith('/runs/run-123/rerun');
      expect(result).toEqual(mockResponse);
      expect(result.run_id).toBe('run-456');
    });
  });

  describe('exportRun', () => {
    it('should export run data as blob', async () => {
      const mockBlob = new Blob(['{}'], { type: 'application/json' });

      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: mockBlob,
      });

      const result = await exportRun('run-123');

      expect(apiClient.get).toHaveBeenCalledWith('/runs/run-123/export', {
        responseType: 'blob',
      });
      expect(result).toBeInstanceOf(Blob);
    });
  });
});
