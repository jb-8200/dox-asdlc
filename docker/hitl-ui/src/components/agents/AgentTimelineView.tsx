/**
 * AgentTimelineView - Gantt-style timeline for agent executions (P05-F12 T09)
 *
 * Features:
 * - Horizontal timeline with agent rows
 * - Task blocks showing duration
 * - Color coded by status
 * - Hover tooltips for task details
 */

import { useState, useMemo, useCallback } from 'react';
import clsx from 'clsx';
import type { TimelineData, TaskExecution, MetricsTimeRange, AgentType } from '../../types/agents';
import { METRICS_TIME_RANGE_OPTIONS, AGENT_TYPE_LABELS } from '../../types/agents';
import { formatDuration } from '../../api/agents';

export interface AgentTimelineViewProps {
  /** Timeline data */
  data?: TimelineData | null;
  /** Current time range */
  timeRange?: MetricsTimeRange;
  /** Loading state */
  isLoading?: boolean;
  /** Callback when time range changes */
  onTimeRangeChange?: (range: MetricsTimeRange) => void;
  /** Custom class name */
  className?: string;
}

/** Status to color mapping for task blocks */
const STATUS_BLOCK_COLORS: Record<TaskExecution['status'], string> = {
  completed: 'bg-status-success',
  running: 'bg-accent-blue',
  failed: 'bg-status-error',
};

/**
 * Calculate position and width of a task block as percentages
 */
function calculateBlockStyle(
  execution: TaskExecution,
  startTime: Date,
  endTime: Date
): { left: string; width: string } {
  const totalDuration = endTime.getTime() - startTime.getTime();
  const taskStart = new Date(execution.startTime).getTime();
  const taskEnd = execution.endTime
    ? new Date(execution.endTime).getTime()
    : endTime.getTime(); // If running, extend to now

  const left = ((taskStart - startTime.getTime()) / totalDuration) * 100;
  const width = ((taskEnd - taskStart) / totalDuration) * 100;

  return {
    left: `${Math.max(0, left)}%`,
    width: `${Math.min(100 - left, Math.max(2, width))}%`, // Min 2% width for visibility
  };
}

/**
 * Task block component with tooltip
 */
interface TaskBlockProps {
  execution: TaskExecution;
  startTime: Date;
  endTime: Date;
}

function TaskBlock({ execution, startTime, endTime }: TaskBlockProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const style = calculateBlockStyle(execution, startTime, endTime);
  const color = STATUS_BLOCK_COLORS[execution.status];

  const handleMouseEnter = useCallback(() => setShowTooltip(true), []);
  const handleMouseLeave = useCallback(() => setShowTooltip(false), []);

  return (
    <div
      data-testid="task-block"
      className={clsx(
        'absolute top-1 bottom-1 rounded cursor-pointer transition-opacity',
        color,
        execution.status === 'running' && 'animate-pulse'
      )}
      style={{ left: style.left, width: style.width }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Tooltip */}
      <div
        data-testid="task-tooltip"
        className={clsx(
          'absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-2',
          'px-3 py-2 rounded-lg bg-bg-primary border border-border-primary shadow-lg',
          'text-xs whitespace-nowrap transition-opacity duration-200',
          showTooltip ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
      >
        <p className="font-medium text-text-primary">{execution.taskName}</p>
        <p className="text-text-muted mt-1">
          Status: <span className="capitalize">{execution.status}</span>
        </p>
        {execution.durationMs && (
          <p className="text-text-muted">
            Duration: {formatDuration(execution.durationMs)}
          </p>
        )}
      </div>
    </div>
  );
}

export default function AgentTimelineView({
  data,
  timeRange = '1h',
  isLoading = false,
  onTimeRangeChange,
  className,
}: AgentTimelineViewProps) {
  // Parse time range
  const { startTime, endTime } = useMemo(() => {
    if (data) {
      return {
        startTime: new Date(data.startTime),
        endTime: new Date(data.endTime),
      };
    }
    return { startTime: new Date(), endTime: new Date() };
  }, [data]);

  // Generate time labels for the axis
  const timeLabels = useMemo(() => {
    if (!data) return [];

    const labels: string[] = [];
    const totalDuration = endTime.getTime() - startTime.getTime();
    const numLabels = 6;

    for (let i = 0; i <= numLabels; i++) {
      const timestamp = new Date(startTime.getTime() + (totalDuration * i) / numLabels);
      labels.push(
        timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      );
    }

    return labels;
  }, [data, startTime, endTime]);

  // Loading state
  if (isLoading && !data) {
    return (
      <div
        data-testid="timeline-loading"
        className={clsx('animate-pulse space-y-3', className)}
      >
        <div className="h-8 w-48 bg-bg-tertiary rounded" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="h-6 w-24 bg-bg-tertiary rounded" />
            <div className="h-8 flex-1 bg-bg-tertiary rounded" />
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (!data || data.agents.length === 0) {
    return (
      <div
        data-testid="timeline-empty"
        className={clsx(
          'flex flex-col items-center justify-center py-12 px-4 text-center',
          'bg-bg-secondary rounded-lg border border-border-primary',
          className
        )}
      >
        <p className="text-text-muted">No timeline data available</p>
        <p className="text-sm text-text-muted mt-1">
          Task executions will appear here as agents work
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="timeline-view"
      role="img"
      aria-label="Agent execution timeline"
      className={clsx('space-y-4', className)}
    >
      {/* Header with Time Range Selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary">
          Execution Timeline
        </h3>
        <div
          data-testid="timeline-time-range"
          className="flex items-center gap-1"
          role="group"
          aria-label="Time range selection"
        >
          {METRICS_TIME_RANGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              data-testid={`timeline-range-${option.value}`}
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

      {/* Timeline */}
      <div className="bg-bg-secondary rounded-lg border border-border-primary p-4">
        {/* Time axis */}
        <div className="flex items-center mb-4 pl-28">
          {timeLabels.map((label, index) => (
            <span
              key={index}
              className="flex-1 text-xs text-text-muted text-center first:text-left last:text-right"
            >
              {label}
            </span>
          ))}
        </div>

        {/* Agent rows */}
        <div className="space-y-2">
          {data.agents.map((agent) => (
            <div
              key={agent.agentId}
              data-testid="agent-row"
              className="flex items-center gap-4"
            >
              {/* Agent label */}
              <div className="w-24 flex-shrink-0">
                <span className="text-sm font-medium text-text-primary">
                  {AGENT_TYPE_LABELS[agent.agentType]}
                </span>
              </div>

              {/* Timeline track */}
              <div className="flex-1 relative h-8 bg-bg-tertiary/30 rounded">
                {agent.executions.map((execution) => (
                  <TaskBlock
                    key={execution.id}
                    execution={execution}
                    startTime={startTime}
                    endTime={endTime}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border-primary">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-status-success" />
            <span className="text-xs text-text-muted">Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-accent-blue" />
            <span className="text-xs text-text-muted">Running</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-status-error" />
            <span className="text-xs text-text-muted">Failed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
