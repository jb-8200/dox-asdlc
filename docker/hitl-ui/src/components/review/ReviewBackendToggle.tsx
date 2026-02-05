/**
 * ReviewBackendToggle Component
 *
 * Toggle switch for selecting between mock and real data sources
 * on the Code Review page. Persists selection to localStorage.
 * Follows the DataSourceToggle pattern from P05-F13.
 */

import { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { useReviewStore, type ReviewDataSource } from '../../stores/reviewStore';
import { apiClient } from '../../api/client';

export interface ReviewBackendToggleProps {
  /** Custom class name */
  className?: string;
  /** Whether to show a health indicator when in "Real" mode */
  showHealth?: boolean;
}

type HealthStatus = 'healthy' | 'unhealthy' | 'unknown' | 'checking';

export default function ReviewBackendToggle({
  className,
  showHealth = true,
}: ReviewBackendToggleProps) {
  const { dataSource, setDataSource } = useReviewStore();
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('unknown');

  const checkHealth = useCallback(async () => {
    setHealthStatus('checking');
    try {
      const response = await apiClient.get('/health', { timeout: 5000 });
      if (response.status === 200) {
        setHealthStatus('healthy');
      } else {
        setHealthStatus('unhealthy');
      }
    } catch {
      setHealthStatus('unhealthy');
    }
  }, []);

  useEffect(() => {
    if (dataSource === 'real' && showHealth) {
      checkHealth();
    }
  }, [dataSource, showHealth, checkHealth]);

  function getHealthColor(): string {
    if (dataSource === 'mock') return 'bg-green-500';
    switch (healthStatus) {
      case 'healthy':
        return 'bg-green-500';
      case 'unhealthy':
        return 'bg-red-500';
      case 'checking':
        return 'bg-yellow-500 animate-pulse';
      default:
        return 'bg-yellow-500';
    }
  }

  function getHealthLabel(): string {
    if (dataSource === 'mock') return 'Mock backend status: healthy';
    return `API status: ${healthStatus}`;
  }

  return (
    <div
      data-testid="review-backend-toggle"
      className={clsx('flex items-center gap-2', className)}
    >
      {showHealth && (
        <div
          className={clsx(
            'h-2.5 w-2.5 rounded-full flex-shrink-0',
            getHealthColor()
          )}
          data-testid="review-health-indicator"
          role="status"
          aria-label={getHealthLabel()}
          title={getHealthLabel()}
        />
      )}
      <span className="text-sm text-text-muted">Data Source:</span>
      <div className="flex rounded-lg border border-border-primary overflow-hidden">
        <button
          data-testid="review-source-mock"
          type="button"
          className={clsx(
            'px-3 py-1 text-sm transition-colors',
            dataSource === 'mock'
              ? 'bg-accent-teal/20 text-accent-teal font-medium'
              : 'bg-bg-primary text-text-secondary hover:bg-bg-tertiary'
          )}
          onClick={() => setDataSource('mock')}
        >
          Mock
        </button>
        <button
          data-testid="review-source-real"
          type="button"
          className={clsx(
            'px-3 py-1 text-sm transition-colors border-l border-border-primary',
            dataSource === 'real'
              ? 'bg-accent-teal/20 text-accent-teal font-medium'
              : 'bg-bg-primary text-text-secondary hover:bg-bg-tertiary'
          )}
          onClick={() => setDataSource('real')}
        >
          Real
        </button>
      </div>
    </div>
  );
}

export { ReviewBackendToggle };
