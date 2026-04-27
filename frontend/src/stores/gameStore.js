import { create } from 'zustand'

export const useGameStore = create((set) => ({
  realms: [],
  currentRealm: null,
  loading: false,
  error: null,

  setRealms: (realms) => set({ realms }),

  setCurrentRealm: (realm) => set({ currentRealm: realm }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  updateRealmProgress: (realmId, progress) =>
    set((state) => ({
      realms: state.realms.map((r) =>
        r.id === realmId ? { ...r, progress } : r
      ),
    })),

  resetGame: () =>
    set({
      realms: [],
      currentRealm: null,
      loading: false,
      error: null,
    }),
}))
