import { create } from 'zustand'

export const useCardStore = create((set) => ({
  cards: [],
  selectedCard: null,
  loading: false,

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

  updateCard: (cardId, updatedCard) =>
    set((state) => ({
      cards: state.cards.map((c) => (c.id === cardId ? updatedCard : c)),
      selectedCard:
        state.selectedCard?.id === cardId ? updatedCard : state.selectedCard,
    })),

  resetCards: () =>
    set({
      cards: [],
      selectedCard: null,
      loading: false,
    }),
}))
