/**
 * Discovery Studio API endpoints
 * Handles chat interactions, outline management, and context queries
 */

import { apiClient } from './client';
import type {
  StudioChatRequest,
  StudioChatResponse,
  WorkingOutline,
  ContextPack,
} from './types';

/**
 * Send a chat message and receive response
 * Supports streaming responses via Server-Sent Events (SSE)
 */
export async function sendChatMessage(
  request: StudioChatRequest
): Promise<StudioChatResponse> {
  const response = await apiClient.post<StudioChatResponse>(
    '/studio/chat',
    request
  );
  return response.data;
}

/**
 * Get the current working outline for a session
 */
export async function getWorkingOutline(
  sessionId: string
): Promise<WorkingOutline> {
  const response = await apiClient.get<WorkingOutline>(
    `/studio/sessions/${sessionId}/outline`
  );
  return response.data;
}

/**
 * Save a draft of the current working outline
 */
export async function saveDraftOutline(
  sessionId: string,
  outline: WorkingOutline
): Promise<void> {
  await apiClient.post(`/studio/sessions/${sessionId}/outline/draft`, outline);
}

/**
 * Generate a preview of the PRD based on current outline
 */
export async function generatePRDPreview(sessionId: string): Promise<string> {
  const response = await apiClient.get<{ content: string }>(
    `/studio/sessions/${sessionId}/prd-preview`
  );
  return response.data.content;
}

/**
 * Query for context pack based on user input
 * Returns relevant files with relevance scores and token counts
 */
export async function queryContextPack(
  sessionId: string,
  query: string
): Promise<ContextPack> {
  const response = await apiClient.post<ContextPack>(
    `/studio/sessions/${sessionId}/context-query`,
    { query }
  );
  return response.data;
}

/**
 * Add a context pack to the session
 */
export async function addContextToSession(
  sessionId: string,
  contextPack: ContextPack
): Promise<void> {
  await apiClient.post(
    `/studio/sessions/${sessionId}/context`,
    contextPack
  );
}

/**
 * Submit an artifact from studio for gate approval
 */
export async function submitArtifactToGate(
  sessionId: string,
  artifactId: string,
  gateType: string
): Promise<{ gate_id: string }> {
  const response = await apiClient.post<{ gate_id: string }>(
    `/studio/sessions/${sessionId}/artifacts/${artifactId}/submit`,
    { gate_type: gateType }
  );
  return response.data;
}

/**
 * Get chat history for a session
 */
export async function getChatHistory(
  sessionId: string
): Promise<StudioChatResponse[]> {
  const response = await apiClient.get<StudioChatResponse[]>(
    `/studio/sessions/${sessionId}/history`
  );
  return response.data;
}
