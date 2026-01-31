/**
 * AgentStatusGrid - Grid of agent status cards (P05-F12 T06)
 *
 * Features:
 * - Responsive grid layout
 * - Click to select agent
 * - Loading state with skeletons
 * - Empty state message
 */

import clsx from 'clsx';
import AgentStatusCard from './AgentStatusCard';
import type { AgentStatus } from '../../types/agents';

export interface AgentStatusGridProps {
  /** List of agents to display */
  agents: AgentStatus[];
  /** Currently selected agent ID */
  selectedAgentId?: string | null;
  /** Callback when an agent is selected */
  onSelect?: (agentId: string) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Loading skeleton for agent card
 */
function AgentCardSkeleton() {
  return (
    <div
      data-testid="skeleton-card"
      className="p-4 rounded-lg border border-border-primary bg-bg-secondary animate-pulse"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-bg-tertiary" />
          <div className="space-y-1.5">
            <div className="h-4 w-20 bg-bg-tertiary rounded" />
            <div className="h-3 w-32 bg-bg-tertiary rounded" />
          </div>
        </div>
        <div className="h-5 w-16 bg-bg-tertiary rounded-full" />
      </div>
      <div className="space-y-2">
        <div className="h-4 w-full bg-bg-tertiary rounded" />
        <div className="h-1.5 w-full bg-bg-tertiary rounded-full" />
      </div>
    </div>
  );
}

export default function AgentStatusGrid({
  agents,
  selectedAgentId,
  onSelect,
  isLoading = false,
  className,
}: AgentStatusGridProps) {
  // Loading state
  if (isLoading && agents.length === 0) {
    return (
      <div
        data-testid="loading-skeleton"
        className={clsx(
          'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
          className
        )}
      >
        {Array.from({ length: 6 }).map((_, index) => (
          <AgentCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  // Empty state
  if (agents.length === 0) {
    return (
      <div
        data-testid="empty-state"
        className={clsx(
          'flex flex-col items-center justify-center py-12 px-4 text-center',
          'bg-bg-secondary rounded-lg border border-border-primary',
          className
        )}
      >
        <p className="text-text-muted">No agents found</p>
        <p className="text-sm text-text-muted mt-1">
          Agents will appear here when they connect
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="agent-status-grid"
      role="list"
      aria-label="Agent status grid"
      className={clsx(
        'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
        className
      )}
    >
      {agents.map((agent) => (
        <AgentStatusCard
          key={agent.agent_id}
          agent={agent}
          isSelected={selectedAgentId === agent.agent_id}
          onClick={onSelect}
        />
      ))}
    </div>
  );
}
