/**
 * AgentStatusCard - Individual agent status card component (P05-F12 T05)
 *
 * Features:
 * - Type icon based on agent type
 * - Status badge (color-coded)
 * - Progress bar when running
 * - Current task name
 * - Click to select
 */

import clsx from 'clsx';
import {
  CodeBracketIcon,
  ComputerDesktopIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  ServerIcon,
  BeakerIcon,
  PaintBrushIcon,
  CommandLineIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';
import type { AgentStatus, AgentType } from '../../types/agents';
import { STATUS_COLORS, STATUS_LABELS, AGENT_TYPE_LABELS } from '../../types/agents';

export interface AgentStatusCardProps {
  /** Agent status data */
  agent: AgentStatus;
  /** Whether this card is selected */
  isSelected?: boolean;
  /** Click handler */
  onClick?: (agentId: string) => void;
  /** Custom class name */
  className?: string;
}

/**
 * Get icon component for agent type
 */
function getAgentIcon(type: AgentType): React.ComponentType<React.SVGProps<SVGSVGElement>> {
  switch (type) {
    case 'backend':
      return CodeBracketIcon;
    case 'frontend':
      return ComputerDesktopIcon;
    case 'planner':
      return DocumentTextIcon;
    case 'reviewer':
      return MagnifyingGlassIcon;
    case 'orchestrator':
      return CpuChipIcon;
    case 'devops':
      return ServerIcon;
    case 'test':
      return BeakerIcon;
    case 'design':
      return PaintBrushIcon;
    case 'coding':
      return CommandLineIcon;
    case 'discovery':
      return LightBulbIcon;
    default:
      return CpuChipIcon;
  }
}

export default function AgentStatusCard({
  agent,
  isSelected = false,
  onClick,
  className,
}: AgentStatusCardProps) {
  const Icon = getAgentIcon(agent.agent_type);
  const statusLabel = STATUS_LABELS[agent.status];
  const statusColor = STATUS_COLORS[agent.status];
  const typeLabel = AGENT_TYPE_LABELS[agent.agent_type];
  const isActive = agent.status === 'running';
  const showProgress = isActive && agent.progress > 0;

  const handleClick = () => {
    if (onClick) {
      onClick(agent.agent_id);
    }
  };

  return (
    <div
      data-testid="agent-card"
      role="article"
      aria-label={`${typeLabel} agent ${agent.agent_id} - ${statusLabel}`}
      onClick={handleClick}
      className={clsx(
        'relative p-4 rounded-lg border bg-bg-secondary transition-all cursor-pointer',
        'hover:bg-bg-tertiary/50',
        isSelected
          ? 'border-accent-blue ring-2 ring-accent-blue'
          : 'border-border-primary hover:border-border-secondary',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={clsx(
              'p-2 rounded-lg',
              isActive ? 'bg-accent-blue/10' : 'bg-bg-tertiary'
            )}
          >
            <Icon
              className={clsx(
                'h-5 w-5',
                isActive ? 'text-accent-blue' : 'text-text-muted'
              )}
            />
          </div>
          <div>
            <h3 className="text-sm font-medium text-text-primary">
              {typeLabel}
            </h3>
            <p className="text-xs text-text-muted">{agent.agent_id}</p>
          </div>
        </div>

        {/* Status Badge */}
        <span
          data-testid="status-badge"
          className={clsx(
            'px-2 py-0.5 rounded-full text-xs font-medium text-white',
            statusColor
          )}
        >
          {statusLabel}
        </span>
      </div>

      {/* Task Info */}
      <div className="space-y-2">
        <p
          className={clsx(
            'text-sm truncate',
            agent.currentTask ? 'text-text-secondary' : 'text-text-muted italic'
          )}
          title={agent.currentTask || undefined}
        >
          {agent.currentTask || 'No active task'}
        </p>

        {/* Progress Bar */}
        {showProgress && (
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Progress</span>
              <span className="text-xs font-medium text-text-secondary">
                {agent.progress}%
              </span>
            </div>
            <div className="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
              <div
                data-testid="progress-bar"
                className="h-full bg-accent-blue rounded-full transition-all duration-300"
                style={{ width: `${agent.progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Running indicator pulse */}
      {isActive && (
        <div className="absolute top-3 right-3">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-blue opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-blue" />
          </span>
        </div>
      )}
    </div>
  );
}
