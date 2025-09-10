// API Configuration
export const API_CONFIG = {
  // Default API base URL - can be overridden by environment variables
  BASE_URL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:3000',
  
  // API endpoints
  ENDPOINTS: {
    CHAT: '/ask',
  },
  
  // Request timeout in milliseconds
  TIMEOUT: 30000,
  
  // Retry configuration
  RETRY: {
    MAX_ATTEMPTS: 3,
    DELAY: 1000, // Initial delay in milliseconds
  },
} as const;

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};
