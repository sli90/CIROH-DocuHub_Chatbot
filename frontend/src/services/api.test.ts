import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ChatAPI } from './api';

// Mock fetch
(globalThis as any).fetch = vi.fn();

describe('ChatAPI', () => {
  let chatAPI: ChatAPI;

  beforeEach(() => {
    chatAPI = new ChatAPI();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('sendQuestion', () => {
    it('should send a successful request and return formatted response', async () => {
      const mockResponse = {
        answer: 'Test answer',
        sources: ['Source 1', 'Source 2'],
        links: ['Link 1', 'Link 2'],
      };

      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.answer).toBe('Test answer');
      expect(result.sources).toBe('Source 1\nSource 2');
      expect(result.links).toBe('Link 1\nLink 2');
      expect(result.success).toBe(true);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/ask',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
      const sent = JSON.parse(
        (globalThis.fetch as any).mock.calls[0][1].body
      );
      expect(sent.text).toBe('Test question');
      expect(sent.mode).toBe('hybrid');
      expect(sent.session_id).toBeTruthy();
    });

    it('should handle string sources and links', async () => {
      const mockResponse = {
        answer: 'Test answer',
        sources: 'Source 1, Source 2',
        links: 'Link 1, Link 2',
      };

      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.sources).toBe('Source 1, Source 2');
      expect(result.links).toBe('Link 1, Link 2');
    });

    it('should handle missing answer with default message', async () => {
      const mockResponse = {};

      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.answer).toBe('No response received');
      expect(result.success).toBe(true);
    });

    it('should handle network errors', async () => {
      // Mock fetch to throw a network error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('Failed to fetch');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });

    it('should handle timeout errors', async () => {
      const abortError = new Error('Request timed out');
      abortError.name = 'AbortError';
      (globalThis.fetch as any).mockRejectedValueOnce(abortError);

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe('Request timed out. Please try again with a shorter question.');
    });

    it('should handle server errors (5xx)', async () => {
      // Mock fetch to throw a server error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('HTTP error! status: 500');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe('Server error. Please try again later.');
    });

    it('should handle client errors (4xx)', async () => {
      // Mock fetch to throw a client error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('HTTP error! status: 400');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe(
        'Invalid request. Please try rephrasing your question.'
      );
    });

    it('should not retry failed requests', async () => {
      (globalThis.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    });
  });
});
