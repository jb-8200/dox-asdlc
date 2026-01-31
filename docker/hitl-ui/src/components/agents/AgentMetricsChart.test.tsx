/**
 * Unit tests for AgentMetricsChart component (P05-F12 T08)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AgentMetricsChart from './AgentMetricsChart';
import type { AgentMetricsResponse, MetricsTimeRange } from '../../types/agents';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('AgentMetricsChart', () => {
  const mockMetrics: AgentMetricsResponse = {
    summary: {
      totalExecutions: 273,
      overallSuccessRate: 92,
      avgDurationMs: 15000,
      totalTokens: 738000,
      byAgentType: {
        backend: { executionCount: 45, successRate: 91, avgDurationMs: 12500 },
        frontend: { executionCount: 38, successRate: 95, avgDurationMs: 8200 },
        reviewer: { executionCount: 62, successRate: 98, avgDurationMs: 4500 },
        planner: { executionCount: 25, successRate: 96, avgDurationMs: 15000 },
        orchestrator: { executionCount: 30, successRate: 93, avgDurationMs: 18000 },
        devops: { executionCount: 18, successRate: 89, avgDurationMs: 25000 },
        discovery: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
        coding: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
        test: { executionCount: 55, successRate: 78, avgDurationMs: 35000 },
        design: { executionCount: 0, successRate: 0, avgDurationMs: 0 },
      },
    },
    agents: [
      {
        agentId: 'agent-backend-001',
        agentType: 'backend',
        executionCount: 45,
        successRate: 91,
        avgDurationMs: 12500,
        totalTokens: 125000,
        executionsOverTime: [
          { timestamp: '2026-01-29T10:00:00Z', value: 5 },
          { timestamp: '2026-01-29T10:15:00Z', value: 8 },
          { timestamp: '2026-01-29T10:30:00Z', value: 6 },
        ],
        successRateOverTime: [
          { timestamp: '2026-01-29T10:00:00Z', value: 90 },
          { timestamp: '2026-01-29T10:15:00Z', value: 92 },
          { timestamp: '2026-01-29T10:30:00Z', value: 91 },
        ],
      },
    ],
    timeRange: '1h',
  };

  describe('Rendering', () => {
    it('renders chart container', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    });

    it('renders summary stats', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByText('273')).toBeInTheDocument(); // total executions
      expect(screen.getByText('92%')).toBeInTheDocument(); // success rate
    });

    it('renders time range selector', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByTestId('time-range-selector')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading skeleton when loading', () => {
      render(<AgentMetricsChart isLoading />);
      expect(screen.getByTestId('metrics-loading')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no data', () => {
      render(<AgentMetricsChart />);
      expect(screen.getByTestId('metrics-empty')).toBeInTheDocument();
    });

    it('displays empty message', () => {
      render(<AgentMetricsChart />);
      expect(screen.getByText('No metrics data available')).toBeInTheDocument();
    });
  });

  describe('Time Range Selection', () => {
    it('displays current time range', () => {
      render(<AgentMetricsChart data={mockMetrics} timeRange="1h" />);
      const selector = screen.getByTestId('time-range-1h');
      expect(selector).toHaveAttribute('aria-pressed', 'true');
    });

    it('calls onTimeRangeChange when selecting new range', () => {
      const handleChange = vi.fn();
      render(
        <AgentMetricsChart
          data={mockMetrics}
          timeRange="1h"
          onTimeRangeChange={handleChange}
        />
      );

      fireEvent.click(screen.getByTestId('time-range-24h'));
      expect(handleChange).toHaveBeenCalledWith('24h');
    });

    it('renders all time range options', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByTestId('time-range-1h')).toBeInTheDocument();
      expect(screen.getByTestId('time-range-6h')).toBeInTheDocument();
      expect(screen.getByTestId('time-range-24h')).toBeInTheDocument();
      expect(screen.getByTestId('time-range-7d')).toBeInTheDocument();
    });
  });

  describe('Summary Statistics', () => {
    it('shows total executions', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByText('Total Executions')).toBeInTheDocument();
      expect(screen.getByText('273')).toBeInTheDocument();
    });

    it('shows success rate', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      // Use getAllByText since "Success Rate" appears in both stat card and chart toggle
      const successRateElements = screen.getAllByText('Success Rate');
      expect(successRateElements.length).toBeGreaterThan(0);
      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('shows average duration', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByText('Avg Duration')).toBeInTheDocument();
    });

    it('shows total tokens', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByText('Total Tokens')).toBeInTheDocument();
    });
  });

  describe('Chart Type Toggle', () => {
    it('renders chart type toggle', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      expect(screen.getByTestId('chart-type-toggle')).toBeInTheDocument();
    });

    it('can switch between executions and success rate view', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      const successRateBtn = screen.getByTestId('chart-success-rate');
      fireEvent.click(successRateBtn);
      expect(successRateBtn).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Accessibility', () => {
    it('has accessible chart container', () => {
      render(<AgentMetricsChart data={mockMetrics} />);
      const chart = screen.getByTestId('metrics-chart');
      expect(chart).toHaveAttribute('role', 'region');
      expect(chart).toHaveAttribute('aria-label', 'Agent metrics chart');
    });
  });
});
