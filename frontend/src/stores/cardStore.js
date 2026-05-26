import { create } from 'zustand'
import { cardService } from '../services/cardService'

export const useCardStore = create((set, get) => ({
  cards: [],
  selectedCard: null,
  loading: false,
  endangeredCount: 0,
  pendingRetakeCount: 0,
  retakeInfo: null,
  filters: {
    algorithm_type: '',
    status: '',
    keyword: '',
  },
  graphData: { nodes: [], edges: [] },
  linkedCards: {},

  setCards: (cards) => set({ cards }),

  addCard: (card) =>
    set((state) => ({
      cards: [card, ...state.cards],
    })),

  setSelectedCard: (card) => set({ selectedCard: card }),

  setLoading: (loading) => set({ loading }),

  removeCard: (cardId) =>
    set((state) => ({
      cards: state.cards.filter((c) => c.id !== cardId),
      selectedCard:
        state.selectedCard?.id === cardId ? null : state.selectedCard,
    })),

  updateCardInList: (cardId, updatedCard) =>
    set((state) => ({
      cards: state.cards.map((c) => (c.id === cardId ? updatedCard : c)),
      selectedCard:
        state.selectedCard?.id === cardId ? updatedCard : state.selectedCard,
    })),

  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
    })),

  resetFilters: () =>
    set({
      filters: {
        algorithm_type: '',
        status: '',
        keyword: '',
      },
    }),

  fetchCards: async () => {
    const { filters } = get()
    set({ loading: true })
    try {
      const params = {}
      if (filters.algorithm_type) params.algorithm_type = filters.algorithm_type
      if (filters.status) params.status = filters.status
      if (filters.keyword) params.keyword = filters.keyword
      const data = await cardService.getAll(params)
      set({
        cards: data.cards || [],
        endangeredCount: data.endangered_count || 0,
        pendingRetakeCount: data.pending_retake_count || 0,
      })
    } catch {
    } finally {
      set({ loading: false })
    }
  },

  fetchCardDetail: async (id) => {
    try {
      const card = await cardService.getById(id)
      set({ selectedCard: card })
      return card
    } catch {
      return null
    }
  },

  updateCard: async (cardId, payload) => {
    const updatedCard = await cardService.update(cardId, payload)
    set((state) => ({
      cards: state.cards.map((c) => (c.id === cardId ? updatedCard : c)),
      selectedCard:
        state.selectedCard?.id === cardId ? updatedCard : state.selectedCard,
    }))
    return updatedCard
  },

  deleteCard: async (cardId) => {
    const result = await cardService.delete(cardId)
    set((state) => ({
      cards: state.cards.filter((c) => c.id !== cardId),
      selectedCard:
        state.selectedCard?.id === cardId ? null : state.selectedCard,
    }))
    return result
  },

  retakeCard: async (cardId) => {
    const result = await cardService.retakeCard(cardId)
    return result
  },

  setRetakeInfo: (cardId, dialogueId, npcId) =>
    set({
      retakeInfo: { cardId, dialogueId, npcId },
    }),

  clearRetakeInfo: () => set({ retakeInfo: null }),

  // 图谱相关
  fetchGraphData: async () => {
    try {
      const data = await cardService.getGraph()
      set({ graphData: data || { nodes: [], edges: [] } })
      return data
    } catch {
      return null
    }
  },

  fetchLinkedCards: async (cardId) => {
    try {
      const data = await cardService.getLinks(cardId)
      set((state) => ({
        linkedCards: { ...state.linkedCards, [cardId]: data || [] },
      }))
      return data
    } catch {
      return []
    }
  },

  addCardLink: async (cardId, targetId, linkType, sourceKeyword) => {
    const result = await cardService.addLink(cardId, {
      target_card_id: targetId,
      link_type: linkType || 'related',
      source_keyword: sourceKeyword || null,
    })
    // 刷新链接列表
    get().fetchLinkedCards(cardId)
    return result
  },

  removeCardLink: async (linkId, cardId) => {
    await cardService.removeLink(linkId)
    if (cardId) {
      get().fetchLinkedCards(cardId)
    }
  },

  resetCards: () =>
    set({
      cards: [],
      selectedCard: null,
      loading: false,
      endangeredCount: 0,
      pendingRetakeCount: 0,
      retakeInfo: null,
      graphData: { nodes: [], edges: [] },
      linkedCards: {},
      filters: {
        algorithm_type: '',
        status: '',
        keyword: '',
      },
    }),
}))
