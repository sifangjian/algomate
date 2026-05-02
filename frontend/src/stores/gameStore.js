import { create } from 'zustand'

export const useGameStore = create((set) => ({
  realms: [],
  loading: false,
  error: null,

  setRealms: (realms) => set({ realms }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  resetGame: () =>
    set({
      realms: [],
      loading: false,
      error: null,
    }),
}))
