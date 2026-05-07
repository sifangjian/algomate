import { create } from 'zustand'
import { bossService } from '../services/bossService'

const BATTLE_STORAGE_KEY = 'boss_battle_state'

export const useBossStore = create((set, get) => ({
  bosses: [],
  selectedBoss: null,
  hasAnyCard: false,
  weaknessCards: [],
  otherCards: [],
  hasWeaknessCard: false,
  battlePhase: 'idle',
  battleState: null,
  currentQuestion: null,
  selectedCardId: null,
  battleResult: null,
  loading: false,
  error: null,

  fetchBosses: async (params) => {
    set({ loading: true, error: null })
    try {
      const result = await bossService.getBosses(params)
      const data = result.data || result
      set({ bosses: data.bosses || [] })
    } catch (err) {
      set({ error: err.message })
    } finally {
      set({ loading: false })
    }
  },

  selectBoss: async (boss) => {
    set({ selectedBoss: boss, loading: true, error: null, currentQuestion: null, selectedCardId: null, battleResult: null })
    try {
      const result = await bossService.getBossDetail(boss.id)
      const data = result.data || result
      set({
        hasAnyCard: data.has_any_card ?? false,
        weaknessCards: data.weakness_cards || [],
        otherCards: data.other_cards || [],
        hasWeaknessCard: data.has_weakness_card ?? false,
        battlePhase: 'selecting_card',
        selectedCardId: null,
      })
    } catch (err) {
      set({ error: err.message })
    } finally {
      set({ loading: false })
    }
  },

  startChallenge: async (bossId, cardId) => {
    set({ loading: true, error: null, selectedCardId: cardId, battlePhase: 'challenging' })
    try {
      const result = await bossService.challenge(bossId, { card_id: cardId })
      const data = result.data || result
      set({
        currentQuestion: data.question,
        battlePhase: 'answering',
      })
    } catch (err) {
      set({ error: err.message, battlePhase: 'selecting_card' })
    } finally {
      set({ loading: false })
    }
  },

  submitAnswer: async (bossId, answerData) => {
    set({ loading: true, error: null, battlePhase: 'submitting' })
    try {
      const result = await bossService.submit(bossId, answerData)
      const data = result.data || result
      set({
        battleResult: data,
        battlePhase: 'result',
      })
    } catch (err) {
      set({ error: err.message, battlePhase: 'answering' })
    } finally {
      set({ loading: false })
    }
  },

  setSelectedCardId: (cardId) => set({ selectedCardId: cardId }),

  setBattlePhase: (phase) => set({ battlePhase: phase }),

  saveBattleToLocalStorage: () => {
    const { selectedBoss, selectedCardId, currentQuestion, battlePhase } = get()
    if (battlePhase !== 'idle') {
      const state = { selectedBoss, selectedCardId, currentQuestion, battlePhase }
      localStorage.setItem(BATTLE_STORAGE_KEY, JSON.stringify(state))
    }
  },

  restoreBattleFromLocalStorage: () => {
    try {
      const saved = localStorage.getItem(BATTLE_STORAGE_KEY)
      if (saved) {
        const state = JSON.parse(saved)
        set({
          battleState: state,
          selectedBoss: state.selectedBoss,
          selectedCardId: state.selectedCardId,
          currentQuestion: state.currentQuestion,
          battlePhase: state.battlePhase,
        })
        return true
      }
    } catch {
    }
    return false
  },

  clearBattleLocalStorage: () => {
    localStorage.removeItem(BATTLE_STORAGE_KEY)
    set({ battleState: null })
  },

  resetBattle: () => {
    set({
      currentQuestion: null,
      selectedCardId: null,
      battleResult: null,
      battlePhase: 'selecting_card',
      error: null,
    })
  },

  resetBoss: () => {
    set({
      selectedBoss: null,
      hasAnyCard: false,
      weaknessCards: [],
      otherCards: [],
      hasWeaknessCard: false,
      currentQuestion: null,
      selectedCardId: null,
      battleResult: null,
      battlePhase: 'idle',
      battleState: null,
      error: null,
    })
  },
}))
