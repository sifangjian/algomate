import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
    _store: () => store,
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

const { mockGetV1Settings, mockUpdateV1Settings } = vi.hoisted(() => ({
  mockGetV1Settings: vi.fn(),
  mockUpdateV1Settings: vi.fn(),
}))

vi.mock('../../services/settingService', () => ({
  settingService: {
    getV1Settings: mockGetV1Settings,
    updateV1Settings: mockUpdateV1Settings,
  },
}))

import { useSettingsStore } from '../../stores/settingsStore'

const DEFAULT_SETTINGS = {
  onboarding_completed: false,
  api_key_configured: false,
  theme: 'light',
  language: 'zh-CN',
}

describe('settingsStore', () => {
  beforeEach(() => {
    useSettingsStore.setState({
      settings: null,
      onboardingCompleted: false,
      loading: false,
    })
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应包含所有默认值', () => {
      const state = useSettingsStore.getState()
      expect(state.settings).toBeNull()
      expect(state.onboardingCompleted).toBe(false)
      expect(state.loading).toBe(false)
    })
  })

  describe('fetchSettings', () => {
    it('应从 API 获取设置并更新状态', async () => {
      mockGetV1Settings.mockResolvedValue({
        code: 200,
        data: { ...DEFAULT_SETTINGS, onboarding_completed: false },
      })

      const { fetchSettings } = useSettingsStore.getState()
      await fetchSettings()

      const state = useSettingsStore.getState()
      expect(state.settings.onboarding_completed).toBe(false)
      expect(state.onboardingCompleted).toBe(false)
      expect(state.loading).toBe(false)
      expect(mockGetV1Settings).toHaveBeenCalled()
    })

    it('onboarding_completed=true 时应更新 onboardingCompleted', async () => {
      mockGetV1Settings.mockResolvedValue({
        code: 200,
        data: { ...DEFAULT_SETTINGS, onboarding_completed: true },
      })

      const { fetchSettings } = useSettingsStore.getState()
      await fetchSettings()

      const state = useSettingsStore.getState()
      expect(state.onboardingCompleted).toBe(true)
    })

    it('请求过程中 loading 应为 true', async () => {
      let resolvePromise
      mockGetV1Settings.mockReturnValue(new Promise((resolve) => { resolvePromise = resolve }))

      const { fetchSettings } = useSettingsStore.getState()
      const fetchPromise = fetchSettings()

      expect(useSettingsStore.getState().loading).toBe(true)

      resolvePromise({ code: 200, data: DEFAULT_SETTINGS })
      await fetchPromise

      expect(useSettingsStore.getState().loading).toBe(false)
    })

    it('API 失败时应保持默认状态', async () => {
      mockGetV1Settings.mockRejectedValue(new Error('Network error'))

      const { fetchSettings } = useSettingsStore.getState()
      await fetchSettings()

      const state = useSettingsStore.getState()
      expect(state.settings).toBeNull()
      expect(state.onboardingCompleted).toBe(false)
      expect(state.loading).toBe(false)
    })
  })

  describe('updateSettings', () => {
    it('应调用 API 更新设置', async () => {
      mockUpdateV1Settings.mockResolvedValue({ code: 200, data: { updated: true } })
      mockGetV1Settings.mockResolvedValue({
        code: 200,
        data: { ...DEFAULT_SETTINGS, onboarding_completed: true },
      })

      const { updateSettings } = useSettingsStore.getState()
      await updateSettings({ onboarding_completed: true })

      expect(mockUpdateV1Settings).toHaveBeenCalledWith({ onboarding_completed: true })
    })

    it('更新 onboarding_completed 后应刷新状态', async () => {
      mockUpdateV1Settings.mockResolvedValue({ code: 200, data: { updated: true } })
      mockGetV1Settings.mockResolvedValue({
        code: 200,
        data: { ...DEFAULT_SETTINGS, onboarding_completed: true },
      })

      const { updateSettings } = useSettingsStore.getState()
      await updateSettings({ onboarding_completed: true })

      const state = useSettingsStore.getState()
      expect(state.onboardingCompleted).toBe(true)
    })
  })

  describe('completeOnboarding', () => {
    it('应调用 updateV1Settings 设置 onboarding_completed=true', async () => {
      mockUpdateV1Settings.mockResolvedValue({ code: 200, data: { updated: true } })

      const { completeOnboarding } = useSettingsStore.getState()
      await completeOnboarding()

      expect(mockUpdateV1Settings).toHaveBeenCalledWith({ onboarding_completed: true })
    })

    it('应更新 localStorage', async () => {
      mockUpdateV1Settings.mockResolvedValue({ code: 200, data: { updated: true } })

      const { completeOnboarding } = useSettingsStore.getState()
      await completeOnboarding()

      expect(localStorageMock.setItem).toHaveBeenCalledWith('algomate_onboarding_completed', 'true')
    })

    it('应更新 onboardingCompleted 状态', async () => {
      mockUpdateV1Settings.mockResolvedValue({ code: 200, data: { updated: true } })

      const { completeOnboarding } = useSettingsStore.getState()
      await completeOnboarding()

      expect(useSettingsStore.getState().onboardingCompleted).toBe(true)
    })
  })

  describe('resetSettings', () => {
    it('应重置所有状态到初始值', () => {
      useSettingsStore.setState({
        settings: DEFAULT_SETTINGS,
        onboardingCompleted: true,
        loading: true,
      })

      const { resetSettings } = useSettingsStore.getState()
      resetSettings()

      const state = useSettingsStore.getState()
      expect(state.settings).toBeNull()
      expect(state.onboardingCompleted).toBe(false)
      expect(state.loading).toBe(false)
    })
  })
})
