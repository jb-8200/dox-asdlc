/**
 * Mock data for Agent Activity Dashboard (P05-F12)
 *
 * Provides mock agent status, logs, and metrics for development.
 */

import type {
  AgentStatus,
  AgentLog,
  AgentMetrics,
  AgentMetricsSummary,
  AgentMetricsResponse,
  AgentType,
  MetricsTimeRange,
  TimelineData,
  TaskExecution,
  MetricsDataPoint,
} from '../../types/agents';

// ============================================================================
// Helper Functions
// ============================================================================

const now = new Date();

function minutesAgo(minutes: number): string {
  return new Date(now.getTime() - minutes * 60 * 1000).toISOString();
}

function hoursAgo(hours: number): string {
  return new Date(now.getTime() - hours * 60 * 60 * 1000).toISOString();
}

/**
 * Simulate network delay for realistic UX
 */
export async function simulateAgentDelay(minMs = 50, maxMs = 150): Promise<void> {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  await new Promise((resolve) => setTimeout(resolve, delay));
}

// ============================================================================
// Mock Agent Status Data
// ============================================================================

export const mockAgents: AgentStatus[] = [
  {
    agent_id: 'agent-backend-001',
    agent_type: 'backend',
    status: 'running',
    currentTask: 'Implementing Redis integration',
    progress: 65,
    sessionId: 'sess-abc123',
    startedAt: minutesAgo(15),
    lastHeartbeat: minutesAgo(0),
  },
  {
    agent_id: 'agent-frontend-001',
    agent_type: 'frontend',
    status: 'running',
    currentTask: 'Building AgentStatusCard component',
    progress: 40,
    sessionId: 'sess-def456',
    startedAt: minutesAgo(8),
    lastHeartbeat: minutesAgo(0),
  },
  {
    agent_id: 'agent-reviewer-001',
    agent_type: 'reviewer',
    status: 'idle',
    currentTask: null,
    progress: 0,
    sessionId: null,
    startedAt: null,
    lastHeartbeat: minutesAgo(2),
  },
  {
    agent_id: 'agent-planner-001',
    agent_type: 'planner',
    status: 'running',
    currentTask: 'Creating design.md for P05-F13',
    progress: 80,
    sessionId: 'sess-ghi789',
    startedAt: minutesAgo(5),
    lastHeartbeat: minutesAgo(0),
  },
  {
    agent_id: 'agent-devops-001',
    agent_type: 'devops',
    status: 'idle',
    currentTask: null,
    progress: 0,
    sessionId: null,
    startedAt: null,
    lastHeartbeat: minutesAgo(10),
  },
  {
    agent_id: 'agent-orchestrator-001',
    agent_type: 'orchestrator',
    status: 'running',
    currentTask: 'Running E2E test suite',
    progress: 25,
    sessionId: 'sess-jkl012',
    startedAt: minutesAgo(3),
    lastHeartbeat: minutesAgo(0),
  },
  {
    agent_id: 'agent-test-001',
    agent_type: 'test',
    status: 'error',
    currentTask: 'Unit test suite',
    progress: 75,
    sessionId: 'sess-mno345',
    startedAt: minutesAgo(20),
    lastHeartbeat: minutesAgo(5),
    metadata: { failureReason: 'Assertion failed in auth module' },
  },
  {
    agent_id: 'agent-coding-001',
    agent_type: 'coding',
    status: 'completed',
    currentTask: null,
    progress: 0,
    sessionId: null,
    startedAt: null,
    lastHeartbeat: hoursAgo(1),
  },
];

export function getMockAgents(): AgentStatus[] {
  return [...mockAgents];
}

export function getMockAgentById(agentId: string): AgentStatus | undefined {
  return mockAgents.find((a) => a.agent_id === agentId);
}

// ============================================================================
// Mock Agent Logs Data
// ============================================================================

const mockLogsBackend: AgentLog[] = [
  {
    id: 'log-001',
    agentId: 'agent-backend-001',
    level: 'info',
    message: 'Starting Redis integration task',
    timestamp: minutesAgo(15),
  },
  {
    id: 'log-002',
    agentId: 'agent-backend-001',
    level: 'debug',
    message: 'Loading context pack: redis_patterns.json',
    timestamp: minutesAgo(14),
  },
  {
    id: 'log-003',
    agentId: 'agent-backend-001',
    level: 'info',
    message: 'Writing test file: test_redis_client.py',
    timestamp: minutesAgo(12),
  },
  {
    id: 'log-004',
    agentId: 'agent-backend-001',
    level: 'warn',
    message: 'Test coverage below threshold (78%)',
    timestamp: minutesAgo(8),
  },
  {
    id: 'log-005',
    agentId: 'agent-backend-001',
    level: 'info',
    message: 'Implementing RedisStreamConsumer class',
    timestamp: minutesAgo(5),
  },
  {
    id: 'log-006',
    agentId: 'agent-backend-001',
    level: 'debug',
    message: 'Tool call: Edit(src/infrastructure/redis_client.py)',
    timestamp: minutesAgo(3),
  },
];

