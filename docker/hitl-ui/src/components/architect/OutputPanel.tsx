/**
 * OutputPanel - Collapsible panel for export outputs
 * P10-F01 Architect Board Canvas - Phase 2 (T09)
 * P10-F02 Diagram Translation - Phase 4 (T20) - Enable all format tabs
 */

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useArchitectStore } from '../../stores/architectStore';
import type { ExportFormat } from '../../api/types/architect';
import FormatTabContent from './FormatTabContent';

export interface OutputPanelProps {
  /** Custom class name */
  className?: string;
}

/** Tab configuration for format tabs */
interface TabConfig {
  id: ExportFormat;
  label: string;
}

const TABS: TabConfig[] = [
  { id: 'svg', label: 'SVG' },
  { id: 'png', label: 'PNG' },
  { id: 'mmd', label: 'Mermaid' },
  { id: 'drawio', label: 'Draw.io' },
];

/**
 * OutputPanel displays export outputs in a collapsible side panel.
 * Connects to architectStore for panel visibility state and translation content.
 */
export default function OutputPanel({ className }: OutputPanelProps) {
  // Store state
  const isOutputPanelOpen = useArchitectStore((state) => state.isOutputPanelOpen);
  const toggleOutputPanel = useArchitectStore((state) => state.toggleOutputPanel);
  const activeOutputTab = useArchitectStore((state) => state.activeOutputTab);
  const setActiveOutputTab = useArchitectStore((state) => state.setActiveOutputTab);

  // Export and translation state
  const exportedSvg = useArchitectStore((state) => state.exportedSvg);
  const isTranslating = useArchitectStore((state) => state.isTranslating);
  const translationError = useArchitectStore((state) => state.translationError);
  const translatedContent = useArchitectStore((state) => state.translatedContent);

  /**
   * Get the content for a specific format tab
   */
  const getTabContent = (format: ExportFormat): string | null => {
    switch (format) {
      case 'svg':
        return exportedSvg;
      case 'png':
        return translatedContent.png;
      case 'mmd':
        return translatedContent.mmd;
      case 'drawio':
        return translatedContent.drawio;
      default:
        return null;
    }
  };

  /**
   * Check if a tab has content ready
   */
  const hasContent = (format: ExportFormat): boolean => {
    return getTabContent(format) !== null;
  };

  /**
   * Check if a tab is currently loading (translating)
   */
  const isTabLoading = (format: ExportFormat): boolean => {
    // Only show loading for the active tab during translation
    return isTranslating && activeOutputTab === format && format !== 'svg';
  };

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
                aria-selected={activeOutputTab === tab.id}
                onClick={() => setActiveOutputTab(tab.id)}
                className={clsx(
                  'flex-1 px-2 py-2 text-xs font-medium transition-colors relative',
                  activeOutputTab === tab.id
                    ? 'text-accent-blue border-b-2 border-accent-blue'
                    : 'text-text-muted hover:text-text-secondary'
                )}
                data-testid={`tab-${tab.id}`}
              >
                <span className="flex items-center justify-center gap-1">
                  {tab.label}
                  {/* Ready badge */}
                  {hasContent(tab.id) && tab.id !== 'svg' && (
                    <span
                      className="inline-block w-2 h-2 bg-status-success rounded-full"
                      title="Ready"
                      data-testid={`badge-${tab.id}`}
                    />
                  )}
                  {/* Loading indicator */}
                  {isTabLoading(tab.id) && (
                    <span
                      className="inline-block w-3 h-3 border border-accent-blue border-t-transparent rounded-full animate-spin"
                      data-testid={`loading-${tab.id}`}
                    />
                  )}
                </span>
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div
            className="flex-1 overflow-y-auto"
            data-testid="export-preview-placeholder"
          >
            <FormatTabContent
              content={getTabContent(activeOutputTab)}
              format={activeOutputTab}
              loading={isTabLoading(activeOutputTab)}
              error={activeOutputTab !== 'svg' ? translationError : null}
            />
          </div>
        </>
      )}
    </div>
  );
}
