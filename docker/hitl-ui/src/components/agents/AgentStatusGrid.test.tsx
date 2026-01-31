/**
 * Unit tests for AgentStatusGrid component (P05-F12 T06)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AgentStatusGrid from './AgentStatusGrid';
import type { AgentStatus } from '../../types/agents';

describe('AgentStatusGrid', () => {
  const mockAgents: AgentStatus[] = [
    {
      agent_id: 'agent-backend-001',
      agent_type: 'backend',
      status: 'running',
      currentTask: 'Implementing feature',
      progress: 50,
      sessionId: 'session-1',
      startedAt: '2026-01-29T10:00:00Z',
      lastHeartbeat: '2026-01-29T10:15:00Z',
    },
    {
      agent_id: 'agent-frontend-001',
      agent_type: 'frontend',
      status: 'idle',
      currentTask: null,
      progress: 0,
      sessionId: null,
      startedAt: null,
      lastHeartbeat: '2026-01-29T10:10:00Z',
    },
    {
      agent_id: 'agent-reviewer-001',
      agent_type: 'reviewer',
      status: 'error',
      currentTask: 'Code review',
      progress: 80,
      sessionId: 'session-2',
      startedAt: '2026-01-29T09:00:00Z',
      lastHeartbeat: '2026-01-29T09:30:00Z',
    },
  ];

  describe('Rendering', () => {
    it('renders grid container', () => {
      render(<AgentStatusGrid agents={mockAgents} />);
      expect(screen.getByTestId('agent-status-grid')).toBeInTheDocument();
    });

    it('renders all agents', () => {
      render(<AgentStatusGrid agents={mockAgents} />);
      const cards = screen.getAllByTestId('agent-card');
      expect(cards).toHaveLength(3);
    });

    it('renders agents in a responsive grid', () => {
      render(<AgentStatusGrid agents={mockAgents} />);
      const grid = screen.getByTestId('agent-status-grid');
      expect(grid).toHaveClass('grid');
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no agents', () => {
      render(<AgentStatusGrid agents={[]} />);
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    it('displays empty message', () => {
      render(<AgentStatusGrid agents={[]} />);
      expect(screen.getByText('No agents found')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading skeletons when loading', () => {
      render(<AgentStatusGrid agents={[]} isLoading />);
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    it('renders multiple skeleton cards', () => {
      render(<AgentStatusGrid agents={[]} isLoading />);
      const skeletons = screen.getAllByTestId('skeleton-card');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Selection', () => {
    it('calls onSelect when card is clicked', () => {
      const handleSelect = vi.fn();
      render(<AgentStatusGrid agents={mockAgents} onSelect={handleSelect} />);

      const cards = screen.getAllByTestId('agent-card');
      fireEvent.click(cards[0]);

      expect(handleSelect).toHaveBeenCalledWith('agent-backend-001');
    });

    it('marks selected agent with selected styles', () => {
      render(
        <AgentStatusGrid
          agents={mockAgents}
          selectedAgentId="agent-frontend-001"
        />
      );

      const cards = screen.getAllByTestId('agent-card');
      // Second card should be selected (frontend)
      expect(cards[1]).toHaveClass('ring-2');
    });

    it('does not mark non-selected agents as selected', () => {
      render(
        <AgentStatusGrid
          agents={mockAgents}
          selectedAgentId="agent-frontend-001"
        />
      );

      const cards = screen.getAllByTestId('agent-card');
      // First card (backend) should not be selected
      expect(cards[0]).not.toHaveClass('ring-2');
    });
  });

  describe('Accessibility', () => {
    it('has correct role for grid', () => {
      render(<AgentStatusGrid agents={mockAgents} />);
      const grid = screen.getByTestId('agent-status-grid');
      expect(grid).toHaveAttribute('role', 'list');
    });

    it('has aria-label', () => {
      render(<AgentStatusGrid agents={mockAgents} />);
      const grid = screen.getByTestId('agent-status-grid');
      expect(grid).toHaveAttribute('aria-label', 'Agent status grid');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(<AgentStatusGrid agents={mockAgents} className="custom-class" />);
      const grid = screen.getByTestId('agent-status-grid');
      expect(grid).toHaveClass('custom-class');
    });
  });
});