const mockLogsFrontend: AgentLog[] = [
  {
    id: 'log-101',
    agentId: 'agent-frontend-001',
    level: 'info',
    message: 'Starting component development',
    timestamp: minutesAgo(8),
  },
  {
    id: 'log-102',
    agentId: 'agent-frontend-001',
    level: 'debug',
    message: 'Reading existing component patterns',
    timestamp: minutesAgo(7),
  },
  {
    id: 'log-103',
    agentId: 'agent-frontend-001',
    level: 'info',
    message: 'Creating AgentStatusCard.test.tsx',
    timestamp: minutesAgo(5),
  },
  {
    id: 'log-104',
    agentId: 'agent-frontend-001',
    level: 'error',
    message: 'Test failed: expected badge to have class "bg-status-error"',
    timestamp: minutesAgo(3),
    context: { testName: 'renders failed status correctly' },
  },
  {
    id: 'log-105',
    agentId: 'agent-frontend-001',
    level: 'info',
    message: 'Fixing status badge color mapping',
    timestamp: minutesAgo(2),
  },
];

const mockLogsTest: AgentLog[] = [
  {
    id: 'log-201',
    agentId: 'agent-test-001',
    level: 'info',
    message: 'Running unit test suite',
    timestamp: minutesAgo(20),
  },
  {
    id: 'log-202',
    agentId: 'agent-test-001',
    level: 'info',
    message: 'Tests passed: 45/60',
    timestamp: minutesAgo(10),
  },
  {
    id: 'log-203',
    agentId: 'agent-test-001',
    level: 'error',
    message: 'FAIL: test_auth_token_refresh - AssertionError',
    timestamp: minutesAgo(8),
    context: {
      file: 'tests/unit/test_auth.py',
      line: 145,
      expected: 'valid_token',
      actual: 'null',
    },
  },
  {
    id: 'log-204',
    agentId: 'agent-test-001',
    level: 'error',
    message: 'FAIL: test_session_expiry - TimeoutError',
    timestamp: minutesAgo(7),
    context: { file: 'tests/unit/test_auth.py', line: 180 },
  },
  {
    id: 'log-205',
    agentId: 'agent-test-001',
    level: 'error',
    message: 'Test suite failed with 15 failures',
    timestamp: minutesAgo(5),
  },
];

const allMockLogs: Record<string, AgentLog[]> = {
  'agent-backend-001': mockLogsBackend,
  'agent-frontend-001': mockLogsFrontend,
  'agent-test-001': mockLogsTest,
};

export function getMockAgentLogs(
  agentId: string,
  params?: { level?: string; search?: string; limit?: number }
): AgentLog[] {
  let logs = allMockLogs[agentId] || [];

  // Filter by level
  if (params?.level) {
    logs = logs.filter((log) => log.level === params.level);
  }

  // Filter by search term
  if (params?.search) {
    const searchLower = params.search.toLowerCase();
    logs = logs.filter((log) => log.message.toLowerCase().includes(searchLower));
  }

  // Apply limit
  if (params?.limit) {
    logs = logs.slice(0, params.limit);
  }

  return logs;
}

// ============================================================================
// Mock Agent Metrics Data
// ============================================================================

function generateTimeSeriesData(
  range: MetricsTimeRange,
  baseValue: number,
  variance: number
): MetricsDataPoint[] {
  const points: MetricsDataPoint[] = [];
  const now = new Date();

  let intervalMs: number;
  let numPoints: number;

  switch (range) {
    case '1h':
      intervalMs = 5 * 60 * 1000; // 5 minutes
      numPoints = 12;
      break;
    case '6h':
      intervalMs = 30 * 60 * 1000; // 30 minutes
      numPoints = 12;
      break;
    case '24h':
      intervalMs = 2 * 60 * 60 * 1000; // 2 hours
      numPoints = 12;
      break;
    case '7d':
      intervalMs = 12 * 60 * 60 * 1000; // 12 hours
      numPoints = 14;
      break;
  }

  for (let i = numPoints - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * intervalMs);
    const value = Math.max(0, baseValue + (Math.random() - 0.5) * variance);
    points.push({
      timestamp: timestamp.toISOString(),
      value: Math.round(value * 100) / 100,
    });
  }

  return points;
}

