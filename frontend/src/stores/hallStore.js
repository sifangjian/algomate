import { create } from 'zustand'
import { cardService } from '../services/cardService'
import api from '../services/api'

export const useHallStore = create((set, get) => ({
  algorithmInfo: null,
  loading: false,
  selectedCard: null,
  cardGraph: null,

  fetchAlgorithmInfo: async () => {
    try {
      const data = await api.get('/v1/algorithm-info')
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

  resetHall: () => set({
    algorithmInfo: null,
    loading: false,
    selectedCard: null,
    cardGraph: null,
  }),
}))