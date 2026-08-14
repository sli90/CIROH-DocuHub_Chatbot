import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => {
    const listeners = new Set();
    return {
      matches: false,
      media: query,
      onchange: null,
      // Modern API (primary)
      addEventListener: vi.fn((_event, callback) => {
        listeners.add(callback);
      }),
      removeEventListener: vi.fn((_event, callback) => {
        listeners.delete(callback);
      }),
      dispatchEvent: vi.fn(),
      // Deprecated API (for backward compatibility)
      addListener: vi.fn((callback) => {
        listeners.add(callback);
      }),
      removeListener: vi.fn((callback) => {
        listeners.delete(callback);
      }),
    };
  }),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn().mockReturnValue(null), // Return null by default
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});