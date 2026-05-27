import { create } from 'zustand'

export const useUserStore = create((set) => ({
  user: {
    id: 'user_001',
    nickname: '冒险者',
    totalCards: 0,
    streakDays: 0,
    totalReviews: 0,
    avatar: null,
  },

  setUser: (userData) =>
    set((state) => ({
      user: { ...state.user, ...userData },
    })),

  updateStats: (stats) =>
    set((state) => ({
      user: { ...state.user, ...stats },
    })),

  resetUser: () =>
    set({
      user: {
        id: 'user_001',
        nickname: '冒险者',
        totalCards: 0,
        streakDays: 0,
        totalReviews: 0,
        avatar: null,
      },
    }),
}))
