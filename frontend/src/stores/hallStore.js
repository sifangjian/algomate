import { create } from 'zustand'
import { npcService } from '../services/npcService'
import { statsService } from '../services/statsService'

export const useHallStore = create((set, get) => ({
  npcs: [],
  selectedNpc: null,
  learningPath: [],
  stats: null,
  filters: {
    algorithm_type: '',
    keyword: '',
  },
  loading: false,
  modalOpen: false,

  fetchNpcs: async () => {
    set({ loading: true })
    try {
      const { filters } = get()
      const params = {}
      if (filters.algorithm_type) params.algorithm_type = filters.algorithm_type
      if (filters.keyword.trim()) params.keyword = filters.keyword.trim()

      const data = await npcService.getAll(params)
      set({
        npcs: data.npcs,
        learningPath: data.learning_path,
      })
    } catch (err) {
      console.error('Failed to fetch NPCs:', err)
    } finally {
      set({ loading: false })
    }
  },

  fetchNpcDetail: async (id) => {
    try {
      const data = await npcService.getById(id)
      set({ selectedNpc: data })
    } catch (err) {
      console.error('Failed to fetch NPC detail:', err)
    }
  },

  fetchStats: async () => {
    try {
      const data = await statsService.getHallStats()
      set({ stats: data })
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      set({ stats: { total_cards: 0, endangered_cards: 0, pending_retake_cards: 0, cards_by_type: {}, is_new_user: false } })
    }
  },

  setSelectedNpc: (npc) => set({
    selectedNpc: npc,
    modalOpen: npc !== null,
  }),

  setFilters: (partial) => {
    set((state) => ({
      filters: { ...state.filters, ...partial },
    }))
  },

  resetFilters: () => set({
    filters: { algorithm_type: '', keyword: '' },
  }),

  setModalOpen: (open) => set({ modalOpen: open }),

  resetHall: () => set({
    npcs: [],
    selectedNpc: null,
    learningPath: [],
    stats: null,
    filters: { algorithm_type: '', keyword: '' },
    loading: false,
    modalOpen: false,
  }),
}))
