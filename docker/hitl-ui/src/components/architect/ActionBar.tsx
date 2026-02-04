/**
 * ActionBar - Bottom action bar for Architect Board
 * P10-F01 Architect Board Canvas - Phase 4 (T15)
 * P10-F02 Diagram Translation - Phase 4 (T18) - Enable Translate dropdown
 *
 * Provides action buttons for the canvas:
 * - Save Draft (disabled, Coming in F03)
 * - History (disabled, Coming in F03)
 * - Export SVG (enabled)
 * - Translate dropdown (enabled in F02)
 */

import { useState, useRef, useEffect } from 'react';
import {
  DocumentArrowDownIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  LanguageIcon,
  ChevronDownIcon,
  PhotoIcon,
  CodeBracketIcon,
  Squares2X2Icon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useArchitectStore } from '../../stores/architectStore';
import type { TranslationFormat } from '../../api/types/architect';

export interface ActionBarProps {
  /** Custom class name */
  className?: string;
}

/** Translation format options */
interface TranslateOption {
  format: TranslationFormat;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TRANSLATE_OPTIONS: TranslateOption[] = [
  {
    format: 'png',
    label: 'PNG Image',
    description: 'Generate a PNG image using AI',
    icon: PhotoIcon,
  },
  {
    format: 'mmd',
    label: 'Mermaid',
    description: 'Convert to Mermaid diagram syntax',
    icon: CodeBracketIcon,
  },
  {
    format: 'drawio',
    label: 'Draw.io XML',
    description: 'Convert to Draw.io/diagrams.net format',
    icon: Squares2X2Icon,
  },
];

/**
 * ActionBar displays action buttons at the bottom of the Architect Board page.
 * Includes Export SVG and Translate dropdown for format conversions.
 */
export default function ActionBar({ className }: ActionBarProps) {
  // Store state
  const isExporting = useArchitectStore((state) => state.isExporting);
  const performExport = useArchitectStore((state) => state.performExport);
  const exportedSvg = useArchitectStore((state) => state.exportedSvg);
  const isTranslating = useArchitectStore((state) => state.isTranslating);
  const translateTo = useArchitectStore((state) => state.translateTo);

  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle export button
  const handleExport = () => {
    performExport();
  };

  // Handle translate option selection
  const handleTranslate = (format: TranslationFormat) => {
    setIsDropdownOpen(false);
    translateTo(format);
  };

  // Translate button is disabled when no SVG or during translation
  const isTranslateDisabled = !exportedSvg || isTranslating;

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

        {/* Translate Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => !isTranslateDisabled && setIsDropdownOpen(!isDropdownOpen)}
            disabled={isTranslateDisabled}
            title={!exportedSvg ? 'Export SVG first' : isTranslating ? 'Translating...' : 'Translate diagram'}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 text-sm',
              'border border-border-primary rounded',
              'transition-colors',
              isTranslateDisabled
                ? 'text-text-muted opacity-50 cursor-not-allowed'
                : 'text-text-primary hover:bg-bg-tertiary'
            )}
            aria-label="Translate"
            aria-expanded={isDropdownOpen}
            aria-haspopup="true"
            data-testid="translate-button"
          >
            {isTranslating ? (
              <span
                className="h-4 w-4 border-2 border-accent-blue border-t-transparent rounded-full animate-spin"
                data-testid="translate-spinner"
              />
            ) : (
              <LanguageIcon className="h-4 w-4" />
            )}
            <span>{isTranslating ? 'Translating...' : 'Translate'}</span>
            <ChevronDownIcon className={clsx('h-3 w-3 transition-transform', isDropdownOpen && 'rotate-180')} />
          </button>

          {/* Dropdown menu */}
          {isDropdownOpen && (
            <div
              className={clsx(
                'absolute right-0 bottom-full mb-1 w-56',
                'bg-bg-secondary border border-border-primary rounded-lg shadow-lg',
                'py-1 z-50'
              )}
              role="menu"
              aria-orientation="vertical"
              data-testid="translate-dropdown"
            >
              {TRANSLATE_OPTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.format}
                    onClick={() => handleTranslate(option.format)}
                    className={clsx(
                      'w-full flex items-start gap-3 px-3 py-2',
                      'text-left hover:bg-bg-tertiary transition-colors'
                    )}
                    role="menuitem"
                    data-testid={`translate-option-${option.format}`}
                  >
                    <Icon className="h-5 w-5 text-text-muted mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-text-primary">
                        {option.label}
                      </div>
                      <div className="text-xs text-text-muted">
                        {option.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
