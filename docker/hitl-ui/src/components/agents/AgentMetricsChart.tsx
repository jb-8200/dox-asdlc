/**
 * AgentMetricsChart - Metrics visualization for agents (P05-F12 T08)
 *
 * Features:
 * - Bar chart for executions by agent type
 * - Line chart for success rate over time
 * - Time range selector
 * - Summary statistics
 */

import { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import clsx from 'clsx';
import type { AgentMetricsResponse, MetricsTimeRange, AgentType } from '../../types/agents';
import { METRICS_TIME_RANGE_OPTIONS, AGENT_TYPE_LABELS } from '../../types/agents';
import { formatDuration, formatTokens } from '../../api/agents';

export interface AgentMetricsChartProps {
  /** Metrics data */
  data?: AgentMetricsResponse | null;
  /** Current time range */
  timeRange?: MetricsTimeRange;
  /** Loading state */
  isLoading?: boolean;
  /** Callback when time range changes */
  onTimeRangeChange?: (range: MetricsTimeRange) => void;
  /** Custom class name */
  className?: string;
}

type ChartType = 'executions' | 'successRate';

// Chart colors
const CHART_COLORS = {
  primary: '#3b82f6', // accent-blue
  secondary: '#10b981', // green
  grid: '#30363d',
  text: '#8b949e',
};

export default function AgentMetricsChart({
  data,
  timeRange = '1h',
  isLoading = false,
  onTimeRangeChange,
  className,
}: AgentMetricsChartProps) {
  const [chartType, setChartType] = useState<ChartType>('executions');

  // Prepare data for bar chart (executions by agent type)
  const barChartData = useMemo(() => {
    if (!data?.summary.byAgentType) return [];

    return Object.entries(data.summary.byAgentType)
      .filter(([, stats]) => stats.executionCount > 0)
      .map(([type, stats]) => ({
        type: AGENT_TYPE_LABELS[type as AgentType],
        executions: stats.executionCount,
        successRate: stats.successRate,
      }))
      .sort((a, b) => b.executions - a.executions);
  }, [data]);

  // Prepare data for line chart (over time)
  const lineChartData = useMemo(() => {
    if (!data?.agents || data.agents.length === 0) return [];

    const firstAgent = data.agents[0];
    const dataSource =
      chartType === 'executions'
        ? firstAgent.executionsOverTime
        : firstAgent.successRateOverTime;

    return dataSource.map((point) => ({
      time: new Date(point.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
      value: point.value,
    }));
  }, [data, chartType]);

  // Loading state
  if (isLoading && !data) {
    return (
      <div
        data-testid="metrics-loading"
        className={clsx('animate-pulse space-y-4', className)}
      >
        <div className="h-8 w-48 bg-bg-tertiary rounded" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-bg-tertiary rounded-lg" />
          ))}
        </div>
        <div className="h-64 bg-bg-tertiary rounded-lg" />
      </div>
    );
  }

  // Empty state
  if (!data) {
    return (
      <div
        data-testid="metrics-empty"
        className={clsx(
          'flex flex-col items-center justify-center py-12 px-4 text-center',
          'bg-bg-secondary rounded-lg border border-border-primary',
          className
        )}
      >
        <p className="text-text-muted">No metrics data available</p>
        <p className="text-sm text-text-muted mt-1">
          Metrics will appear as agents execute tasks
        </p>
      </div>
    );
  }

  const { summary } = data;

  return (
    <div
      data-testid="metrics-chart"
      role="region"
      aria-label="Agent metrics chart"
      className={clsx('space-y-6', className)}
    >
      {/* Header with Time Range Selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary">
          Agent Metrics
        </h3>
        <div
          data-testid="time-range-selector"
          className="flex items-center gap-1"
          role="group"
          aria-label="Time range selection"
        >
          {METRICS_TIME_RANGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              data-testid={`time-range-${option.value}`}
              onClick={() => onTimeRangeChange?.(option.value)}
              className={clsx(
                'px-3 py-1.5 rounded text-xs font-medium transition-colors',
                timeRange === option.value
                  ? 'bg-accent-blue text-white'
                  : 'bg-bg-tertiary text-text-muted hover:bg-bg-tertiary/80 hover:text-text-secondary'
              )}
              aria-pressed={timeRange === option.value}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Executions"
          value={summary.totalExecutions.toString()}
        />
        <StatCard
          label="Success Rate"
          value={`${summary.overallSuccessRate}%`}
          color={summary.overallSuccessRate >= 90 ? 'green' : summary.overallSuccessRate >= 70 ? 'yellow' : 'red'}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(summary.avgDurationMs)}
        />
        <StatCard
          label="Total Tokens"
          value={formatTokens(summary.totalTokens)}
        />
      </div>

      {/* Chart Type Toggle */}
      <div
        data-testid="chart-type-toggle"
        className="flex items-center gap-2"
        role="group"
        aria-label="Chart type selection"
      >
        <button
          data-testid="chart-executions"
          onClick={() => setChartType('executions')}
          className={clsx(
            'px-3 py-1.5 rounded text-xs font-medium transition-colors',
            chartType === 'executions'
              ? 'bg-accent-blue text-white'
              : 'bg-bg-tertiary text-text-muted hover:text-text-secondary'
          )}
          aria-pressed={chartType === 'executions'}
        >
          Executions
        </button>
        <button
          data-testid="chart-success-rate"
          onClick={() => setChartType('successRate')}
          className={clsx(
            'px-3 py-1.5 rounded text-xs font-medium transition-colors',
            chartType === 'successRate'
              ? 'bg-accent-blue text-white'
              : 'bg-bg-tertiary text-text-muted hover:text-text-secondary'
          )}
          aria-pressed={chartType === 'successRate'}
        >
          Success Rate
        </button>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart - Executions by Agent Type */}
        <div className="bg-bg-secondary rounded-lg border border-border-primary p-4">
          <h4 className="text-sm font-medium text-text-muted mb-4">
            {chartType === 'executions' ? 'Executions by Agent Type' : 'Success Rate by Agent Type'}
          </h4>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barChartData} layout="vertical">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={CHART_COLORS.grid}
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  stroke={CHART_COLORS.text}
                  fontSize={11}
                  tickLine={false}
                  domain={chartType === 'successRate' ? [0, 100] : undefined}
                />
                <YAxis
                  type="category"
                  dataKey="type"
                  stroke={CHART_COLORS.text}
                  fontSize={11}
                  tickLine={false}
                  width={80}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#161b22',
                    border: '1px solid #30363d',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#c9d1d9' }}
                  itemStyle={{ color: '#8b949e' }}
                />
                <Bar
                  dataKey={chartType === 'executions' ? 'executions' : 'successRate'}
                  fill={CHART_COLORS.primary}
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Line Chart - Over Time */}
        <div className="bg-bg-secondary rounded-lg border border-border-primary p-4">
          <h4 className="text-sm font-medium text-text-muted mb-4">
            {chartType === 'executions' ? 'Executions Over Time' : 'Success Rate Over Time'}
          </h4>
          <div className="h-[200px]">
            {lineChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke={CHART_COLORS.grid}
                    vertical={false}
                  />
                  <XAxis
                    dataKey="time"
                    stroke={CHART_COLORS.text}
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis
                    stroke={CHART_COLORS.text}
                    fontSize={11}
                    tickLine={false}
                    domain={chartType === 'successRate' ? [0, 100] : undefined}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#161b22',
                      border: '1px solid #30363d',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#c9d1d9' }}
                    itemStyle={{ color: '#8b949e' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={CHART_COLORS.secondary}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-text-muted text-sm">
                No time series data available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Stat card component for summary metrics
 */
interface StatCardProps {
  label: string;
  value: string;
  color?: 'green' | 'yellow' | 'red';
}

function StatCard({ label, value, color }: StatCardProps) {
  return (
    <div className="bg-bg-secondary rounded-lg border border-border-primary p-4">
      <p className="text-xs text-text-muted">{label}</p>
      <p
        className={clsx(
          'text-2xl font-bold mt-1',
          color === 'green' && 'text-status-success',
          color === 'yellow' && 'text-status-warning',
          color === 'red' && 'text-status-error',
          !color && 'text-text-primary'
        )}
      >
        {value}
      </p>
    </div>
  );
}
