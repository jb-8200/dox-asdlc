/**
 * Artifact Management API endpoints
 * Handles artifact browsing, detail, history, and provenance
 */

import { apiClient } from './client';
import type {
  ArtifactDetail,
  ArtifactVersion,
  ArtifactProvenance,
  SpecIndex,
  ArtifactsQueryParams,
  ArtifactsResponse,
} from './types';

/**
 * List artifacts with optional filters
 */
export async function listArtifacts(
  params?: ArtifactsQueryParams
): Promise<ArtifactsResponse> {
  const response = await apiClient.get<ArtifactsResponse>('/artifacts', {
    params,
  });
  return response.data;
}

/**
 * Get detailed information for a specific artifact
 */
export async function getArtifactDetail(
  artifactId: string
): Promise<ArtifactDetail> {
  const response = await apiClient.get<ArtifactDetail>(
    `/artifacts/${artifactId}`
  );
  return response.data;
}

/**
 * Get version history for an artifact
 */
export async function getArtifactHistory(
  artifactId: string
): Promise<ArtifactVersion[]> {
  const response = await apiClient.get<ArtifactVersion[]>(
    `/artifacts/${artifactId}/history`
  );
  return response.data;
}

/**
 * Get a specific version of an artifact
 */
export async function getArtifactVersion(
  artifactId: string,
  version: number
): Promise<ArtifactDetail> {
  const response = await apiClient.get<ArtifactDetail>(
    `/artifacts/${artifactId}/versions/${version}`
  );
  return response.data;
}

/**
 * Compare two versions of an artifact
 * Returns a diff string
 */
export async function compareArtifactVersions(
  artifactId: string,
  versionA: number,
  versionB: number
): Promise<string> {
  const response = await apiClient.get<{ diff: string }>(
    `/artifacts/${artifactId}/compare`,
    {
      params: { version_a: versionA, version_b: versionB },
    }
  );
  return response.data.diff;
}

/**
 * Get provenance information for an artifact
 */
export async function getArtifactProvenance(
  artifactId: string
): Promise<ArtifactProvenance> {
  const response = await apiClient.get<ArtifactProvenance>(
    `/artifacts/${artifactId}/provenance`
  );
  return response.data;
}

/**
 * Get the spec index (artifact tree organized by phase)
 */
export async function getSpecIndex(epicId?: string): Promise<SpecIndex> {
  const response = await apiClient.get<SpecIndex>('/artifacts/spec-index', {
    params: epicId ? { epic_id: epicId } : undefined,
  });
  return response.data;
}

/**
 * Download an artifact as a file
 */
export async function downloadArtifact(artifactId: string): Promise<Blob> {
  const response = await apiClient.get(`/artifacts/${artifactId}/download`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Submit an artifact to a gate for approval
 */
export async function submitArtifact(
  artifactId: string,
  gateType: string
): Promise<{ gate_id: string }> {
  const response = await apiClient.post<{ gate_id: string }>(
    `/artifacts/${artifactId}/submit`,
    { gate_type: gateType }
  );
  return response.data;
}

/**
 * Regenerate an artifact with current context
 */
export async function regenerateArtifact(
  artifactId: string
): Promise<{ run_id: string }> {
  const response = await apiClient.post<{ run_id: string }>(
    `/artifacts/${artifactId}/regenerate`
  );
  return response.data;
}

/**
 * View artifact in git (returns git URL)
 */
export async function getArtifactGitUrl(artifactId: string): Promise<string> {
  const response = await apiClient.get<{ url: string }>(
    `/artifacts/${artifactId}/git-url`
  );
  return response.data.url;
}