export function getMockAgentMetrics(
  params?: { timeRange?: MetricsTimeRange; agentType?: AgentType }
): AgentMetricsResponse {
  const timeRange = params?.timeRange || '1h';

  const agentMetrics: AgentMetrics[] = [
    {
      agentId: 'agent-backend-001',
      agentType: 'backend',
      executionCount: 45,
      successRate: 91,
      avgDurationMs: 12500,
      totalTokens: 125000,
      executionsOverTime: generateTimeSeriesData(timeRange, 4, 2),
      successRateOverTime: generateTimeSeriesData(timeRange, 90, 10),
    },
    {
      agentId: 'agent-frontend-001',
      agentType: 'frontend',
      executionCount: 38,
      successRate: 95,
      avgDurationMs: 8200,
      totalTokens: 95000,
      executionsOverTime: generateTimeSeriesData(timeRange, 3, 2),
      successRateOverTime: generateTimeSeriesData(timeRange, 94, 8),
    },
    {
      agentId: 'agent-reviewer-001',
      agentType: 'reviewer',
      executionCount: 62,
      successRate: 98,
      avgDurationMs: 4500,
      totalTokens: 78000,
      executionsOverTime: generateTimeSeriesData(timeRange, 5, 3),
      successRateOverTime: generateTimeSeriesData(timeRange, 97, 5),
    },
    {
      agentId: 'agent-planner-001',
      agentType: 'planner',
      executionCount: 25,
      successRate: 96,
      avgDurationMs: 15000,
      totalTokens: 150000,
      executionsOverTime: generateTimeSeriesData(timeRange, 2, 1),
      successRateOverTime: generateTimeSeriesData(timeRange, 95, 8),
    },
    {
      agentId: 'agent-devops-001',
      agentType: 'devops',
      executionCount: 18,
      successRate: 89,
      avgDurationMs: 25000,
      totalTokens: 45000,
      executionsOverTime: generateTimeSeriesData(timeRange, 1.5, 1),
      successRateOverTime: generateTimeSeriesData(timeRange, 88, 15),
    },
    {
      agentId: 'agent-orchestrator-001',
      agentType: 'orchestrator',
      executionCount: 30,
      successRate: 93,
      avgDurationMs: 18000,
      totalTokens: 180000,
      executionsOverTime: generateTimeSeriesData(timeRange, 2.5, 1.5),
      successRateOverTime: generateTimeSeriesData(timeRange, 92, 10),
    },
    {
      agentId: 'agent-test-001',
      agentType: 'test',
      executionCount: 55,
      successRate: 78,
      avgDurationMs: 35000,
      totalTokens: 65000,
      executionsOverTime: generateTimeSeriesData(timeRange, 4.5, 2),
      successRateOverTime: generateTimeSeriesData(timeRange, 78, 15),
    },
  ];

  // Filter by agent type if specified
  let filteredMetrics = agentMetrics;
  if (params?.agentType) {
    filteredMetrics = agentMetrics.filter((m) => m.agentType === params.agentType);
  }

  // Calculate summary
  const summary: AgentMetricsSummary = {
    totalExecutions: agentMetrics.reduce((sum, m) => sum + m.executionCount, 0),
    overallSuccessRate: Math.round(
      agentMetrics.reduce((sum, m) => sum + m.successRate * m.executionCount, 0) /
        agentMetrics.reduce((sum, m) => sum + m.executionCount, 0)
    ),
    avgDurationMs: Math.round(
      agentMetrics.reduce((sum, m) => sum + m.avgDurationMs * m.executionCount, 0) /
        agentMetrics.reduce((sum, m) => sum + m.executionCount, 0)
    ),
    totalTokens: agentMetrics.reduce((sum, m) => sum + m.totalTokens, 0),
    byAgentType: {
      planner: { executionCount: 25, successRate: 96, avgDurationMs: 15000 },
      backend: { executionCount: 45, successRate: 91, avgDurationMs: 12500 },
      frontend: { executionCount: 38, successRate: 95, avgDurationMs: 8200 },
      reviewer: { executionCount: 62, successRate: 98, avgDurationMs: 4500 },
      orchestrator: { executionCount: 30, successRate: 93, avgDurationMs: 18000 },
      devops: { executionCount: 18, successRate: 89, avgDurationMs: 25000 },
      discovery: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
      coding: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
      test: { executionCount: 55, successRate: 78, avgDurationMs: 35000 },
      design: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
    },
  };

  return {
    summary,
    agents: filteredMetrics,
    timeRange,
  };
}

