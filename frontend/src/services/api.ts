import { API_CONFIG, getApiUrl } from '../config/api';

export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  answer: string;
  success: boolean;
  error?: string;
}

export class ChatAPI {
  constructor() {
    // No need to store baseUrl since we use getApiUrl function
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

  async sendQuestion(request: ChatRequest): Promise<ChatResponse> {
    try {
      const data = await this.retryRequest(async () => {
        return await this.makeRequest<{ answer?: string; message?: string }>(
          getApiUrl(API_CONFIG.ENDPOINTS.CHAT),
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
          }
        );
      });

      return {
        answer: data.answer || data.message || 'No response received',
        success: true,
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
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

// Create a default instance
export const chatAPI = new ChatAPI();
