/**
 * Unit tests for AgentLogsPanel component (P05-F12 T07)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AgentLogsPanel from './AgentLogsPanel';
import type { AgentLog, LogLevel } from '../../types/agents';

describe('AgentLogsPanel', () => {
  const mockLogs: AgentLog[] = [
    {
      id: 'log-1',
      agentId: 'agent-1',
      level: 'info',
      message: 'Task started',
      timestamp: '2026-01-29T10:00:00Z',
    },
    {
      id: 'log-2',
      agentId: 'agent-1',
      level: 'debug',
      message: 'Loading context pack',
      timestamp: '2026-01-29T10:01:00Z',
    },
    {
      id: 'log-3',
      agentId: 'agent-1',
      level: 'warn',
      message: 'Test coverage below threshold',
      timestamp: '2026-01-29T10:02:00Z',
    },
    {
      id: 'log-4',
      agentId: 'agent-1',
      level: 'error',
      message: 'Assertion failed in test',
      timestamp: '2026-01-29T10:03:00Z',
    },
  ];

  describe('Rendering', () => {
    it('renders panel container', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      expect(screen.getByTestId('logs-panel')).toBeInTheDocument();
    });

    it('renders all log entries', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const logEntries = screen.getAllByTestId('log-entry');
      expect(logEntries).toHaveLength(4);
    });

    it('renders log messages', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      expect(screen.getByText('Task started')).toBeInTheDocument();
      expect(screen.getByText('Loading context pack')).toBeInTheDocument();
    });

    it('renders log level badges', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const logEntries = screen.getAllByTestId('log-entry');
      // Check that log entries have level badges
      const badges = logEntries.map((entry) =>
        entry.querySelector('.uppercase')?.textContent
      );
      expect(badges).toContain('info');
      expect(badges).toContain('debug');
      expect(badges).toContain('warn');
      expect(badges).toContain('error');
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no logs', () => {
      render(<AgentLogsPanel logs={[]} />);
      expect(screen.getByTestId('empty-logs')).toBeInTheDocument();
    });

    it('shows empty message', () => {
      render(<AgentLogsPanel logs={[]} />);
      expect(screen.getByText('No logs available')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading state', () => {
      render(<AgentLogsPanel logs={[]} isLoading />);
      expect(screen.getByTestId('logs-loading')).toBeInTheDocument();
    });
  });

  describe('Level Filter', () => {
    it('renders level filter dropdown', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      expect(screen.getByTestId('level-filter')).toBeInTheDocument();
    });

    it('has all level options', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const select = screen.getByTestId('level-filter');

      expect(select).toContainHTML('All Levels');
      expect(select).toContainHTML('debug');
      expect(select).toContainHTML('info');
      expect(select).toContainHTML('warn');
      expect(select).toContainHTML('error');
    });

    it('calls onLevelChange when level selected', () => {
      const handleLevelChange = vi.fn();
      render(
        <AgentLogsPanel logs={mockLogs} onLevelChange={handleLevelChange} />
      );

      const select = screen.getByTestId('level-filter');
      fireEvent.change(select, { target: { value: 'error' } });

      expect(handleLevelChange).toHaveBeenCalledWith('error');
    });

    it('shows selected level', () => {
      render(<AgentLogsPanel logs={mockLogs} levelFilter="error" />);
      const select = screen.getByTestId('level-filter') as HTMLSelectElement;
      expect(select.value).toBe('error');
    });
  });

  describe('Search', () => {
    it('renders search input', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      expect(screen.getByTestId('log-search')).toBeInTheDocument();
    });

    it('shows search value', () => {
      render(<AgentLogsPanel logs={mockLogs} searchTerm="error" />);
      const input = screen.getByTestId('log-search') as HTMLInputElement;
      expect(input.value).toBe('error');
    });

    it('calls onSearchChange when typing', () => {
      const handleSearchChange = vi.fn();
      render(
        <AgentLogsPanel logs={mockLogs} onSearchChange={handleSearchChange} />
      );

      const input = screen.getByTestId('log-search');
      fireEvent.change(input, { target: { value: 'test' } });

      expect(handleSearchChange).toHaveBeenCalledWith('test');
    });

    it('has placeholder text', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const input = screen.getByTestId('log-search');
      expect(input).toHaveAttribute('placeholder', 'Search logs...');
    });
  });

  describe('Log Level Colors', () => {
    it('applies debug color class', () => {
      render(<AgentLogsPanel logs={[mockLogs[1]]} />);
      const logEntry = screen.getByTestId('log-entry');
      const badge = logEntry.querySelector('.uppercase');
      expect(badge).toHaveTextContent('debug');
      expect(badge).toHaveClass('text-text-muted');
    });

    it('applies info color class', () => {
      render(<AgentLogsPanel logs={[mockLogs[0]]} />);
      const logEntry = screen.getByTestId('log-entry');
      const badge = logEntry.querySelector('.uppercase');
      expect(badge).toHaveTextContent('info');
      expect(badge).toHaveClass('text-text-secondary');
    });

    it('applies warn color class', () => {
      render(<AgentLogsPanel logs={[mockLogs[2]]} />);
      const logEntry = screen.getByTestId('log-entry');
      const badge = logEntry.querySelector('.uppercase');
      expect(badge).toHaveTextContent('warn');
      expect(badge).toHaveClass('text-status-warning');
    });

    it('applies error color class', () => {
      render(<AgentLogsPanel logs={[mockLogs[3]]} />);
      const logEntry = screen.getByTestId('log-entry');
      const badge = logEntry.querySelector('.uppercase');
      expect(badge).toHaveTextContent('error');
      expect(badge).toHaveClass('text-status-error');
    });
  });

  describe('Timestamps', () => {
    it('renders formatted timestamps', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      // Should show time portion
      const logEntries = screen.getAllByTestId('log-entry');
      expect(logEntries[0]).toHaveTextContent(/\d{1,2}:\d{2}/);
    });
  });

  describe('Accessibility', () => {
    it('has role="log" for container', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const logList = screen.getByTestId('log-list');
      expect(logList).toHaveAttribute('role', 'log');
    });

    it('has aria-label for search', () => {
      render(<AgentLogsPanel logs={mockLogs} />);
      const input = screen.getByTestId('log-search');
      expect(input).toHaveAttribute('aria-label', 'Search logs');
    });
  });
});
