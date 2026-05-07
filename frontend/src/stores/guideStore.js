import { create } from 'zustand'

const STORAGE_KEY_PREFIX = 'guide_skipped_'

export const useGuideStore = create((set, get) => ({
  currentGuide: null,
  visible: false,
  cardAcquired: {
    card: null,
    animating: false,
  },

  setGuide: (guide) => set({
    currentGuide: guide,
    visible: true,
  }),

  setCardAcquired: (card) => set({
    cardAcquired: { card, animating: card !== null },
  }),

  setAnimating: (animating) => set((state) => ({
    cardAcquired: { ...state.cardAcquired, animating },
  })),

  dismissGuide: () => set({
    currentGuide: null,
    visible: false,
  }),

  resetGuide: () => set({
    currentGuide: null,
    visible: false,
    cardAcquired: { card: null, animating: false },
  }),

  skipGuide: (scene) => {
    sessionStorage.setItem(`${STORAGE_KEY_PREFIX}${scene}`, 'true')
    set({ currentGuide: null, visible: false })
  },

  shouldShowGuide: (scene) => {
    return sessionStorage.getItem(`${STORAGE_KEY_PREFIX}${scene}`) !== 'true'
  },
}))
