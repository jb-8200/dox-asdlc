/**
 * ActionBar - Bottom action bar for Architect Board
 * P10-F01 Architect Board Canvas - Phase 4 (T15)
 *
 * Provides action buttons for the canvas:
 * - Save Draft (disabled, Coming in F03)
 * - History (disabled, Coming in F03)
 * - Export SVG (enabled)
 * - Translate dropdown (disabled, Coming in F02)
 */

import {
  DocumentArrowDownIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  LanguageIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useArchitectStore } from '../../stores/architectStore';

export interface ActionBarProps {
  /** Custom class name */
  className?: string;
}

/**
 * ActionBar displays action buttons at the bottom of the Architect Board page.
 * Some buttons are disabled placeholders for future features.
 */
export default function ActionBar({ className }: ActionBarProps) {
  const isExporting = useArchitectStore((state) => state.isExporting);
  const performExport = useArchitectStore((state) => state.performExport);

  const handleExport = () => {
    performExport();
  };

  return (
    <div
      className={clsx(
        'flex items-center justify-between px-4 py-2',
        'bg-bg-secondary border-t border-border-primary',
        className
      )}
      data-testid="action-bar"
    >
      {/* Left side buttons */}
      <div className="flex items-center gap-2">
        {/* Save Draft - Coming in F03 */}
        <button
          type="button"
          disabled
          title="Coming in F03"
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 text-sm',
            'border border-border-primary rounded',
            'text-text-muted',
            'opacity-50 cursor-not-allowed'
          )}
          aria-label="Save Draft"
        >
          <DocumentArrowDownIcon className="h-4 w-4" />
          <span>Save Draft</span>
        </button>

        {/* History - Coming in F03 */}
        <button
          type="button"
          disabled
          title="Coming in F03"
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 text-sm',
            'border border-border-primary rounded',
            'text-text-muted',
            'opacity-50 cursor-not-allowed'
          )}
          aria-label="History"
        >
          <ClockIcon className="h-4 w-4" />
          <span>History</span>
        </button>
      </div>

      {/* Right side buttons */}
      <div className="flex items-center gap-2">
        {/* Export SVG - Enabled */}
        <button
          type="button"
          onClick={handleExport}
          disabled={isExporting}
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 text-sm',
            'bg-accent-blue text-white rounded',
            'hover:bg-blue-700 transition-colors',
            isExporting && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={isExporting ? 'Exporting' : 'Export SVG'}
        >
          <ArrowDownTrayIcon className="h-4 w-4" />
          <span>{isExporting ? 'Exporting...' : 'Export SVG'}</span>
        </button>

        {/* Translate - Coming in F02 */}
        <button
          type="button"
          disabled
          title="Coming in F02"
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 text-sm',
            'border border-border-primary rounded',
            'text-text-muted',
            'opacity-50 cursor-not-allowed'
          )}
          aria-label="Translate"
        >
          <LanguageIcon className="h-4 w-4" />
          <span>Translate</span>
        </button>
      </div>
    </div>
  );
}
