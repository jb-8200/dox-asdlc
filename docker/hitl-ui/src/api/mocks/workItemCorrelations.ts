/**
 * Work Item Correlations for Brainflare Graph (P08-F06)
 *
 * Defines relationships between work item features based on:
 * - Direct dependencies (feature depends on another)
 * - Similar patterns (shared technology/architecture)
 * - Contradictions (one deprecates/replaces another)
 *
 * Data Source: .workitems/ design.md dependency sections
 */

import type { GraphNode, GraphEdge } from '../../types/graph';
import { workItemFeatureIdeas, projectColors } from './workItemIdeas';

/**
 * Helper to truncate label to reasonable length
 */
function truncateLabel(content: string, maxWords: number = 6): string {
  const words = content.split(/\s+/);
  if (words.length <= maxWords) return content;
  return words.slice(0, maxWords).join(' ') + '...';
}

/**
 * Convert work item ideas to graph nodes
 */
export const workItemNodes: GraphNode[] = workItemFeatureIdeas.map((idea) => {
  // Extract project code (e.g., "P01" from "workitem-P01-F01")
  const projectMatch = idea.id.match(/P(\d+)/);
  const projectCode = projectMatch ? `P${projectMatch[1].padStart(2, '0')}` : 'P00';

  return {
    id: idea.id,
    label: truncateLabel(idea.content),
    classification: idea.classification,
    labels: idea.labels,
    degree: 0, // Will be calculated after edges are defined
    // Custom properties for styling
    projectCode,
    color: projectColors[projectCode] || '#6b7280',
  };
});

/**
 * Work item feature correlations (edges)
 *
 * Types:
 * - 'related': Direct dependency (source depends on target)
 * - 'similar': Shared pattern or technology
 * - 'contradicts': One replaces or deprecates the other
 */
