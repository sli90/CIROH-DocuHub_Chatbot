// API Configuration
export const API_CONFIG = {
  // VITE_API_BASE_URL overrides everything (an empty value means same-origin).
  // Otherwise production builds call same-origin (CloudFront routes /ask and
  // /telemetry to the API) and `npm run dev` calls the local FastAPI server.
  BASE_URL:
    (import.meta as any).env?.VITE_API_BASE_URL ??
    ((import.meta as any).env?.PROD ? '' : 'http://127.0.0.1:8000'),
  
  // API endpoints
  ENDPOINTS: {
    CHAT: '/ask',
    // Same answer, streamed as newline-delimited JSON while it is written.
    CHAT_STREAM: '/ask/stream',
  },

  // Give up on a stream that has sent nothing (not even a keep-alive, which
  // the server sends every 10s) for this long.
  STREAM_IDLE_TIMEOUT: 70000,
  
  // Hybrid RAG + gpt-5.x often exceeds 30s. Do not retry a timed-out ask.
  TIMEOUT: 180000,

  RETRY: {
    MAX_ATTEMPTS: 1,
    DELAY: 1000,
  },
} as const;

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};
