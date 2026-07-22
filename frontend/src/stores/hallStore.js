import { create } from 'zustand'
import { npcService } from '../services/npcService'
import { statsService } from '../services/statsService'

export const useHallStore = create((set, get) => ({
  npcs: [],
  learningPath: [],
  stats: null,
  algorithmInfo: null,
  loading: false,

  fetchNpcs: async () => {
    set({ loading: true })
    try {
      const data = await npcService.getAll()
      set({
        npcs: data.data?.npcs || [],
        learningPath: data.data?.learning_path || [],
      })
    } catch (err) {
      console.error('Failed to fetch NPCs:', err)
    } finally {
      set({ loading: false })
    }
  },

  fetchStats: async () => {
    try {
      const data = await statsService.getHallStats()
      set({ stats: data.data })
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      set({ stats: { total_cards: 0, endangered_cards: 0, pending_retake_cards: 0, cards_by_type: {}, is_new_user: false } })
    }
  },

  fetchAlgorithmInfo: async () => {
    try {
      const data = await npcService.getAlgorithmInfo()
      set({ algorithmInfo: data })
    } catch (err) {
      console.error('Failed to fetch algorithm info:', err)
      set({ algorithmInfo: null })
    }
  },

  resetHall: () => set({
    npcs: [],
    learningPath: [],
    stats: null,
    algorithmInfo: null,
    loading: false,
  }),
}))