/**
 * Agent Activity Dashboard Types (P05-F12)
 *
 * Type definitions for agent status, logs, and metrics
 * used in the Agent Activity Dashboard.
 */

// ============================================================================
// Agent Status Types
// ============================================================================

/** Agent status states */
export type AgentStatusType = 'idle' | 'running' | 'blocked' | 'error' | 'completed';

/** Agent type identifiers */
export type AgentType =
  | 'planner'
  | 'backend'
  | 'frontend'
  | 'reviewer'
  | 'orchestrator'
  | 'devops'
  | 'discovery'
  | 'coding'
  | 'test'
  | 'design';

/** Agent status information */
export interface AgentStatus {
  /** Unique agent identifier */
  agent_id: string;
  /** Agent type/role */
  agent_type: AgentType;
  /** Current status */
  status: AgentStatusType;
  /** Current task being executed (if running) */
  currentTask: string | null;
  /** Task progress percentage (0-100) */
  progress: number;
  /** Session ID if actively working */
  sessionId: string | null;
  /** When the agent started current task */
  startedAt: string | null;
  /** Last heartbeat timestamp */
  lastHeartbeat: string;
  /** Agent metadata */
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Agent Log Types
// ============================================================================

/** Log level */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/** Agent log entry */
export interface AgentLog {
  /** Unique log entry ID */
  id: string;
  /** Agent ID that generated this log */
  agentId: string;
  /** Log level */
  level: LogLevel;
  /** Log message */
  message: string;
  /** Timestamp */
  timestamp: string;
  /** Additional context */
  context?: Record<string, unknown>;
}

// ============================================================================
// Agent Metrics Types
// ============================================================================

/** Time range for metrics queries */
export type MetricsTimeRange = '1h' | '6h' | '24h' | '7d';

/** Metrics time range options for UI */
export const METRICS_TIME_RANGE_OPTIONS: Array<{
  value: MetricsTimeRange;
  label: string;
}> = [
  { value: '1h', label: '1h' },
  { value: '6h', label: '6h' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
];

/** Data point for time series */
export interface MetricsDataPoint {
  /** Timestamp */
  timestamp: string;
  /** Value */
  value: number;
}

/** Agent metrics */
export interface AgentMetrics {
  /** Agent ID */
  agentId: string;
  /** Agent type */
  agentType: AgentType;
  /** Number of executions */
  executionCount: number;
  /** Success rate (0-100) */
  successRate: number;
  /** Average duration in milliseconds */
  avgDurationMs: number;
  /** Total tokens used */
  totalTokens: number;
  /** Executions over time */
  executionsOverTime: MetricsDataPoint[];
  /** Success rate over time */
  successRateOverTime: MetricsDataPoint[];
}

/** Aggregated metrics for all agents */
export interface AgentMetricsSummary {
  /** Total executions across all agents */
  totalExecutions: number;
  /** Overall success rate */
  overallSuccessRate: number;
  /** Average duration across all agents */
  avgDurationMs: number;
  /** Total tokens used by all agents */
  totalTokens: number;
  /** Metrics by agent type */
  byAgentType: Record<AgentType, {
    executionCount: number;
    successRate: number;
    avgDurationMs: number;
  }>;
}

// ============================================================================
// Timeline Types
// ============================================================================

/** Task execution block for timeline */
export interface TaskExecution {
  /** Unique execution ID */
  id: string;
  /** Task name */
  taskName: string;
  /** Agent ID */
  agentId: string;
  /** Agent type */
  agentType: AgentType;
  /** Start timestamp */
  startTime: string;
  /** End timestamp (null if still running) */
  endTime: string | null;
  /** Duration in milliseconds (computed or null if running) */
  durationMs: number | null;
  /** Status */
  status: 'running' | 'completed' | 'failed';
}

/** Timeline data for Gantt-style view */
export interface TimelineData {
  /** Agent rows with their executions */
  agents: Array<{
    agentId: string;
    agentType: AgentType;
    executions: TaskExecution[];
  }>;
  /** Time range start */
  startTime: string;
  /** Time range end */
  endTime: string;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

/** WebSocket agent status update event */
export interface AgentStatusUpdateEvent {
  type: 'agent:status_update';
  agentId: string;
  status: AgentStatusType;
  currentTask: string | null;
  progress: number;
  timestamp: string;
}

/** WebSocket agent log event */
export interface AgentLogEvent {
  type: 'agent:log';
  log: AgentLog;
}

// ============================================================================
// API Response Types
// ============================================================================

/** Response for GET /api/agents/status */
export interface AgentsStatusResponse {
  agents: AgentStatus[];
  total: number;
}

/** Response for GET /api/agents/{id}/logs */
export interface AgentLogsResponse {
  logs: AgentLog[];
  total: number;
  hasMore: boolean;
}

/** Response for GET /api/agents/metrics */
export interface AgentMetricsResponse {
  summary: AgentMetricsSummary;
  agents: AgentMetrics[];
  timeRange: MetricsTimeRange;
}

/** Response for GET /api/agents/timeline */
export interface AgentTimelineResponse {
  timeline: TimelineData;
}

// ============================================================================
// Query Parameters
// ============================================================================

/** Query parameters for agent logs */
export interface AgentLogsQueryParams {
  /** Filter by log level */
  level?: LogLevel;
  /** Search term */
  search?: string;
  /** Maximum number of logs to return */
  limit?: number;
  /** Offset for pagination */
  offset?: number;
}

/** Query parameters for agent metrics */
export interface AgentMetricsQueryParams {
  /** Time range */
  timeRange?: MetricsTimeRange;
  /** Filter by agent type */
  agentType?: AgentType;
}

// ============================================================================
// UI Helper Constants
// ============================================================================

/** Status to color mapping for badges */
export const STATUS_COLORS: Record<AgentStatusType, string> = {
  idle: 'bg-status-info',
  running: 'bg-accent-blue',
  blocked: 'bg-status-warning',
  error: 'bg-status-error',
  completed: 'bg-status-success',
};

/** Status to label mapping */
export const STATUS_LABELS: Record<AgentStatusType, string> = {
  idle: 'Idle',
  running: 'Running',
  blocked: 'Blocked',
  error: 'Error',
  completed: 'Completed',
};

/** Log level to color mapping */
export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  debug: 'text-text-muted',
  info: 'text-text-secondary',
  warn: 'text-status-warning',
  error: 'text-status-error',
};

/** Agent type icons (for reference, actual icons in components) */
export const AGENT_TYPE_LABELS: Record<AgentType, string> = {
  planner: 'Planner',
  backend: 'Backend',
  frontend: 'Frontend',
  reviewer: 'Reviewer',
  orchestrator: 'Orchestrator',
  devops: 'DevOps',
  discovery: 'Discovery',
  coding: 'Coding',
  test: 'Test',
  design: 'Design',
};
