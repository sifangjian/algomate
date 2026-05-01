import { create } from 'zustand'

export const useCardStore = create((set) => ({
  cards: [],
  selectedCard: null,
  filterState: {
    searchKeyword: '',
    sortBy: 'name',
    sortOrder: 'asc',
  },
  loading: false,

  setCards: (cards) => set({ cards }),

  addCard: (card) =>
    set((state) => ({
      cards: [card, ...state.cards],
    })),

  setSelectedCard: (card) => set({ selectedCard: card }),

  setFilterState: (filterState) =>
    set((state) => ({
      filterState: { ...state.filterState, ...filterState },
    })),

  setLoading: (loading) => set({ loading }),

  removeCard: (cardId) =>
    set((state) => ({
      cards: state.cards.filter((c) => c.id !== cardId),
      selectedCard:
        state.selectedCard?.id === cardId ? null : state.selectedCard,
    })),

  resetCards: () =>
    set({
      cards: [],
      selectedCard: null,
      filterState: {
        searchKeyword: '',
        sortBy: 'name',
        sortOrder: 'asc',
      },
      loading: false,
    }),
}))
