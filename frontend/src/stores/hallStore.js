import { create } from 'zustand'
import { npcService } from '../services/npcService'
import { statsService } from '../services/statsService'
import { cardService } from '../services/cardService'

export const useHallStore = create((set, get) => ({
  npcs: [],
  learningPath: [],
  stats: null,
  algorithmInfo: null,
  loading: false,
  selectedCard: null,
  cardGraph: null,

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

  setSelectedCard: (card) => set({ selectedCard: card }),
  clearSelectedCard: () => set({ selectedCard: null }),

  fetchCardByAlgorithmType: async (algorithmType) => {
    try {
      const result = await cardService.getAll({ algorithm_type: algorithmType })
      const card = result?.cards?.[0] || null
      set({ selectedCard: card })
      return card
    } catch (err) {
      console.error('Failed to fetch card by algorithm type:', err)
      set({ selectedCard: null })
      return null
    }
  },

  fetchCardById: async (cardId) => {
    try {
      const card = await cardService.getById(cardId)
      set({ selectedCard: card })
      return card
    } catch (err) {
      console.error('Failed to fetch card by id:', err)
      set({ selectedCard: null })
      return null
    }
  },

  fetchCardGraph: async () => {
    try {
      const data = await cardService.getGraph()
      set({ cardGraph: data.data || data })
    } catch (err) {
      console.error('Failed to fetch card graph:', err)
      set({ cardGraph: null })
    }
  },

  addPrerequisite: async (cardId, prerequisiteCardId) => {
    try {
      await cardService.addPrerequisite(cardId, prerequisiteCardId)
      // Refresh graph after adding prerequisite
      const data = await cardService.getGraph()
      set({ cardGraph: data.data || data })
    } catch (err) {
      console.error('Failed to add prerequisite:', err)
      throw err
    }
  },

  removePrerequisite: async (cardId, prerequisiteCardId) => {
    try {
      await cardService.removePrerequisite(cardId, prerequisiteCardId)
      // Refresh graph after removing prerequisite
      const data = await cardService.getGraph()
      set({ cardGraph: data.data || data })
    } catch (err) {
      console.error('Failed to remove prerequisite:', err)
      throw err
    }
  },

  resetHall: () => set({
    npcs: [],
    learningPath: [],
    stats: null,
    algorithmInfo: null,
    loading: false,
    selectedCard: null,
    cardGraph: null,
  }),
}))