export const workItemEdges: GraphEdge[] = [
  // ============================================
  // P01 Internal Dependencies
  // ============================================
  {
    id: 'wi-corr-001',
    source: 'workitem-P01-F02',
    target: 'workitem-P01-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-002',
    source: 'workitem-P01-F03',
    target: 'workitem-P01-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-003',
    source: 'workitem-P01-F04',
    target: 'workitem-P01-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-004',
    source: 'workitem-P01-F05',
    target: 'workitem-P01-F04',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-005',
    source: 'workitem-P01-F06',
    target: 'workitem-P01-F04',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-006',
    source: 'workitem-P01-F07',
    target: 'workitem-P01-F04',
    correlationType: 'related',
  },

  // ============================================
  // P01 → P02 Dependencies
  // ============================================
  {
    id: 'wi-corr-007',
    source: 'workitem-P02-F01',
    target: 'workitem-P01-F04',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-008',
    source: 'workitem-P02-F04',
    target: 'workitem-P01-F03',
    correlationType: 'contradicts', // ES replaces ChromaDB
  },
  {
    id: 'wi-corr-009',
    source: 'workitem-P02-F06',
    target: 'workitem-P01-F04',
    correlationType: 'related',
  },

  // ============================================
  // P02 Internal Dependencies
  // ============================================
  {
    id: 'wi-corr-010',
    source: 'workitem-P02-F02',
    target: 'workitem-P02-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-011',
    source: 'workitem-P02-F03',
    target: 'workitem-P02-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-012',
    source: 'workitem-P02-F05',
    target: 'workitem-P02-F04',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-013',
    source: 'workitem-P02-F08',
    target: 'workitem-P02-F07',
    correlationType: 'related',
  },

  // ============================================
  // P02 → P03 Dependencies
  // ============================================
  {
    id: 'wi-corr-014',
    source: 'workitem-P03-F01',
    target: 'workitem-P02-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-015',
    source: 'workitem-P03-F02',
    target: 'workitem-P02-F05',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-016',
    source: 'workitem-P03-F03',
    target: 'workitem-P02-F07',
    correlationType: 'related',
  },

  // ============================================
  // P03 → P04 Dependencies
  // ============================================
  {
    id: 'wi-corr-017',
    source: 'workitem-P04-F01',
    target: 'workitem-P03-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-018',
    source: 'workitem-P04-F01',
    target: 'workitem-P03-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-019',
    source: 'workitem-P04-F02',
    target: 'workitem-P03-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-020',
    source: 'workitem-P04-F03',
    target: 'workitem-P03-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-021',
    source: 'workitem-P04-F03',
    target: 'workitem-P03-F03',
    correlationType: 'related',
  },

  // ============================================
  // P04 Internal (Workflow Sequence)
  // ============================================
  {
    id: 'wi-corr-022',
    source: 'workitem-P04-F02',
    target: 'workitem-P04-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-023',
    source: 'workitem-P04-F03',
    target: 'workitem-P04-F02',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-024',
    source: 'workitem-P04-F04',
    target: 'workitem-P04-F03',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-025',
    source: 'workitem-P04-F05',
    target: 'workitem-P04-F03',
    correlationType: 'similar', // Parallel review is alternative to sequential
  },

  // ============================================
  // P05 Dependencies
  // ============================================
  {
    id: 'wi-corr-026',
    source: 'workitem-P05-F06',
    target: 'workitem-P05-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-027',
    source: 'workitem-P05-F07',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-028',
    source: 'workitem-P05-F08',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-029',
    source: 'workitem-P05-F09',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-030',
    source: 'workitem-P05-F10',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-031',
    source: 'workitem-P05-F11',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-032',
    source: 'workitem-P05-F12',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-033',
    source: 'workitem-P05-F13',
    target: 'workitem-P05-F06',
    correlationType: 'related',
  },

  // ============================================
  // P05 ← P02 Cross-Project Dependencies
  // ============================================
  {
    id: 'wi-corr-034',
    source: 'workitem-P05-F08',
    target: 'workitem-P02-F04',
    correlationType: 'related', // Search UI needs ES
  },
  {
    id: 'wi-corr-035',
    source: 'workitem-P05-F10',
    target: 'workitem-P02-F07',
    correlationType: 'related', // Metrics dashboard needs metrics collection
  },
  {
    id: 'wi-corr-036',
    source: 'workitem-P05-F11',
    target: 'workitem-P08-F01',
    correlationType: 'related', // Ideation uses Ideas repository
  },

  // ============================================
  // P06 Dependencies
  // ============================================
  {
    id: 'wi-corr-037',
    source: 'workitem-P06-F02',
    target: 'workitem-P06-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-038',
    source: 'workitem-P06-F03',
    target: 'workitem-P06-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-039',
    source: 'workitem-P06-F04',
    target: 'workitem-P06-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-040',
    source: 'workitem-P06-F05',
    target: 'workitem-P06-F04',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-041',
    source: 'workitem-P06-F06',
    target: 'workitem-P06-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-042',
    source: 'workitem-P06-F07',
    target: 'workitem-P06-F06',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-043',
    source: 'workitem-P06-F08',
    target: 'workitem-P06-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-044',
    source: 'workitem-P06-F09',
    target: 'workitem-P06-F06',
    correlationType: 'related',
  },

  // ============================================
  // P06 ← P05 Cross-Project (Metrics)
  // ============================================
  {
    id: 'wi-corr-045',
    source: 'workitem-P05-F10',
    target: 'workitem-P06-F06',
    correlationType: 'related', // Metrics dashboard needs VictoriaMetrics
  },

  // ============================================
  // P08 Dependencies (Ideas Lifecycle)
  // ============================================
  {
    id: 'wi-corr-046',
    source: 'workitem-P08-F01',
    target: 'workitem-P02-F04',
    correlationType: 'related', // Ideas needs Elasticsearch
  },
  {
    id: 'wi-corr-047',
    source: 'workitem-P08-F02',
    target: 'workitem-P08-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-048',
    source: 'workitem-P08-F03',
    target: 'workitem-P08-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-049',
    source: 'workitem-P08-F04',
    target: 'workitem-P08-F03',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-050',
    source: 'workitem-P08-F05',
    target: 'workitem-P08-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-051',
    source: 'workitem-P08-F06',
    target: 'workitem-P08-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-052',
    source: 'workitem-P08-F07',
    target: 'workitem-P08-F06',
    correlationType: 'related',
  },

  // ============================================
  // P10 Dependencies
  // ============================================
  {
    id: 'wi-corr-053',
    source: 'workitem-P10-F01',
    target: 'workitem-P05-F06',
    correlationType: 'related', // Canvas in SPA
  },
  {
    id: 'wi-corr-054',
    source: 'workitem-P10-F02',
    target: 'workitem-P10-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-055',
    source: 'workitem-P10-F03',
    target: 'workitem-P10-F01',
    correlationType: 'related',
  },
  {
    id: 'wi-corr-056',
    source: 'workitem-P10-F03',
    target: 'workitem-P01-F04',
    correlationType: 'related', // Draft history uses Redis
  },

  // ============================================
  // Similar Pattern Correlations
  // ============================================
  // Visualization patterns
  {
    id: 'wi-corr-057',
    source: 'workitem-P08-F06',
    target: 'workitem-P10-F01',
    correlationType: 'similar', // Both are canvas visualizations
  },
  // Dashboard patterns
  {
    id: 'wi-corr-058',
    source: 'workitem-P05-F08',
    target: 'workitem-P08-F04',
    correlationType: 'similar', // Both do search/correlation
  },
  {
    id: 'wi-corr-059',
    source: 'workitem-P05-F10',
    target: 'workitem-P05-F08',
    correlationType: 'similar', // Both are dashboards
  },
  // MCP integration patterns
  {
    id: 'wi-corr-060',
    source: 'workitem-P06-F08',
    target: 'workitem-P02-F04',
    correlationType: 'similar', // Both involve MCP integration
  },
  // Agent patterns
  {
    id: 'wi-corr-061',
    source: 'workitem-P04-F05',
    target: 'workitem-P03-F01',
    correlationType: 'similar', // Both are agent execution patterns
  },

  // ============================================
  // Cross-pollination with existing user ideas
  // ============================================
  // User idea about graph visualization relates to snowflake
  {
    id: 'wi-corr-062',
    source: 'idea-006', // Graph visualization idea
    target: 'workitem-P08-F06',
    correlationType: 'similar',
  },
  // User idea about Redis caching relates to Redis coordination
  {
    id: 'wi-corr-063',
    source: 'idea-002', // Redis caching idea
    target: 'workitem-P01-F04',
    correlationType: 'similar',
  },
  // User idea about Slack integration relates to P08-F02
  {
    id: 'wi-corr-064',
    source: 'idea-004', // Slack integration idea
    target: 'workitem-P08-F02',
    correlationType: 'similar',
  },
  // User idea about notifications relates to P01-F05
  {
    id: 'wi-corr-065',
    source: 'idea-003', // Notification system idea
    target: 'workitem-P01-F05',
    correlationType: 'similar',
  },

  // ============================================
  // Deprecation Correlations
  // ============================================
  {
    id: 'wi-corr-066',
    source: 'workitem-P06-F03',
    target: 'workitem-P01-F03',
    correlationType: 'similar', // Both ChromaDB related, both deprecated
  },
];

/**
 * Calculate and update node degrees based on edges
 */
function calculateDegrees(nodes: GraphNode[], edges: GraphEdge[]): void {
  // Reset degrees
  nodes.forEach((node) => (node.degree = 0));

  // Count edges for each node
  edges.forEach((edge) => {
    const sourceId = typeof edge.source === 'string' ? edge.source : (edge.source as GraphNode).id;
    const targetId = typeof edge.target === 'string' ? edge.target : (edge.target as GraphNode).id;

    const sourceNode = nodes.find((n) => n.id === sourceId);
    const targetNode = nodes.find((n) => n.id === targetId);

    if (sourceNode) sourceNode.degree++;
    if (targetNode) targetNode.degree++;
  });
}

// Calculate degrees for work item nodes
calculateDegrees(workItemNodes, workItemEdges);

/**
 * Get work item graph data to merge with existing graph
 */
export function getWorkItemGraphData(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  return {
    nodes: workItemNodes.map((n) => ({ ...n })),
    edges: workItemEdges.map((e) => ({ ...e })),
  };
}
