/**
 * Unit tests for AgentTimelineView component (P05-F12 T09)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AgentTimelineView from './AgentTimelineView';
import type { TimelineData, MetricsTimeRange } from '../../types/agents';

describe('AgentTimelineView', () => {
  const now = new Date();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);

  const mockTimeline: TimelineData = {
    agents: [
      {
        agentId: 'agent-backend-001',
        agentType: 'backend',
        executions: [
          {
            id: 'exec-001',
            taskName: 'Implement Redis client',
            agentId: 'agent-backend-001',
            agentType: 'backend',
            startTime: new Date(hourAgo.getTime() + 10 * 60 * 1000).toISOString(),
            endTime: new Date(hourAgo.getTime() + 25 * 60 * 1000).toISOString(),
            durationMs: 15 * 60 * 1000,
            status: 'completed',
          },
          {
            id: 'exec-002',
            taskName: 'Add Redis streams',
            agentId: 'agent-backend-001',
            agentType: 'backend',
            startTime: new Date(hourAgo.getTime() + 40 * 60 * 1000).toISOString(),
            endTime: null,
            durationMs: null,
            status: 'running',
          },
        ],
      },
      {
        agentId: 'agent-frontend-001',
        agentType: 'frontend',
        executions: [
          {
            id: 'exec-101',
            taskName: 'Build dashboard',
            agentId: 'agent-frontend-001',
            agentType: 'frontend',
            startTime: new Date(hourAgo.getTime() + 15 * 60 * 1000).toISOString(),
            endTime: new Date(hourAgo.getTime() + 35 * 60 * 1000).toISOString(),
            durationMs: 20 * 60 * 1000,
            status: 'completed',
          },
        ],
      },
      {
        agentId: 'agent-test-001',
        agentType: 'test',
        executions: [
          {
            id: 'exec-201',
            taskName: 'Unit test suite',
            agentId: 'agent-test-001',
            agentType: 'test',
            startTime: new Date(hourAgo.getTime() + 30 * 60 * 1000).toISOString(),
            endTime: new Date(hourAgo.getTime() + 45 * 60 * 1000).toISOString(),
            durationMs: 15 * 60 * 1000,
            status: 'failed',
          },
        ],
      },
    ],
    startTime: hourAgo.toISOString(),
    endTime: now.toISOString(),
  };

  describe('Rendering', () => {
    it('renders timeline container', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      expect(screen.getByTestId('timeline-view')).toBeInTheDocument();
    });

    it('renders agent rows', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const rows = screen.getAllByTestId('agent-row');
      expect(rows).toHaveLength(3);
    });

    it('renders task blocks', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');
      expect(blocks).toHaveLength(4); // 2 + 1 + 1 executions
    });

    it('renders agent type labels', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      expect(screen.getByText('Backend')).toBeInTheDocument();
      expect(screen.getByText('Frontend')).toBeInTheDocument();
      expect(screen.getByText('Test')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no data', () => {
      render(<AgentTimelineView />);
      expect(screen.getByTestId('timeline-empty')).toBeInTheDocument();
    });

    it('shows empty message', () => {
      render(<AgentTimelineView />);
      expect(screen.getByText('No timeline data available')).toBeInTheDocument();
    });

    it('shows empty state for timeline with no agents', () => {
      const emptyTimeline: TimelineData = {
        agents: [],
        startTime: hourAgo.toISOString(),
        endTime: now.toISOString(),
      };
      render(<AgentTimelineView data={emptyTimeline} />);
      expect(screen.getByTestId('timeline-empty')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading state', () => {
      render(<AgentTimelineView isLoading />);
      expect(screen.getByTestId('timeline-loading')).toBeInTheDocument();
    });
  });

  describe('Task Block Status Colors', () => {
    it('applies completed color to completed tasks', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');
      // First block is completed
      expect(blocks[0]).toHaveClass('bg-status-success');
    });

    it('applies running color to running tasks', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');
      // Second block (exec-002) is running
      expect(blocks[1]).toHaveClass('bg-accent-blue');
    });

    it('applies failed color to failed tasks', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');
      // Last block is failed
      expect(blocks[3]).toHaveClass('bg-status-error');
    });
  });

  describe('Time Range Selection', () => {
    it('renders time range selector', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      expect(screen.getByTestId('timeline-time-range')).toBeInTheDocument();
    });

    it('calls onTimeRangeChange when range selected', () => {
      const handleChange = vi.fn();
      render(
        <AgentTimelineView
          data={mockTimeline}
          timeRange="1h"
          onTimeRangeChange={handleChange}
        />
      );

      fireEvent.click(screen.getByTestId('timeline-range-6h'));
      expect(handleChange).toHaveBeenCalledWith('6h');
    });
  });

  describe('Hover Tooltips', () => {
    it('shows task name in tooltip on hover', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');

      // Hover over first block
      fireEvent.mouseEnter(blocks[0]);
      expect(screen.getByText('Implement Redis client')).toBeInTheDocument();
    });

    it('hides tooltip on mouse leave', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const blocks = screen.getAllByTestId('task-block');

      fireEvent.mouseEnter(blocks[0]);
      fireEvent.mouseLeave(blocks[0]);

      // Tooltip should be hidden (task name should not be visible in tooltip)
      const tooltips = screen.queryAllByTestId('task-tooltip');
      expect(tooltips.every((t) => t.classList.contains('opacity-0'))).toBe(true);
    });
  });

  describe('Accessibility', () => {
    it('has role="img" for timeline', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const timeline = screen.getByTestId('timeline-view');
      expect(timeline).toHaveAttribute('role', 'img');
    });

    it('has aria-label', () => {
      render(<AgentTimelineView data={mockTimeline} />);
      const timeline = screen.getByTestId('timeline-view');
      expect(timeline).toHaveAttribute('aria-label', 'Agent execution timeline');
    });
  });
});
