import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { User, AppState } from '@/types';

interface AppStore extends AppState {
  // Actions
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  logout: () => void;
}

export const useAppStore = create<AppStore>()(
  devtools(
    set => ({
      // Initial state
      user: null,
      isLoading: false,
      error: null,

      // Actions
      setUser: user => set({ user }),
      setLoading: isLoading => set({ isLoading }),
      setError: error => set({ error }),
      clearError: () => set({ error: null }),
      logout: () => set({ user: null, error: null }),
    }),
    {
      name: 'app-store',
    }
  )
);
