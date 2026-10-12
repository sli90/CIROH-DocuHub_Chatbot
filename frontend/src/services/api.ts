import { API_CONFIG, getApiUrl } from '../config/api';
import { getSessionId } from './telemetry';
import type { QuotaInfo, SourceDetail, UsageInfo } from '../components/chat/types';

export interface ChatRequest {
  text: string;
  /** Required by the API: questions are limited per email per day. */
  email: string;
}

export interface ChatResponse {
  answer: string;
  sources: string | string[];
  links?: string | string[];
  success: boolean;
  error?: string;
  route?: string;
  question_type?: string;
  route_reason?: string;
  usage?: UsageInfo;
  source_details?: SourceDetail[];
  follow_ups?: string[];
  quota?: QuotaInfo | null;
}

export interface StreamHandlers {
  onStatus?: (message: string) => void;
  onDelta?: (text: string) => void;
  onReplace?: (text: string) => void;
}

/** Thrown when streaming fails before any answer text arrived, so the
 * caller can safely fall back to the non-streaming /ask endpoint. */
export class StreamUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StreamUnavailableError';
  }
}

interface StreamEvent {
  type: 'status' | 'delta' | 'replace' | 'done' | 'error' | 'ping';
  message?: string;
  text?: string;
  sources?: string | string[];
  links?: string | string[];
  route?: string;
  question_type?: string;
  route_reason?: string;
  usage?: UsageInfo;
  source_details?: SourceDetail[];
  follow_ups?: string[];
  quota?: QuotaInfo | null;
}

// The API returns sources/links as arrays (or, from older backends, a
// quoted comma-separated string); the UI wants newline-separated text.
function toLines(value?: string | string[]): string {
  if (!value) return '';
  if (Array.isArray(value)) return value.join('\n');
  return value.replace(/",\s*"/g, '"\n"').replace(/^"|"$/g, '');
}

// CloudFront signs requests to the streaming Lambda (Origin Access
// Control), and AWS requires the viewer to supply the SHA-256 of a POST
// body for that signature.
async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

export function questionTypeLabel(route?: string, questionType?: string): string {
  if (questionType) return questionType;
  if (route === 'top_down') return 'Overview Question';
  if (route === 'bottom_up') return 'Specific Question';
  if (route === 'both') return 'Overview Question / Specific Question';
  return '';
}

export class ChatAPI {
  constructor() {
    // API client for real API integration
  }

  private async makeRequest<T>(url: string, options: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    maxAttempts: number = API_CONFIG.RETRY.MAX_ATTEMPTS
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on certain errors
        if (error instanceof Error && error.name === 'AbortError') {
          throw error;
        }

        if (attempt === maxAttempts) {
          throw lastError;
        }

        // Wait before retrying
        await new Promise(resolve => 
          setTimeout(resolve, API_CONFIG.RETRY.DELAY * attempt)
        );
      }
    }

    throw lastError!;
  }

  /**
   * Ask a question and receive the answer as it is generated. Resolves with
   * the complete response once the stream ends. Throws
   * StreamUnavailableError if nothing of the answer arrived (the caller
   * should fall back to sendQuestion).
   */
  async streamQuestion(request: ChatRequest, handlers: StreamHandlers = {}): Promise<ChatResponse> {
    const body = JSON.stringify({ ...request, session_id: getSessionId(), mode: 'hybrid' });
    const controller = new AbortController();
    let idleTimer = setTimeout(() => controller.abort(), API_CONFIG.STREAM_IDLE_TIMEOUT);
    const resetIdle = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => controller.abort(), API_CONFIG.STREAM_IDLE_TIMEOUT);
    };

    let answer = '';
    let receivedText = false;
    try {
      let response: Response;
      try {
        response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.CHAT_STREAM), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-amz-content-sha256': await sha256Hex(body),
          },
          body,
          signal: controller.signal,
        });
      } catch (error) {
        throw new StreamUnavailableError(error instanceof Error ? error.message : 'fetch failed');
      }
      if (!response.ok || !response.body) {
        throw new StreamUnavailableError(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let done: StreamEvent | null = null;

      const handle = (event: StreamEvent) => {
        switch (event.type) {
          case 'status':
            if (event.message) handlers.onStatus?.(event.message);
            break;
          case 'delta':
            receivedText = true;
            answer += event.text ?? '';
            handlers.onDelta?.(event.text ?? '');
            break;
          case 'replace':
            receivedText = true;
            answer = event.text ?? '';
            handlers.onReplace?.(answer);
            break;
          case 'error':
            throw new Error(event.message || 'Stream error');
          case 'done':
            done = event;
            break;
        }
      };

      for (;;) {
        let chunk: Awaited<ReturnType<typeof reader.read>>;
        try {
          chunk = await reader.read();
        } catch (error) {
          if (!receivedText) {
            throw new StreamUnavailableError(error instanceof Error ? error.message : 'stream failed');
          }
          throw error;
        }
        resetIdle();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        let newline: number;
        while ((newline = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, newline).trim();
          buffer = buffer.slice(newline + 1);
          if (line) handle(JSON.parse(line) as StreamEvent);
        }
      }
      if (buffer.trim()) handle(JSON.parse(buffer) as StreamEvent);

      const final = done as StreamEvent | null;
      if (!final) {
        if (!receivedText) throw new StreamUnavailableError('stream ended without an answer');
        throw new Error('The answer was cut off. Please try again.');
      }
      return {
        answer: answer || 'No response received',
        sources: toLines(final.sources),
        links: toLines(final.links),
        success: true,
        route: final.route,
        question_type: final.question_type,
        route_reason: final.route_reason,
        usage: final.usage,
        source_details: final.source_details,
        follow_ups: final.follow_ups,
        quota: final.quota,
      };
    } finally {
      clearTimeout(idleTimer);
    }
  }

  async sendQuestion(request: ChatRequest): Promise<ChatResponse> {
    try {
      const data = await this.retryRequest(async () => {
        return await this.makeRequest<{
          answer?: string;
          sources?: string | string[];
          links?: string | string[];
          route?: string;
          question_type?: string;
          route_reason?: string;
          usage?: UsageInfo;
          source_details?: SourceDetail[];
          follow_ups?: string[];
          quota?: QuotaInfo | null;
        }>(
          getApiUrl(API_CONFIG.ENDPOINTS.CHAT),
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              ...request,
              session_id: getSessionId(),
              mode: 'hybrid',
            }),
          }
        );
      });

      return {
        answer: data.answer || 'No response received',
        sources: toLines(data.sources),
        links: toLines(data.links),
        success: true,
        route: data.route,
        question_type: data.question_type,
        route_reason: data.route_reason,
        usage: data.usage,
        source_details: data.source_details,
        follow_ups: data.follow_ups,
        quota: data.quota,
      };
    } catch (error) {
      console.error('Chat API error:', error);
      
      let errorMessage = 'Sorry, I encountered an error while processing your question. Please try again later.';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Request timed out. Please try again with a shorter question.';
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
        } else if (error.message.includes('HTTP error! status: 5')) {
          errorMessage = 'Server error. Please try again later.';
        } else if (error.message.includes('HTTP error! status: 4')) {
          errorMessage = 'Invalid request. Please try rephrasing your question.';
        }
      }

      return {
        answer: errorMessage,
        sources: '',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

// Create a default instance
export const chatAPI = new ChatAPI();