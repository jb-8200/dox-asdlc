/**
 * Unit tests for AgentStatusCard component (P05-F12 T05)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AgentStatusCard from './AgentStatusCard';
import type { AgentStatus } from '../../types/agents';

describe('AgentStatusCard', () => {
  const mockAgent: AgentStatus = {
    agent_id: 'agent-backend-001',
    agent_type: 'backend',
    status: 'running',
    currentTask: 'Implementing Redis client',
    progress: 65,
    sessionId: 'session-123',
    startedAt: '2026-01-29T10:00:00Z',
    lastHeartbeat: '2026-01-29T10:15:00Z',
  };

  describe('Rendering', () => {
    it('renders agent type label', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      expect(screen.getByText('Backend')).toBeInTheDocument();
    });

    it('renders agent ID', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      expect(screen.getByText('agent-backend-001')).toBeInTheDocument();
    });

    it('renders status badge with correct color for running', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Running');
      expect(badge).toHaveClass('bg-accent-blue');
    });

    it('renders current task when running', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      expect(screen.getByText('Implementing Redis client')).toBeInTheDocument();
    });

    it('renders progress bar when running', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      const progressBar = screen.getByTestId('progress-bar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveStyle({ width: '65%' });
    });

    it('renders progress percentage text', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      expect(screen.getByText('65%')).toBeInTheDocument();
    });
  });

  describe('Status Variations', () => {
    it('renders idle status correctly', () => {
      const idleAgent: AgentStatus = {
        ...mockAgent,
        status: 'idle',
        currentTask: null,
        progress: 0,
      };
      render(<AgentStatusCard agent={idleAgent} />);

      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Idle');
      expect(badge).toHaveClass('bg-status-info');
    });

    it('renders error status correctly', () => {
      const errorAgent: AgentStatus = {
        ...mockAgent,
        status: 'error',
        progress: 75,
      };
      render(<AgentStatusCard agent={errorAgent} />);

      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Error');
      expect(badge).toHaveClass('bg-status-error');
    });

    it('renders completed status correctly', () => {
      const completedAgent: AgentStatus = {
        ...mockAgent,
        status: 'completed',
        currentTask: null,
        progress: 0,
      };
      render(<AgentStatusCard agent={completedAgent} />);

      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Completed');
      expect(badge).toHaveClass('bg-status-success');
    });

    it('renders blocked status correctly', () => {
      const blockedAgent: AgentStatus = {
        ...mockAgent,
        status: 'blocked',
        progress: 50,
      };
      render(<AgentStatusCard agent={blockedAgent} />);

      const badge = screen.getByTestId('status-badge');
      expect(badge).toHaveTextContent('Blocked');
      expect(badge).toHaveClass('bg-status-warning');
    });
  });

  describe('Idle State', () => {
    it('shows "No active task" when idle', () => {
      const idleAgent: AgentStatus = {
        ...mockAgent,
        status: 'idle',
        currentTask: null,
        progress: 0,
      };
      render(<AgentStatusCard agent={idleAgent} />);
      expect(screen.getByText('No active task')).toBeInTheDocument();
    });

    it('does not show progress bar when idle', () => {
      const idleAgent: AgentStatus = {
        ...mockAgent,
        status: 'idle',
        currentTask: null,
        progress: 0,
      };
      render(<AgentStatusCard agent={idleAgent} />);
      expect(screen.queryByTestId('progress-bar')).not.toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('calls onClick when clicked', () => {
      const handleClick = vi.fn();
      render(<AgentStatusCard agent={mockAgent} onClick={handleClick} />);

      fireEvent.click(screen.getByTestId('agent-card'));
      expect(handleClick).toHaveBeenCalledWith(mockAgent.agent_id);
    });

    it('applies selected styles when selected', () => {
      render(<AgentStatusCard agent={mockAgent} isSelected />);

      const card = screen.getByTestId('agent-card');
      expect(card).toHaveClass('ring-2');
      expect(card).toHaveClass('ring-accent-blue');
    });

    it('does not apply selected styles when not selected', () => {
      render(<AgentStatusCard agent={mockAgent} isSelected={false} />);

      const card = screen.getByTestId('agent-card');
      expect(card).not.toHaveClass('ring-2');
    });
  });

  describe('Agent Types', () => {
    const agentTypes = [
      { agent_type: 'backend', label: 'Backend' },
      { agent_type: 'frontend', label: 'Frontend' },
      { agent_type: 'planner', label: 'Planner' },
      { agent_type: 'reviewer', label: 'Reviewer' },
      { agent_type: 'orchestrator', label: 'Orchestrator' },
      { agent_type: 'devops', label: 'DevOps' },
      { agent_type: 'test', label: 'Test' },
    ] as const;

    agentTypes.forEach(({ agent_type, label }) => {
      it(`renders ${agent_type} agent type correctly`, () => {
        const agent: AgentStatus = {
          ...mockAgent,
          agent_type,
        };
        render(<AgentStatusCard agent={agent} />);
        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has role="article" for card', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      const card = screen.getByTestId('agent-card');
      expect(card).toHaveAttribute('role', 'article');
    });

    it('has aria-label with agent info', () => {
      render(<AgentStatusCard agent={mockAgent} />);
      const card = screen.getByTestId('agent-card');
      expect(card).toHaveAttribute('aria-label', 'Backend agent agent-backend-001 - Running');
    });
  });
});
