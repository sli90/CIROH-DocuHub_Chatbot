import { useState, useEffect, useRef } from 'react';
import { Message } from './types';
import { chatAPI } from '../../services/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isBotResponding, setIsBotResponding] = useState(false);
  const [showExamples, setShowExamples] = useState(true);
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(
    new Set()
  );
  const [lastError, setLastError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isBotResponding]);

  // Hide examples when user starts chatting
  useEffect(() => {
    if (messages.length > 0) {
      setShowExamples(false);
    }
  }, [messages.length]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

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

    try {
      // Send question to API
      const response = await chatAPI.sendQuestion({ question: text.trim() });
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isBot: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
      
      // Clear any previous errors on successful response
      if (response.success) {
        setLastError(null);
      } else {
        setLastError(response.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = 'Sorry, I encountered an error while processing your question. Please try again later.';
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: errorMessage,
        isBot: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
      setLastError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsBotResponding(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setShowExamples(true);
    setLastError(null);
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

  return {
    messages,
    inputValue,
    isBotResponding,
    showExamples,
    expandedCategories,
    lastError,
    messagesEndRef,
    setInputValue,
    handleSendMessage,
    handleClearChat,
    handleToggleCategory,
    handleShowExamples,
    handleRetryLastMessage,
  };
}
