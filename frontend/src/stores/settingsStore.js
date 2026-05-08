import { create } from 'zustand'
import { settingService } from '../services/settingService'

const ONBOARDING_COMPLETED_KEY = 'algomate_onboarding_completed'
const ONBOARDING_STEP_KEY = 'algomate_onboarding_step'

export const useSettingsStore = create((set, get) => ({
  settings: null,
  onboardingCompleted: false,
  onboardingStep: null,
  loading: false,

  fetchSettings: async () => {
    set({ loading: true })
    try {
      const response = await settingService.getV1Settings()
      const data = response.data || response
      const onboardingCompleted = data.onboarding_completed
        || localStorage.getItem(ONBOARDING_COMPLETED_KEY) === 'true'

      let onboardingStep = null
      if (!onboardingCompleted) {
        const savedStep = localStorage.getItem(ONBOARDING_STEP_KEY)
        onboardingStep = savedStep || 'welcome'
      }

      set({
        settings: data,
        onboardingCompleted,
        onboardingStep,
        loading: false,
      })
    } catch {
      set({ loading: false })
    }
  },

  updateSettings: async (updateData) => {
    await settingService.updateV1Settings(updateData)
    const response = await settingService.getV1Settings()
    const data = response.data || response
    const onboardingCompleted = data.onboarding_completed
      || localStorage.getItem(ONBOARDING_COMPLETED_KEY) === 'true'

    set({
      settings: data,
      onboardingCompleted,
    })
  },

  completeOnboarding: async () => {
    await settingService.updateV1Settings({ onboarding_completed: true })
    localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true')
    localStorage.removeItem(ONBOARDING_STEP_KEY)
    set({ onboardingCompleted: true, onboardingStep: null })
  },

  setOnboardingStep: (step) => {
    if (step) {
      localStorage.setItem(ONBOARDING_STEP_KEY, step)
    } else {
      localStorage.removeItem(ONBOARDING_STEP_KEY)
    }
    set({ onboardingStep: step })
  },

  resetSettings: () => set({
    settings: null,
    onboardingCompleted: false,
    onboardingStep: null,
    loading: false,
  }),
}))
