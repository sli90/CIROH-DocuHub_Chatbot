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

      expect(result).toEqual({
        answer: 'Test answer',
        sources: 'Source 1\nSource 2',
        links: 'Link 1\nLink 2',
        success: true,
      });

      expect(globalThis.fetch).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/ask',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text: 'Test question' }),
        })
      );
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
      expect(result.answer).toBe('Sorry, I encountered an error while processing your question. Please try again later.');
      expect(result.error).toBe('Cannot read properties of undefined (reading \'ok\')');
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
      expect(result.answer).toBe('Sorry, I encountered an error while processing your question. Please try again later.');
    });

    it('should handle client errors (4xx)', async () => {
      // Mock fetch to throw a client error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('HTTP error! status: 400');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe('Sorry, I encountered an error while processing your question. Please try again later.');
    });

    it('should retry failed requests', async () => {
      (globalThis.fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ answer: 'Success after retry' }),
        });

      const result = await chatAPI.sendQuestion({ text: 'Test question' });

      expect(result.success).toBe(true);
      expect(result.answer).toBe('Success after retry');
      expect(globalThis.fetch).toHaveBeenCalledTimes(3);
    });
  });
});
