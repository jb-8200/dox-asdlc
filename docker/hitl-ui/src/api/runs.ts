/**
 * Agent Cockpit API endpoints
 * Handles agent run queries, KPI metrics, and workflow graph data
 */

import { apiClient } from './client';
import type {
  AgentRunDetail,
  KPIMetrics,
  WorkflowGraph,
  GitState,
  RunsQueryParams,
  RunsResponse,
} from './types';

/**
 * List agent runs with optional filters
 */
export async function listRuns(
  params?: RunsQueryParams
): Promise<RunsResponse> {
  const response = await apiClient.get<RunsResponse>('/runs', { params });
  return response.data;
}

/**
 * Get detailed information for a specific run
 */
export async function getRunDetail(runId: string): Promise<AgentRunDetail> {
  const response = await apiClient.get<AgentRunDetail>(`/runs/${runId}`);
  return response.data;
}

/**
 * Get KPI metrics for the cockpit dashboard
 */
export async function getKPIMetrics(): Promise<KPIMetrics> {
  const response = await apiClient.get<KPIMetrics>('/cockpit/kpis');
  return response.data;
}

/**
 * Get workflow graph data (Sankey/node graph)
 */
export async function getWorkflowGraph(): Promise<WorkflowGraph> {
  const response = await apiClient.get<WorkflowGraph>('/cockpit/workflow');
  return response.data;
}

/**
 * Get git state for all environments
 */
export async function getGitStates(): Promise<GitState[]> {
  const response = await apiClient.get<GitState[]>('/cockpit/git-states');
  return response.data;
}

/**
 * Force sync git state for a specific environment
 */
export async function forceGitSync(environment: string): Promise<void> {
  await apiClient.post(`/cockpit/git-states/${environment}/sync`);
}

/**
 * Rerun a completed or failed run
 */
export async function rerunAgent(runId: string): Promise<{ run_id: string }> {
  const response = await apiClient.post<{ run_id: string }>(
    `/runs/${runId}/rerun`
  );
  return response.data;
}

/**
 * Export run data as JSON
 */
export async function exportRun(runId: string): Promise<Blob> {
  const response = await apiClient.get(`/runs/${runId}/export`, {
    responseType: 'blob',
  });
  return response.data;
}
