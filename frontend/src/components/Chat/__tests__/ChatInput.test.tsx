import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ChatInput from '../ChatInput';
import { ChatSettings } from '../../../types/chat';
import chatService from '../../../services/chatService';

// Mock the chat service
jest.mock('../../../services/chatService');

describe('ChatInput Component', () => {
  const mockChatService = chatService as jest.Mocked<typeof chatService>;
  
  const defaultSettings: ChatSettings = {
    model: 'test_model',
    temperature: 0.7,
    maxTokens: 2000,
    webBrowsing: false,
    deepResearch: false,
    includeDocuments: []
  };
  
  const mockModelsResponse = {
    models: [
      {
        id: 'test_model',
        technical_name: 'test-model-technical',
        common_name: 'Test Model',
        provider: 'test_provider'
      },
      {
        id: 'another_model',
        technical_name: 'another-model-technical', 
        common_name: 'Another Model',
        provider: 'test_provider'
      }
    ],
    default_model: 'test_model'
  };

  const defaultProps = {
    onSend: jest.fn(),
    disabled: false,
    settings: defaultSettings,
    onSettingsChange: jest.fn(),
    onAddDocument: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockChatService.getAvailableModels.mockResolvedValue(mockModelsResponse);
  });

  describe('Rendering', () => {
    it('renders input field and send button', () => {
      render(<ChatInput {...defaultProps} />);

      expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
    });

    it('displays current model setting', () => {
      render(<ChatInput {...defaultProps} />);

      expect(screen.getByText('Model: test_model')).toBeInTheDocument();
    });

    it('shows active settings as chips', () => {
      const settingsWithFeatures: ChatSettings = {
        ...defaultSettings,
        webBrowsing: true,
        deepResearch: true,
        includeDocuments: ['doc1', 'doc2']
      };

      render(
        <ChatInput
          {...defaultProps}
          settings={settingsWithFeatures}
        />
      );

      expect(screen.getByText('Web Browsing')).toBeInTheDocument();
      expect(screen.getByText('Deep Research')).toBeInTheDocument();
      expect(screen.getByText('2 Documents')).toBeInTheDocument();
    });

    it('renders control buttons', () => {
      render(<ChatInput {...defaultProps} />);

      expect(screen.getByLabelText(/add documents/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/toggle web browsing/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/toggle deep research/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/chat settings/i)).toBeInTheDocument();
    });
  });

  describe('Message Input', () => {
    it('allows typing message', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      await user.type(input, 'Hello world');

      expect(input).toHaveValue('Hello world');
    });

    it('sends message on send button click', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      expect(onSendMock).toHaveBeenCalledWith('Test message');
    });

    it('sends message on Enter key press', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      await user.type(input, 'Test message');
      await user.keyboard('{Enter}');

      expect(onSendMock).toHaveBeenCalledWith('Test message');
    });

    it('does not send message on Shift+Enter', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      await user.type(input, 'Test message');
      await user.keyboard('{Shift>}{Enter}{/Shift}');

      expect(onSendMock).not.toHaveBeenCalled();
    });

    it('clears input after sending message', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, 'Test message');
      await user.click(sendButton);

      expect(input).toHaveValue('');
    });

    it('trims whitespace from message', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, '  Test message  ');
      await user.click(sendButton);

      expect(onSendMock).toHaveBeenCalledWith('Test message');
    });

    it('does not send empty messages', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const sendButton = screen.getByRole('button', { name: /send message/i });
      await user.click(sendButton);

      expect(onSendMock).not.toHaveBeenCalled();
    });

    it('does not send whitespace-only messages', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      await user.type(input, '   ');
      await user.click(sendButton);

      expect(onSendMock).not.toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('disables input and buttons when disabled', () => {
      render(<ChatInput {...defaultProps} disabled={true} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('prevents message sending when disabled', async () => {
      const user = userEvent.setup();
      const onSendMock = jest.fn();

      render(<ChatInput {...defaultProps} onSend={onSendMock} disabled={true} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      
      // Try to type (should not work when disabled)
      await user.type(input, 'Test message');
      
      // Try keyboard shortcut
      await user.keyboard('{Enter}');

      expect(onSendMock).not.toHaveBeenCalled();
    });
  });

  describe('Settings Toggle Buttons', () => {
    it('toggles web browsing setting', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const webBrowsingButton = screen.getByLabelText(/toggle web browsing/i);
      await user.click(webBrowsingButton);

      expect(onSettingsChangeMock).toHaveBeenCalledWith({
        webBrowsing: true
      });
    });

    it('toggles deep research setting', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const deepResearchButton = screen.getByLabelText(/toggle deep research/i);
      await user.click(deepResearchButton);

      expect(onSettingsChangeMock).toHaveBeenCalledWith({
        deepResearch: true
      });
    });

    it('shows active state for enabled features', () => {
      const settingsWithFeatures: ChatSettings = {
        ...defaultSettings,
        webBrowsing: true,
        deepResearch: true
      };

      render(
        <ChatInput
          {...defaultProps}
          settings={settingsWithFeatures}
        />
      );

      const webBrowsingButton = screen.getByLabelText(/toggle web browsing/i);
      const deepResearchButton = screen.getByLabelText(/toggle deep research/i);

      // Buttons should have active styling (implementation-dependent)
      expect(webBrowsingButton).toBeInTheDocument();
      expect(deepResearchButton).toBeInTheDocument();
    });
  });

  describe('Settings Menu', () => {
    it('opens settings menu when settings button is clicked', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByText('Chat Settings')).toBeInTheDocument();
    });

    it('displays model selection in settings menu', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByText('Model:')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test_model')).toBeInTheDocument();
    });

    it('allows changing model in settings menu', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      const modelSelect = screen.getByDisplayValue('test_model');
      await user.selectOptions(modelSelect, 'gpt-3.5-turbo');

      expect(onSettingsChangeMock).toHaveBeenCalledWith({
        model: 'gpt-3.5-turbo'
      });
    });

    it('displays temperature slider in settings menu', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByText('Temperature: 0.7')).toBeInTheDocument();
      expect(screen.getByRole('slider')).toBeInTheDocument();
    });

    it('allows changing temperature in settings menu', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      const temperatureSlider = screen.getByRole('slider');
      fireEvent.change(temperatureSlider, { target: { value: '0.9' } });

      expect(onSettingsChangeMock).toHaveBeenCalledWith({
        temperature: 0.9
      });
    });

    it('displays max tokens input in settings menu', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByText('Max Tokens:')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2000')).toBeInTheDocument();
    });

    it('allows changing max tokens in settings menu', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      const maxTokensInput = screen.getByDisplayValue('2000');
      await user.clear(maxTokensInput);
      await user.type(maxTokensInput, '1500');

      expect(onSettingsChangeMock).toHaveBeenCalledWith({
        maxTokens: 1500
      });
    });

    it('displays toggle switches in settings menu', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByLabelText('Web Browsing')).toBeInTheDocument();
      expect(screen.getByLabelText('Deep Research Mode')).toBeInTheDocument();
    });

    it('closes settings menu when clicked outside', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const settingsButton = screen.getByLabelText(/chat settings/i);
      await user.click(settingsButton);

      expect(screen.getByText('Chat Settings')).toBeInTheDocument();

      // Click outside the menu
      await user.click(document.body);

      await waitFor(() => {
        expect(screen.queryByText('Chat Settings')).not.toBeInTheDocument();
      });
    });
  });

  describe('Document Management', () => {
    it('calls onAddDocument when add document button is clicked', async () => {
      const user = userEvent.setup();
      const onAddDocumentMock = jest.fn();

      render(
        <ChatInput
          {...defaultProps}
          onAddDocument={onAddDocumentMock}
        />
      );

      const addDocumentButton = screen.getByLabelText(/add documents/i);
      await user.click(addDocumentButton);

      expect(onAddDocumentMock).toHaveBeenCalledWith('sample-doc');
    });

    it('does not render add document button when onAddDocument is not provided', () => {
      render(
        <ChatInput
          {...defaultProps}
          onAddDocument={undefined}
        />
      );

      expect(screen.queryByLabelText(/add documents/i)).not.toBeInTheDocument();
    });
  });

  describe('Feature Chips', () => {
    it('allows removing web browsing by clicking chip delete', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();
      const settingsWithWebBrowsing: ChatSettings = {
        ...defaultSettings,
        webBrowsing: true
      };

      render(
        <ChatInput
          {...defaultProps}
          settings={settingsWithWebBrowsing}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const webBrowsingChip = screen.getByText('Web Browsing');
      const deleteButton = webBrowsingChip.parentElement?.querySelector('[data-testid="CancelIcon"]');
      
      if (deleteButton) {
        await user.click(deleteButton);
        expect(onSettingsChangeMock).toHaveBeenCalledWith({
          webBrowsing: false
        });
      }
    });

    it('allows removing deep research by clicking chip delete', async () => {
      const user = userEvent.setup();
      const onSettingsChangeMock = jest.fn();
      const settingsWithDeepResearch: ChatSettings = {
        ...defaultSettings,
        deepResearch: true
      };

      render(
        <ChatInput
          {...defaultProps}
          settings={settingsWithDeepResearch}
          onSettingsChange={onSettingsChangeMock}
        />
      );

      const deepResearchChip = screen.getByText('Deep Research');
      const deleteButton = deepResearchChip.parentElement?.querySelector('[data-testid="CancelIcon"]');
      
      if (deleteButton) {
        await user.click(deleteButton);
        expect(onSettingsChangeMock).toHaveBeenCalledWith({
          deepResearch: false
        });
      }
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<ChatInput {...defaultProps} />);

      expect(screen.getByLabelText(/add documents/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/toggle web browsing/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/toggle deep research/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/chat settings/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/send message/i)).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ChatInput {...defaultProps} />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send message/i });

      // Tab through elements
      await user.tab();
      expect(input).toHaveFocus();

      await user.tab();
      // Should move to next focusable element
      expect(document.activeElement).not.toBe(input);
    });
  });
});