// ============================================================================
// Mock Timeline Data
// ============================================================================

export function getMockAgentTimeline(timeRange: MetricsTimeRange): TimelineData {
  const now = new Date();
  let rangeMs: number;

  switch (timeRange) {
    case '1h':
      rangeMs = 60 * 60 * 1000;
      break;
    case '6h':
      rangeMs = 6 * 60 * 60 * 1000;
      break;
    case '24h':
      rangeMs = 24 * 60 * 60 * 1000;
      break;
    case '7d':
      rangeMs = 7 * 24 * 60 * 60 * 1000;
      break;
  }

  const startTime = new Date(now.getTime() - rangeMs);

  const backendExecutions: TaskExecution[] = [
    {
      id: 'exec-001',
      taskName: 'Implement Redis client',
      agentId: 'agent-backend-001',
      agentType: 'backend',
      startTime: new Date(startTime.getTime() + rangeMs * 0.1).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.25).toISOString(),
      durationMs: rangeMs * 0.15,
      status: 'completed',
    },
    {
      id: 'exec-002',
      taskName: 'Add Redis stream support',
      agentId: 'agent-backend-001',
      agentType: 'backend',
      startTime: new Date(startTime.getTime() + rangeMs * 0.4).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.55).toISOString(),
      durationMs: rangeMs * 0.15,
      status: 'completed',
    },
    {
      id: 'exec-003',
      taskName: 'Redis integration',
      agentId: 'agent-backend-001',
      agentType: 'backend',
      startTime: new Date(startTime.getTime() + rangeMs * 0.75).toISOString(),
      endTime: null,
      durationMs: null,
      status: 'running',
    },
  ];

  const frontendExecutions: TaskExecution[] = [
    {
      id: 'exec-101',
      taskName: 'Build Dashboard layout',
      agentId: 'agent-frontend-001',
      agentType: 'frontend',
      startTime: new Date(startTime.getTime() + rangeMs * 0.15).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.35).toISOString(),
      durationMs: rangeMs * 0.2,
      status: 'completed',
    },
    {
      id: 'exec-102',
      taskName: 'AgentStatusCard component',
      agentId: 'agent-frontend-001',
      agentType: 'frontend',
      startTime: new Date(startTime.getTime() + rangeMs * 0.8).toISOString(),
      endTime: null,
      durationMs: null,
      status: 'running',
    },
  ];

  const reviewerExecutions: TaskExecution[] = [
    {
      id: 'exec-201',
      taskName: 'Review Redis implementation',
      agentId: 'agent-reviewer-001',
      agentType: 'reviewer',
      startTime: new Date(startTime.getTime() + rangeMs * 0.28).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.38).toISOString(),
      durationMs: rangeMs * 0.1,
      status: 'completed',
    },
    {
      id: 'exec-202',
      taskName: 'Review dashboard PR',
      agentId: 'agent-reviewer-001',
      agentType: 'reviewer',
      startTime: new Date(startTime.getTime() + rangeMs * 0.6).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.68).toISOString(),
      durationMs: rangeMs * 0.08,
      status: 'completed',
    },
  ];

  const testExecutions: TaskExecution[] = [
    {
      id: 'exec-301',
      taskName: 'Unit test suite',
      agentId: 'agent-test-001',
      agentType: 'test',
      startTime: new Date(startTime.getTime() + rangeMs * 0.5).toISOString(),
      endTime: new Date(startTime.getTime() + rangeMs * 0.65).toISOString(),
      durationMs: rangeMs * 0.15,
      status: 'failed',
    },
  ];

  return {
    agents: [
      { agentId: 'agent-backend-001', agentType: 'backend', executions: backendExecutions },
      { agentId: 'agent-frontend-001', agentType: 'frontend', executions: frontendExecutions },
      { agentId: 'agent-reviewer-001', agentType: 'reviewer', executions: reviewerExecutions },
      { agentId: 'agent-test-001', agentType: 'test', executions: testExecutions },
    ],
    startTime: startTime.toISOString(),
    endTime: now.toISOString(),
  };
}
