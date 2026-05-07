import { create } from 'zustand'
import { settingService } from '../services/settingService'

const ONBOARDING_COMPLETED_KEY = 'algomate_onboarding_completed'

export const useSettingsStore = create((set, get) => ({
  settings: null,
  onboardingCompleted: false,
  loading: false,

  fetchSettings: async () => {
    set({ loading: true })
    try {
      const response = await settingService.getV1Settings()
      const data = response.data || response
      const onboardingCompleted = data.onboarding_completed
        || localStorage.getItem(ONBOARDING_COMPLETED_KEY) === 'true'

      set({
        settings: data,
        onboardingCompleted,
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
    set({ onboardingCompleted: true })
  },

  resetSettings: () => set({
    settings: null,
    onboardingCompleted: false,
    loading: false,
  }),
}))
