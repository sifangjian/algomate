import { create } from 'zustand'
import { cardService } from '../services/cardService'
import api from '../services/api'

export const useHallStore = create((set, get) => ({
  algorithmInfo: null,
  loading: false,
  selectedCard: null,
  overview: null,
  overviewLoading: false,

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

  fetchTopicOverview: async () => {
    set({ overviewLoading: true })
    try {
      const data = await cardService.getOverview()
      set({ overview: data })
      return data
    } catch (err) {
      console.error('Failed to fetch overview:', err)
      set({ overview: null })
      return null
    } finally {
      set({ overviewLoading: false })
    }
  },

  resetHall: () => set({
    algorithmInfo: null,
    loading: false,
    selectedCard: null,
    overview: null,
  }),
}))