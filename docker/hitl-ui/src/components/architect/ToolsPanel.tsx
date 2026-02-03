/**
 * ToolsPanel - Collapsible panel for drawing tools
 * P10-F01 Architect Board Canvas - Phase 2 (T07)
 */

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useArchitectStore } from '../../stores/architectStore';

export interface ToolsPanelProps {
  /** Custom class name */
  className?: string;
}

/**
 * ToolsPanel displays drawing tools in a collapsible side panel.
 * Connects to architectStore for panel visibility state.
 */
export default function ToolsPanel({ className }: ToolsPanelProps) {
  const isToolsPanelOpen = useArchitectStore((state) => state.isToolsPanelOpen);
  const toggleToolsPanel = useArchitectStore((state) => state.toggleToolsPanel);

  return (
    <div
      className={clsx(
        'flex flex-col bg-bg-secondary border-r border-border-primary',
        'transition-all duration-300',
        isToolsPanelOpen ? 'w-60' : 'w-12',
        className
      )}
      data-testid="tools-panel"
    >
      {/* Header with toggle button */}
      <div
        className={clsx(
          'flex items-center p-2 border-b border-border-primary',
          isToolsPanelOpen ? 'justify-between' : 'justify-center'
        )}
      >
        {isToolsPanelOpen && (
          <h3 className="text-sm font-semibold text-text-primary">Drawing Tools</h3>
        )}
        <button
          onClick={toggleToolsPanel}
          className={clsx(
            'p-1 rounded hover:bg-bg-tertiary transition-colors',
            'text-text-muted hover:text-text-primary'
          )}
          aria-label={isToolsPanelOpen ? 'Collapse tools panel' : 'Expand tools panel'}
        >
          {isToolsPanelOpen ? (
            <ChevronLeftIcon className="h-5 w-5" />
          ) : (
            <ChevronRightIcon className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Tools content (placeholder for future F02 features) */}
      {isToolsPanelOpen && (
        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs text-text-muted text-center py-4">
            Drawing tools provided by Excalidraw toolbar
          </div>
        </div>
      )}
    </div>
  );
}
