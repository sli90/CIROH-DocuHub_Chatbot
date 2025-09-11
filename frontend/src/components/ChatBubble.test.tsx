import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatBubble } from './ChatBubble';

// Mock the chat components
vi.mock('./chat', () => ({
  ChatPanel: ({
    isOpen,
    onClose,
  }: {
    isOpen: boolean;
    onClose: () => void;
  }) => (
    <div
      data-testid="chat-panel"
      style={{ display: isOpen ? 'block' : 'none' }}
    >
      <button onClick={onClose} data-testid="close-chat">
        Close
      </button>
    </div>
  ),
  DarkModeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dark-mode-provider">{children}</div>
  ),
}));

describe('ChatBubble', () => {
  it('renders the chat button when closed', () => {
    render(<ChatBubble />);

    const chatButton = screen.getByLabelText('Open chat');
    expect(chatButton).toBeInTheDocument();
    expect(chatButton).toHaveClass('fixed', 'bottom-6', 'right-6');
  });

  it('opens chat panel when button is clicked', () => {
    render(<ChatBubble />);

    const chatButton = screen.getByLabelText('Open chat');
    fireEvent.click(chatButton);

    const chatPanel = screen.getByTestId('chat-panel');
    expect(chatPanel).toBeVisible();
  });

  it('hides chat button when panel is open', () => {
    render(<ChatBubble />);

    const chatButton = screen.getByLabelText('Open chat');
    fireEvent.click(chatButton);

    expect(chatButton).not.toBeVisible();
  });

  it('closes chat panel when close button is clicked', () => {
    render(<ChatBubble />);

    // Open the chat
    const chatButton = screen.getByLabelText('Open chat');
    fireEvent.click(chatButton);

    // Close the chat
    const closeButton = screen.getByTestId('close-chat');
    fireEvent.click(closeButton);

    // Chat button should be visible again (re-render to get updated state)
    const updatedChatButton = screen.getByLabelText('Open chat');
    expect(updatedChatButton).toBeVisible();
  });

  it('wraps content in DarkModeProvider', () => {
    render(<ChatBubble />);

    const darkModeProvider = screen.getByTestId('dark-mode-provider');
    expect(darkModeProvider).toBeInTheDocument();
  });
});
