import { create } from 'zustand'
import { cardService } from '../services/cardService'
import { npcService } from '../services/npcService'
import { statsService } from '../services/statsService'
import api from '../services/api'

export const useHallStore = create((set, get) => ({
    algorithmInfo: null,
    loading: false,
    selectedCard: null,
    overview: null,
    overviewLoading: false,
    todayStats: null,
    todayStatsLoading: false,

    npcs: [],
    learningPath: [],
    stats: null,
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

    fetchTodayStats: async () => {
      set({ todayStatsLoading: true })
      try {
        const data = await cardService.getTodayStats()
        set({ todayStats: data?.data || null })
        return data
      } catch (err) {
        console.error('Failed to fetch today stats:', err)
        set({ todayStats: null })
        return null
      } finally {
        set({ todayStatsLoading: false })
      }
    },

    fetchNpcs: async () => {
      try {
        set({ loading: true })
        const result = await npcService.getAll()
        const data = result?.data || result
        const npcs = data?.npcs || []
        const learningPath = data?.learning_path || []
        set({ npcs, learningPath, loading: false })
      } catch (err) {
        console.error('Failed to fetch npcs:', err)
        set({ npcs: [], learningPath: [], loading: false })
      }
    },

    fetchStats: async () => {
      try {
        const result = await statsService.getHallStats()
        set({
          stats: {
            total_cards: result?.data?.total_cards ?? 0,
            is_new_user: result?.data?.is_new_user ?? false,
          },
        })
      } catch (err) {
        console.error('Failed to fetch stats:', err)
        set({ stats: { total_cards: 0, is_new_user: false } })
      }
    },

    fetchCardGraph: async () => {
      try {
        const graph = await cardService.getGraph?.()
        set({ cardGraph: graph })
        return graph
      } catch (err) {
        console.error('Failed to fetch card graph:', err)
        set({ cardGraph: null })
        return null
      }
    },

    resetHall: () => set({
      algorithmInfo: null,
      loading: false,
      selectedCard: null,
      overview: null,
      todayStats: null,
      npcs: [],
      learningPath: [],
      stats: null,
      cardGraph: null,
    }),
  }))
