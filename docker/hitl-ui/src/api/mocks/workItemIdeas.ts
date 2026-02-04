/**
 * Work Items Data Migration for Brainflare Graph (P08-F06)
 *
 * Distilled ideas from .workitems/ features and tasks.
 * Each idea is summarized to max ~25 words capturing the "what" and "why".
 *
 * Data Source: 57 features from P01-P10 projects
 * Target: Existing Idea model + GraphEdge correlations
 */

import type { Idea } from '../../types/ideas';

/**
 * Project color coding for graph visualization
 */
export const projectColors: Record<string, string> = {
  P01: '#ef4444', // Red - Infrastructure Foundation
  P02: '#f97316', // Orange - Orchestration & State
  P03: '#eab308', // Yellow - Agent Infrastructure
  P04: '#22c55e', // Green - Agent Cluster (Workflow)
  P05: '#3b82f6', // Blue - HITL User Interface
  P06: '#8b5cf6', // Purple - Infrastructure/DevOps
  P07: '#ec4899', // Pink - External Integrations
  P08: '#14b8a6', // Teal - Ideas Management
  P09: '#6b7280', // Gray - Security
  P10: '#06b6d4', // Cyan - Diagram Tool
};

/**
 * Helper to calculate word count
 */
function wordCount(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

/**
 * Base timestamp for work item ideas (before existing mock ideas)
 */
const BASE_TIME = Date.now() - 30 * 24 * 60 * 60 * 1000; // 30 days ago

/**
 * Generate ISO timestamp offset from base
 */
function timestamp(offsetDays: number): string {
  return new Date(BASE_TIME + offsetDays * 24 * 60 * 60 * 1000).toISOString();
}

/**
 * Distilled work item feature ideas
 * Each captures the essence of a feature in ~20-25 words
 */
export const workItemFeatureIdeas: Idea[] = [
  // ============================================
  // P01: Infrastructure Foundation
  // ============================================
  {
    id: 'workitem-P01-F01',
    content:
      'Core infrastructure setup with Docker containers, Redis configuration, Python development environment, and foundational tooling for the aSDLC system',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'docker', 'foundation', 'feature'],
    created_at: timestamp(0),
    updated_at: timestamp(0),
    word_count: 0, // Will be calculated
  },
  {
    id: 'workitem-P01-F02',
    content:
      'Bash tool abstraction layer providing standardized JSON interface for agent tooling including lint, test, SAST, SCA, and AST operations',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'tools', 'bash', 'feature'],
    created_at: timestamp(1),
    updated_at: timestamp(1),
    word_count: 0,
  },
  {
    id: 'workitem-P01-F03',
    content:
      'ChromaDB-based knowledge store implementing RAG abstraction layer for semantic code search with future backend replaceability',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'archived', // Deprecated by P02-F04
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'search', 'chromadb', 'deprecated', 'feature'],
    created_at: timestamp(2),
    updated_at: timestamp(2),
    word_count: 0,
  },
  {
    id: 'workitem-P01-F04',
    content:
      'Redis-based coordination system for multi-CLI communication using pub/sub with MCP wrapper, enabling real-time message notifications',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'redis', 'coordination', 'mcp', 'feature'],
    created_at: timestamp(3),
    updated_at: timestamp(3),
    word_count: 0,
  },
  {
    id: 'workitem-P01-F05',
    content:
      'Agent-to-agent push notification system using Redis notification queues for real-time awareness between Claude CLI instances',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'notifications', 'redis', 'feature'],
    created_at: timestamp(4),
    updated_at: timestamp(4),
    word_count: 0,
  },
  {
    id: 'workitem-P01-F06',
    content:
      'Trunk-based development workflow where all CLI instances commit directly to main with pre-commit hook validation for quality gates',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'git', 'workflow', 'feature'],
    created_at: timestamp(5),
    updated_at: timestamp(5),
    word_count: 0,
  },
  {
    id: 'workitem-P01-F07',
    content:
      'CLI subagent architecture with dedicated agents (backend, frontend, orchestrator) having specific instructions and path restrictions',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P01', 'Infrastructure', 'agents', 'cli', 'feature'],
    created_at: timestamp(6),
    updated_at: timestamp(6),
    word_count: 0,
  },

  // ============================================
  // P02: Orchestration & State Management
  // ============================================
  {
    id: 'workitem-P02-F01',
    content:
      'Redis Streams event infrastructure with consumer groups, idempotent processing, tenant awareness, and crash recovery for task orchestration',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Orchestration', 'events', 'redis', 'streams', 'feature'],
    created_at: timestamp(7),
    updated_at: timestamp(7),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F02',
    content:
      'Manager agent serving as exclusive commit gateway and state machine owner, consuming events and dispatching work to agent workers',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P02', 'Orchestration', 'manager', 'gateway', 'feature'],
    created_at: timestamp(8),
    updated_at: timestamp(8),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F03',
    content:
      'HITL dispatcher managing gate requests, evidence bundles, and decision logging with complete audit trail for governance compliance',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P02', 'Orchestration', 'hitl', 'gates', 'audit', 'feature'],
    created_at: timestamp(9),
    updated_at: timestamp(9),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F04',
    content:
      'Elasticsearch semantic search replacing ChromaDB as primary KnowledgeStore backend with kNN vector similarity for intelligent retrieval',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Infrastructure', 'elasticsearch', 'search', 'vectors', 'feature'],
    created_at: timestamp(10),
    updated_at: timestamp(10),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F05',
    content:
      'Repository ingestion with AST analysis into Elasticsearch enabling semantic code search via MCP for agent context enrichment',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Infrastructure', 'ingestion', 'ast', 'context', 'feature'],
    created_at: timestamp(11),
    updated_at: timestamp(11),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F06',
    content:
      'Sender identity validation deriving identity from git user.email for coordination messages, restoring message routing and audit traceability',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Orchestration', 'security', 'identity', 'feature'],
    created_at: timestamp(12),
    updated_at: timestamp(12),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F07',
    content:
      'Prometheus-compatible metrics endpoints exposing request latency, request count, active tasks, and Redis connection status for observability',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Orchestration', 'metrics', 'prometheus', 'observability', 'feature'],
    created_at: timestamp(13),
    updated_at: timestamp(13),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F08',
    content:
      'Agent telemetry REST API and WebSocket endpoints for real-time activity monitoring including status, logs, and execution timeline',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Orchestration', 'telemetry', 'api', 'websocket', 'feature'],
    created_at: timestamp(14),
    updated_at: timestamp(14),
    word_count: 0,
  },
  {
    id: 'workitem-P02-F09',
    content:
      'PostgreSQL persistence layer using repository pattern for storing ideation session data including projects, messages, and maturity state',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P02', 'Infrastructure', 'database', 'persistence', 'postgresql', 'feature'],
    created_at: timestamp(15),
    updated_at: timestamp(15),
    word_count: 0,
  },

  // ============================================
  // P03: Agent Infrastructure
  // ============================================
  {
    id: 'workitem-P03-F01',
    content:
      'Agent worker pool framework consuming events from Redis Streams, executing agents in parallel, and publishing completion events',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P03', 'Agents', 'workers', 'pool', 'parallel', 'feature'],
    created_at: timestamp(16),
    updated_at: timestamp(16),
    word_count: 0,
  },
  {
    id: 'workitem-P03-F02',
    content:
      'Repository mapper generating deterministic context packs by extracting relevant symbols and dependency neighborhoods for focused agent context',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P03', 'Agents', 'context', 'mapper', 'ast', 'feature'],
    created_at: timestamp(17),
    updated_at: timestamp(17),
    word_count: 0,
  },
  {
    id: 'workitem-P03-F03',
    content:
      'Recursive long-horizon reasoning (RLM) for complex codebase exploration using sub-call budgets and REPL-style iterative tool surface',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P03', 'Agents', 'rlm', 'exploration', 'reasoning', 'feature'],
    created_at: timestamp(18),
    updated_at: timestamp(18),
    word_count: 0,
  },

  // ============================================
  // P04: Agent Cluster (Workflow Agents)
  // ============================================
  {
    id: 'workitem-P04-F01',
    content:
      'Discovery agents (PRD Agent, Acceptance Agent) transforming user requirements into structured PRD documents and acceptance criteria',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P04', 'Agents', 'discovery', 'prd', 'requirements', 'feature'],
    created_at: timestamp(19),
    updated_at: timestamp(19),
    word_count: 0,
  },
  {
    id: 'workitem-P04-F02',
    content:
      'Design agents (Arch Surveyor, Solution Architect, Planner) transforming PRDs into technical architecture and implementation plans',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P04', 'Agents', 'design', 'architecture', 'planning', 'feature'],
    created_at: timestamp(20),
    updated_at: timestamp(20),
    word_count: 0,
  },
  {
    id: 'workitem-P04-F03',
    content:
      'Development agents (UTest, Coding, Debugger, Reviewer) implementing TDD Red-Green-Refactor cycle for quality code generation',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P04', 'Agents', 'development', 'tdd', 'coding', 'feature'],
    created_at: timestamp(21),
    updated_at: timestamp(21),
    word_count: 0,
  },
  {
    id: 'workitem-P04-F04',
    content:
      'Validation and deployment agents ensuring code quality through validation, security checks, and managing releases and deployments',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P04', 'Agents', 'validation', 'deployment', 'security', 'feature'],
    created_at: timestamp(22),
    updated_at: timestamp(22),
    word_count: 0,
  },
  {
    id: 'workitem-P04-F05',
    content:
      'Parallel review swarm spawning three specialized reviewers (security, performance, style) with unified result aggregation',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P04', 'Agents', 'review', 'swarm', 'parallel', 'feature'],
    created_at: timestamp(23),
    updated_at: timestamp(23),
    word_count: 0,
  },

  // ============================================
  // P05: HITL User Interface
  // ============================================
  {
    id: 'workitem-P05-F01',
    content:
      'HITL governance dashboard foundation with React, Vite, TypeScript, and TanStack Query for human-in-loop gate approvals',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'react', 'dashboard', 'governance', 'feature'],
    created_at: timestamp(24),
    updated_at: timestamp(24),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F04',
    content:
      'Feedback learning evaluator agent capturing HITL feedback patterns, classifying them, and proposing system improvement rules',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'feedback', 'learning', 'evaluator', 'feature'],
    created_at: timestamp(25),
    updated_at: timestamp(25),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F05',
    content:
      'Command-line interface using Typer/Rich for aSDLC automation, scripting, and CI/CD integration workflows',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'CLI', 'automation', 'cicd', 'feature'],
    created_at: timestamp(26),
    updated_at: timestamp(26),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F06',
    content:
      'Full SPA dashboard with multi-view layout, documentation browser, agent cockpit, discovery studio, and artifact management',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'spa', 'dashboard', 'comprehensive', 'feature'],
    created_at: timestamp(27),
    updated_at: timestamp(27),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F07',
    content:
      'Documentation browser integrating system docs and Mermaid diagrams with navigation, search, and markdown rendering',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'docs', 'markdown', 'diagrams', 'feature'],
    created_at: timestamp(28),
    updated_at: timestamp(28),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F08',
    content:
      'KnowledgeStore search interface supporting REST, GraphQL, and MCP backends with full-text and semantic search capabilities',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'search', 'elasticsearch', 'interface', 'feature'],
    created_at: timestamp(29),
    updated_at: timestamp(29),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F09',
    content:
      'Kubernetes visibility dashboard with cluster health monitoring, pod logs, metrics visualization, and diagnostic command execution',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'k8s', 'monitoring', 'dashboard', 'feature'],
    created_at: timestamp(30),
    updated_at: timestamp(30),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F10',
    content:
      'Metrics dashboard visualizing VictoriaMetrics time series with real-time CPU, memory, and request metrics with auto-refresh',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'metrics', 'charts', 'realtime', 'feature'],
    created_at: timestamp(31),
    updated_at: timestamp(31),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F11',
    content:
      'PRD ideation studio guiding users through structured discovery interviews with maturity tracking and auto-generation capabilities',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'ideation', 'prd', 'studio', 'feature'],
    created_at: timestamp(32),
    updated_at: timestamp(32),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F12',
    content:
      'Agent activity dashboard showing real-time execution status, logs, metrics aggregation, and timeline for agent pool visibility',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'agents', 'activity', 'monitoring', 'feature'],
    created_at: timestamp(33),
    updated_at: timestamp(33),
    word_count: 0,
  },
  {
    id: 'workitem-P05-F13',
    content:
      'LLM admin configuration interface for managing AI providers and per-agent model assignments for studio and development agents',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P05', 'UI', 'llm', 'admin', 'configuration', 'feature'],
    created_at: timestamp(34),
    updated_at: timestamp(34),
    word_count: 0,
  },

  // ============================================
  // P06: Infrastructure/DevOps
  // ============================================
  {
    id: 'workitem-P06-F01',
    content:
      'Kubernetes base infrastructure with Helm umbrella chart, namespace definitions, and minikube development environment scripts',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'k8s', 'helm', 'infrastructure', 'feature'],
    created_at: timestamp(35),
    updated_at: timestamp(35),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F02',
    content:
      'Redis Kubernetes StatefulSet deployment with persistent storage for event streaming and caching infrastructure services',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'redis', 'k8s', 'statefulset', 'feature'],
    created_at: timestamp(36),
    updated_at: timestamp(36),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F03',
    content:
      'ChromaDB Kubernetes StatefulSet with persistent storage for RAG backend plus Mock Anthology implementation for testing',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'archived', // Related to deprecated ChromaDB
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'chromadb', 'k8s', 'deprecated', 'feature'],
    created_at: timestamp(37),
    updated_at: timestamp(37),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F04',
    content:
      'Stateless service deployments (Orchestrator, Workers, HITL-UI) as Kubernetes Deployments with HPA for worker auto-scaling',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'k8s', 'deployment', 'hpa', 'feature'],
    created_at: timestamp(38),
    updated_at: timestamp(38),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F05',
    content:
      'Multi-tenancy support with tenant-aware Redis keys, KnowledgeStore collections, and isolated event routing across aSDLC',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'multitenancy', 'isolation', 'feature'],
    created_at: timestamp(39),
    updated_at: timestamp(39),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F06',
    content:
      'VictoriaMetrics time-series database as StatefulSet with vmagent DaemonSet for Prometheus-compatible metrics collection and storage',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'metrics', 'victoriametrics', 'tsdb', 'feature'],
    created_at: timestamp(40),
    updated_at: timestamp(40),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F07',
    content:
      'Kubernetes cluster monitoring dashboard with interactive service topology, sparkline charts, and DevOps activity tracking',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'monitoring', 'dashboard', 'topology', 'feature'],
    created_at: timestamp(41),
    updated_at: timestamp(41),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F08',
    content:
      'MCP sidecars for Redis and Elasticsearch enabling Claude CLI integration plus Prometheus annotations for metrics scraping',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'mcp', 'sidecars', 'integration', 'feature'],
    created_at: timestamp(42),
    updated_at: timestamp(42),
    word_count: 0,
  },
  {
    id: 'workitem-P06-F09',
    content:
      'Metrics query alignment fixing name and label mismatches between aSDLC metric exports and VictoriaMetrics dashboard queries',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P06', 'DevOps', 'metrics', 'fix', 'alignment', 'feature'],
    created_at: timestamp(43),
    updated_at: timestamp(43),
    word_count: 0,
  },

  // ============================================
  // P07: External Integrations
  // ============================================
  {
    id: 'workitem-P07-F01',
    content:
      'Plane Community Edition deployment to Kubernetes for project, epic, and task management integration with aSDLC workflow',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P07', 'Integration', 'plane', 'project-management', 'feature'],
    created_at: timestamp(44),
    updated_at: timestamp(44),
    word_count: 0,
  },

  // ============================================
  // P08: Ideas Management
  // ============================================
  {
    id: 'workitem-P08-F01',
    content:
      'Ideas repository capturing short-form ideas with full-text search, vector embeddings, and Elasticsearch-backed storage',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'repository', 'search', 'storage', 'feature'],
    created_at: timestamp(45),
    updated_at: timestamp(45),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F02',
    content:
      'Slack integration enabling team members to submit ideas directly from their workspace without context switching',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'slack', 'integration', 'capture', 'feature'],
    created_at: timestamp(46),
    updated_at: timestamp(46),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F03',
    content:
      'Auto-classification engine using ML to categorize ideas as functional, non-functional, or undetermined based on content analysis',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'classification', 'ml', 'auto', 'feature'],
    created_at: timestamp(47),
    updated_at: timestamp(47),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F04',
    content:
      'Correlation engine discovering relationships between ideas using semantic similarity, contradictions, and complementary patterns',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'correlations', 'relationships', 'ml', 'feature'],
    created_at: timestamp(48),
    updated_at: timestamp(48),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F05',
    content:
      'Mindflare hub UI for browsing ideas with filtering, search, detail panels, and "bake to PRD" workflow integration',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'hub', 'ui', 'browsing', 'feature'],
    created_at: timestamp(49),
    updated_at: timestamp(49),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F06',
    content:
      'Snowflake graph visualization showing idea correlations as interactive force-directed graph with node selection and filtering',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'graph', 'visualization', 'snowflake', 'feature'],
    created_at: timestamp(50),
    updated_at: timestamp(50),
    word_count: 0,
  },
  {
    id: 'workitem-P08-F07',
    content:
      'Enhanced snowflake graph with advanced controls, clustering visualization, edge bundling, and evidence inspector for connections',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P08', 'Ideas', 'graph', 'enhanced', 'clustering', 'feature'],
    created_at: timestamp(51),
    updated_at: timestamp(51),
    word_count: 0,
  },

  // ============================================
  // P09: Security
  // ============================================
  {
    id: 'workitem-P09-F01',
    content:
      'Centralized secrets management evaluating Infisical vs GCP Secret Manager with auditing and environment isolation capabilities',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'non_functional',
    labels: ['P09', 'Security', 'secrets', 'vault', 'audit', 'feature'],
    created_at: timestamp(52),
    updated_at: timestamp(52),
    word_count: 0,
  },

  // ============================================
  // P10: Diagram Tool
  // ============================================
  {
    id: 'workitem-P10-F01',
    content:
      'Architect board canvas using Excalidraw for interactive diagram creation with 3-panel layout and SVG export capabilities',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P10', 'Diagrams', 'canvas', 'excalidraw', 'drawing', 'feature'],
    created_at: timestamp(53),
    updated_at: timestamp(53),
    word_count: 0,
  },
  {
    id: 'workitem-P10-F02',
    content:
      'Diagram translation service converting SVG drawings to PNG, Mermaid, and Draw.io formats using LLM-based interpretation',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P10', 'Diagrams', 'translation', 'llm', 'export', 'feature'],
    created_at: timestamp(54),
    updated_at: timestamp(54),
    word_count: 0,
  },
  {
    id: 'workitem-P10-F03',
    content:
      'Draft history manager enabling diagram persistence with PostgreSQL/Redis storage, history browsing, and auto-save functionality',
    author_id: 'system',
    author_name: 'Work Items Import',
    status: 'active',
    classification: 'functional',
    labels: ['P10', 'Diagrams', 'history', 'persistence', 'autosave', 'feature'],
    created_at: timestamp(55),
    updated_at: timestamp(55),
    word_count: 0,
  },
];

// Calculate word counts for all ideas
workItemFeatureIdeas.forEach((idea) => {
  idea.word_count = wordCount(idea.content);
});

/**
 * Get all work item ideas merged with existing mock ideas
 */
export function getAllIdeasWithWorkItems(existingIdeas: Idea[]): Idea[] {
  return [...workItemFeatureIdeas, ...existingIdeas];
}
