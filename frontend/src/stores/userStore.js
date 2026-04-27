import { create } from 'zustand'

function getLevelTitle(level) {
  const titles = [
    '', '新手', '见习生', '探索者', '冒险家', '精英',
    '大师', '宗师', '传奇', '神话', '至尊',
  ]
  return titles[Math.min(level, titles.length - 1)] || '至尊'
}

export const useUserStore = create((set) => ({
  user: {
    id: 'user_001',
    nickname: '冒险者',
    level: 1,
    title: '新手',
    experience: 0,
    nextLevelExp: 100,
    avatar: null,
  },

  setUser: (userData) =>
    set((state) => ({
      user: { ...state.user, ...userData },
    })),

  addExperience: (amount) =>
    set((state) => {
      const newExp = state.user.experience + amount
      if (newExp >= state.user.nextLevelExp) {
        return {
          user: {
            ...state.user,
            experience: newExp - state.user.nextLevelExp,
            level: state.user.level + 1,
            nextLevelExp: Math.round(state.user.nextLevelExp * 1.5),
            title: getLevelTitle(state.user.level + 1),
          },
        }
      }
      return {
        user: { ...state.user, experience: newExp },
      }
    }),

  resetUser: () =>
    set({
      user: {
        id: 'user_001',
        nickname: '冒险者',
        level: 1,
        title: '新手',
        experience: 0,
        nextLevelExp: 100,
        avatar: null,
      },
    }),
}))
