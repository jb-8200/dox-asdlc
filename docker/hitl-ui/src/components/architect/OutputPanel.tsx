/**
 * OutputPanel - Collapsible panel for export outputs
 * P10-F01 Architect Board Canvas - Phase 2 (T09)
 */

import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useArchitectStore } from '../../stores/architectStore';
import type { ExportFormat } from '../../api/types/architect';
import ExportPreview from './ExportPreview';

export interface OutputPanelProps {
  /** Custom class name */
  className?: string;
}

/** Tab configuration */
interface TabConfig {
  id: ExportFormat;
  label: string;
  enabled: boolean;
}

const TABS: TabConfig[] = [
  { id: 'svg', label: 'SVG', enabled: true },
  { id: 'png', label: 'PNG', enabled: false },
  { id: 'mmd', label: 'MMD', enabled: false },
  { id: 'drawio', label: 'DrawIO', enabled: false },
];

/**
 * OutputPanel displays export outputs in a collapsible side panel.
 * Connects to architectStore for panel visibility state.
 */
export default function OutputPanel({ className }: OutputPanelProps) {
  const isOutputPanelOpen = useArchitectStore((state) => state.isOutputPanelOpen);
  const toggleOutputPanel = useArchitectStore((state) => state.toggleOutputPanel);
  const [activeTab, setActiveTab] = useState<ExportFormat>('svg');

  return (
    <div
      className={clsx(
        'flex flex-col bg-bg-secondary border-l border-border-primary',
        'transition-all duration-300',
        isOutputPanelOpen ? 'w-80' : 'w-12',
        className
      )}
      data-testid="output-panel"
    >
      {/* Header with toggle button */}
      <div
        className={clsx(
          'flex items-center p-2 border-b border-border-primary',
          isOutputPanelOpen ? 'justify-between' : 'justify-center'
        )}
      >
        <button
          onClick={toggleOutputPanel}
          className={clsx(
            'p-1 rounded hover:bg-bg-tertiary transition-colors',
            'text-text-muted hover:text-text-primary'
          )}
          aria-label={isOutputPanelOpen ? 'Collapse output panel' : 'Expand output panel'}
        >
          {isOutputPanelOpen ? (
            <ChevronRightIcon className="h-5 w-5" />
          ) : (
            <ChevronLeftIcon className="h-5 w-5" />
          )}
        </button>
        {isOutputPanelOpen && (
          <h3 className="text-sm font-semibold text-text-primary">Output</h3>
        )}
      </div>

      {/* Tabs and content */}
      {isOutputPanelOpen && (
        <>
          {/* Tab bar */}
          <div
            className="flex border-b border-border-primary"
            role="tablist"
            aria-label="Export format tabs"
          >
            {TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                disabled={!tab.enabled}
                title={!tab.enabled ? 'Coming in F02' : undefined}
                onClick={() => tab.enabled && setActiveTab(tab.id)}
                className={clsx(
                  'flex-1 px-2 py-2 text-xs font-medium transition-colors',
                  activeTab === tab.id && tab.enabled
                    ? 'text-accent-blue border-b-2 border-accent-blue'
                    : 'text-text-muted hover:text-text-secondary',
                  !tab.enabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Export content */}
          <div
            className="flex-1 overflow-y-auto"
            data-testid="export-preview-placeholder"
          >
            {activeTab === 'svg' ? (
              <ExportPreview />
            ) : (
              <div className="flex items-center justify-center h-full min-h-[200px] p-2">
                <div className="flex items-center justify-center h-full border border-dashed border-border-primary rounded-lg w-full">
                  <span className="text-xs text-text-muted">
                    {activeTab.toUpperCase()} preview will appear here
                  </span>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
