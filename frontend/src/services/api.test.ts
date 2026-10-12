import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ChatAPI, StreamUnavailableError } from './api';

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

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

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

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.sources).toBe('Source 1, Source 2');
      expect(result.links).toBe('Link 1, Link 2');
    });

    it('should handle missing answer with default message', async () => {
      const mockResponse = {};

      (globalThis.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.answer).toBe('No response received');
      expect(result.success).toBe(true);
    });

    it('should handle network errors', async () => {
      // Mock fetch to throw a network error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('Failed to fetch');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });

    it('should handle timeout errors', async () => {
      const abortError = new Error('Request timed out');
      abortError.name = 'AbortError';
      (globalThis.fetch as any).mockRejectedValueOnce(abortError);

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe('Request timed out. Please try again with a shorter question.');
    });

    it('should handle server errors (5xx)', async () => {
      // Mock fetch to throw a server error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('HTTP error! status: 500');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe('Server error. Please try again later.');
    });

    it('should handle client errors (4xx)', async () => {
      // Mock fetch to throw a client error
      (globalThis.fetch as any).mockImplementationOnce(() => {
        throw new Error('HTTP error! status: 400');
      });

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.success).toBe(false);
      expect(result.answer).toBe(
        'Invalid request. Please try rephrasing your question.'
      );
    });

    it('should not retry failed requests', async () => {
      (globalThis.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await chatAPI.sendQuestion({ text: 'Test question', email: 'test@ua.edu' });

      expect(result.success).toBe(false);
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('streamQuestion', () => {
    // A fetch Response whose body yields the given strings as chunks.
    const streamResponse = (chunks: string[]) => ({
      ok: true,
      status: 200,
      body: new ReadableStream<Uint8Array>({
        start(controller) {
          const encoder = new TextEncoder();
          chunks.forEach(chunk => controller.enqueue(encoder.encode(chunk)));
          controller.close();
        },
      }),
    });

    it('delivers status and text as it arrives, then the full response', async () => {
      const events = [
        { type: 'status', message: 'Searching...' },
        { type: 'ping' },
        { type: 'delta', text: '# Title\n\nHello ' },
        { type: 'delta', text: '**world**' },
        { type: 'done', sources: ['A > B'], links: ['/a'], route: 'bottom_up', usage: { total_tokens: 7 } },
      ].map(e => JSON.stringify(e) + '\n');
      // Split one event across two chunks to exercise line buffering.
      const joined = events.join('');
      (globalThis.fetch as any).mockResolvedValueOnce(
        streamResponse([joined.slice(0, 40), joined.slice(40)])
      );

      const statuses: string[] = [];
      const deltas: string[] = [];
      const result = await chatAPI.streamQuestion(
        { text: 'q', email: 'test@ua.edu' },
        { onStatus: s => statuses.push(s), onDelta: d => deltas.push(d) }
      );

      expect(statuses).toEqual(['Searching...']);
      expect(deltas).toEqual(['# Title\n\nHello ', '**world**']);
      expect(result.answer).toBe('# Title\n\nHello **world**');
      expect(result.sources).toBe('A > B');
      expect(result.links).toBe('/a');
      expect(result.route).toBe('bottom_up');
      const [url, init] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe('http://127.0.0.1:8000/ask/stream');
      expect(init.headers['x-amz-content-sha256']).toMatch(/^[0-9a-f]{64}$/);
      expect(JSON.parse(init.body).email).toBe('test@ua.edu');
    });

    it('applies a replace event (guardrail retraction)', async () => {
      (globalThis.fetch as any).mockResolvedValueOnce(
        streamResponse([
          JSON.stringify({ type: 'delta', text: 'partial' }) + '\n',
          JSON.stringify({ type: 'replace', text: 'Refused.' }) + '\n',
          JSON.stringify({ type: 'done', route: 'both' }) + '\n',
        ])
      );
      const result = await chatAPI.streamQuestion({ text: 'q', email: 'test@ua.edu' });
      expect(result.answer).toBe('Refused.');
    });

    it('throws StreamUnavailableError when the endpoint fails before any text', async () => {
      (globalThis.fetch as any).mockResolvedValueOnce({ ok: false, status: 403, body: null });
      await expect(chatAPI.streamQuestion({ text: 'q', email: 'test@ua.edu' })).rejects.toBeInstanceOf(
        StreamUnavailableError
      );
    });

    it('reports a cut-off answer when the stream ends without done', async () => {
      (globalThis.fetch as any).mockResolvedValueOnce(
        streamResponse([JSON.stringify({ type: 'delta', text: 'half an' }) + '\n'])
      );
      await expect(chatAPI.streamQuestion({ text: 'q', email: 'test@ua.edu' })).rejects.toThrow('cut off');
    });
  });
});
