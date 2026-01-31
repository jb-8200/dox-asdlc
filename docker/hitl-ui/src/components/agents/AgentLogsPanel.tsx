/**
 * AgentLogsPanel - Log viewer with filters (P05-F12 T07)
 *
 * Features:
 * - Log list with level badges
 * - Level filter dropdown
 * - Search input
 * - Scrollable container
 * - Loading and empty states
 */

import { useMemo } from 'react';
import clsx from 'clsx';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import type { AgentLog, LogLevel } from '../../types/agents';
import { LOG_LEVEL_COLORS } from '../../types/agents';

export interface AgentLogsPanelProps {
  /** Log entries to display */
  logs: AgentLog[];
  /** Selected level filter */
  levelFilter?: LogLevel | null;
  /** Search term */
  searchTerm?: string;
  /** Loading state */
  isLoading?: boolean;
  /** Callback when level filter changes */
  onLevelChange?: (level: LogLevel | null) => void;
  /** Callback when search term changes */
  onSearchChange?: (term: string) => void;
  /** Custom class name */
  className?: string;
}

const LOG_LEVELS: LogLevel[] = ['debug', 'info', 'warn', 'error'];

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Single log entry component
 */
function LogEntry({ log }: { log: AgentLog }) {
  const levelColor = LOG_LEVEL_COLORS[log.level];

  return (
    <div
      data-testid="log-entry"
      className="flex items-start gap-3 py-2 px-3 hover:bg-bg-tertiary/30 rounded"
    >
      <span className="text-xs text-text-muted font-mono whitespace-nowrap">
        {formatTimestamp(log.timestamp)}
      </span>
      <span
        className={clsx(
          'text-xs font-medium uppercase min-w-[45px]',
          levelColor
        )}
      >
        {log.level}
      </span>
      <span className="text-sm text-text-secondary flex-1 break-words">
        {log.message}
      </span>
    </div>
  );
}

export default function AgentLogsPanel({
  logs,
  levelFilter,
  searchTerm = '',
  isLoading = false,
  onLevelChange,
  onSearchChange,
  className,
}: AgentLogsPanelProps) {
  // Filter logs based on level and search
  const filteredLogs = useMemo(() => {
    let result = logs;

    if (levelFilter) {
      result = result.filter((log) => log.level === levelFilter);
    }

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      result = result.filter((log) =>
        log.message.toLowerCase().includes(searchLower)
      );
    }

    return result;
  }, [logs, levelFilter, searchTerm]);

  const handleLevelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onLevelChange?.(value === '' ? null : (value as LogLevel));
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSearchChange?.(e.target.value);
  };

  return (
    <div
      data-testid="logs-panel"
      className={clsx(
        'flex flex-col bg-bg-secondary rounded-lg border border-border-primary',
        className
      )}
    >
      {/* Filters */}
      <div className="flex items-center gap-3 p-3 border-b border-border-primary">
        {/* Level Filter */}
        <select
          data-testid="level-filter"
          value={levelFilter || ''}
          onChange={handleLevelChange}
          className="px-3 py-1.5 text-sm bg-bg-tertiary border border-border-primary rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-blue"
        >
          <option value="">All Levels</option>
          {LOG_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>

        {/* Search */}
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            data-testid="log-search"
            type="text"
            value={searchTerm}
            onChange={handleSearchChange}
            placeholder="Search logs..."
            aria-label="Search logs"
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-bg-tertiary border border-border-primary rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent-blue"
          />
        </div>
      </div>

      {/* Log List */}
      <div
        data-testid="log-list"
        role="log"
        className="flex-1 overflow-auto max-h-[400px] min-h-[200px]"
      >
        {isLoading ? (
          <div
            data-testid="logs-loading"
            className="flex items-center justify-center h-full"
          >
            <div className="space-y-2 w-full px-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-3 py-2 animate-pulse">
                  <div className="h-4 w-16 bg-bg-tertiary rounded" />
                  <div className="h-4 w-12 bg-bg-tertiary rounded" />
                  <div className="h-4 flex-1 bg-bg-tertiary rounded" />
                </div>
              ))}
            </div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div
            data-testid="empty-logs"
            className="flex flex-col items-center justify-center h-full text-text-muted"
          >
            <p>No logs available</p>
            {(levelFilter || searchTerm) && (
              <p className="text-sm mt-1">Try adjusting your filters</p>
            )}
          </div>
        ) : (
          <div className="py-1">
            {filteredLogs.map((log) => (
              <LogEntry key={log.id} log={log} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
