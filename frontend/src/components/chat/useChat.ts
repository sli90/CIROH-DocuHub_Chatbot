import { useState, useEffect, useRef } from 'react';
import { Message, QuotaInfo } from './types';
import { chatAPI, ChatResponse, StreamUnavailableError } from '../../services/api';
import { trackEvent } from '../../services/telemetry';
import { clearEmail, getEmail, setEmail as storeEmail } from '../../services/user';

const MESSAGES_KEY = 'ciroh_chat_messages';
const QUOTA_KEY = 'ciroh_chat_quota';

// Remembered so "N questions left today" survives a reload; ignored once the
// day changes (the server resets counts at midnight US Central).
function todayKey(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
}

function loadQuota(): QuotaInfo | null {
  try {
    const saved = JSON.parse(localStorage.getItem(QUOTA_KEY) || 'null');
    return saved && saved.day === todayKey() ? (saved.quota as QuotaInfo) : null;
  } catch {
    return null;
  }
}

function saveQuota(quota: QuotaInfo): void {
  try {
    localStorage.setItem(QUOTA_KEY, JSON.stringify({ day: todayKey(), quota }));
  } catch {
    // Ignore.
  }
}

function loadMessages(): Message[] {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Array<Omit<Message, 'timestamp'> & { timestamp: string }>;
    return parsed
      // Drop an answer that was still streaming when the page was closed.
      .filter(msg => !(msg.isStreaming && !msg.text))
      .map(msg => ({ ...msg, isStreaming: false, status: undefined, timestamp: new Date(msg.timestamp) }));
  } catch {
    return [];
  }
}

function saveMessages(messages: Message[]): void {
  try {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
  } catch {
    // Ignore quota / private-mode failures.
  }
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>(() => loadMessages());
  const [inputValue, setInputValue] = useState('');
  const [isBotResponding, setIsBotResponding] = useState(false);
  const [showExamples, setShowExamples] = useState(() => loadMessages().length === 0);
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(
    new Set()
  );
  const [lastError, setLastError] = useState<string | null>(null);
  const [email, setEmailState] = useState<string | null>(() => getEmail());
  const [quota, setQuota] = useState<QuotaInfo | null>(() => loadQuota());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastBotMessageRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the start of the last bot message when it arrives
  useEffect(() => {
    const scrollToLastBotMessage = () => {
      if (lastBotMessageRef.current) {
        lastBotMessageRef.current.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      } else if (messagesEndRef.current) {
        // Fallback to bottom if no bot message ref
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };
    
    // Small delay to ensure DOM is updated
    const timeoutId = setTimeout(scrollToLastBotMessage, 100);
    
    return () => clearTimeout(timeoutId);
    // Not on every streamed word: that would yank the view while reading.
  }, [messages.length, isBotResponding]);

  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  // Hide examples when user starts chatting
  useEffect(() => {
    if (messages.length > 0) {
      setShowExamples(false);
    }
  }, [messages.length]);

  const handleSetEmail = (value: string) => {
    storeEmail(value);
    setEmailState(value);
    setQuota(null);
    trackEvent('email_provided');
  };

  const handleChangeEmail = () => {
    clearEmail();
    setEmailState(null);
    setQuota(null);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || !email || isBotResponding) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      isBot: false,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsBotResponding(true);
    setLastError(null);
    trackEvent('question_asked', { length: text.trim().length });

    const botId = (Date.now() + 1).toString();
    const updateBot = (patch: (msg: Message) => Partial<Message>) =>
      setMessages(prev => prev.map(msg => (msg.id === botId ? { ...msg, ...patch(msg) } : msg)));

    setMessages(prev => [
      ...prev,
      {
        id: botId,
        text: '',
        isBot: true,
        timestamp: new Date(),
        isStreaming: true,
        status: 'Thinking...',
      },
    ]);

    let streamed = true;
    let response: ChatResponse;
    try {
      try {
        response = await chatAPI.streamQuestion(
          { text: text.trim(), email },
          {
            onStatus: status => updateBot(() => ({ status })),
            onDelta: delta => updateBot(msg => ({ text: msg.text + delta, status: undefined })),
            onReplace: replacement => updateBot(() => ({ text: replacement, status: undefined })),
          }
        );
      } catch (error) {
        if (!(error instanceof StreamUnavailableError)) throw error;
        // Streaming endpoint unreachable: fall back to the buffered /ask.
        console.warn('Streaming unavailable, falling back to /ask:', error.message);
        streamed = false;
        response = await chatAPI.sendQuestion({ text: text.trim(), email });
      }

      updateBot(() => ({
        text: response.answer,
        isStreaming: false,
        status: undefined,
        sources: response.sources,
        links: response.links,
        route: response.route,
        questionType: response.question_type,
        routeReason: response.route_reason,
        usage: response.usage,
        sourceDetails: response.source_details,
        followUps: response.follow_ups,
      }));
      if (response.quota) {
        setQuota(response.quota);
        saveQuota(response.quota);
      }
      trackEvent('question_answered', {
        route: response.route,
        estimated_usd: response.usage?.estimated_usd,
        total_tokens: response.usage?.total_tokens,
        success: response.success,
        streamed,
      });
      setLastError(response.success ? null : response.error || 'Unknown error occurred');
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage =
        error instanceof Error && error.message.startsWith('The answer was cut off')
          ? error.message
          : 'Sorry, I encountered an error while processing your question. Please try again later.';
      // Keep whatever was already streamed and append the error under it.
      updateBot(msg => ({
        text: msg.text ? `${msg.text}\n\n_${errorMessage}_` : errorMessage,
        isStreaming: false,
        status: undefined,
      }));
      setLastError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsBotResponding(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setShowExamples(true);
    setLastError(null);
    saveMessages([]);
    trackEvent('chat_cleared');
  };

  const handleRetryLastMessage = () => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages].reverse().find(msg => !msg.isBot);
      if (lastUserMessage) {
        handleSendMessage(lastUserMessage.text);
      }
    }
  };

  const handleToggleCategory = (index: number) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCategories(newExpanded);
  };

  const handleShowExamples = () => {
    setShowExamples(true);
  };

  const handleShowChat = () => {
    setShowExamples(false);
  };

  return {
    messages,
    inputValue,
    isBotResponding,
    showExamples,
    expandedCategories,
    lastError,
    email,
    quota,
    handleSetEmail,
    handleChangeEmail,
    messagesEndRef,
    lastBotMessageRef,
    setInputValue,
    handleSendMessage,
    handleClearChat,
    handleToggleCategory,
    handleShowExamples,
    handleShowChat,
    handleRetryLastMessage,
  };
}
