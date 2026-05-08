import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

const { mockEndDialogue, mockGetV1Settings, mockUpdateV1Settings } = vi.hoisted(() => ({
  mockEndDialogue: vi.fn(),
  mockGetV1Settings: vi.fn(),
  mockUpdateV1Settings: vi.fn(),
}))

vi.mock('../../services/dialogueService', () => ({
  dialogueService: {
    start: vi.fn(),
    sendMessageStream: vi.fn(),
    endDialogue: mockEndDialogue,
    saveNote: vi.fn(),
    getHistory: vi.fn(),
    heartbeat: vi.fn(),
  },
}))

vi.mock('../../services/settingService', () => ({
  settingService: {
    getV1Settings: mockGetV1Settings,
    updateV1Settings: mockUpdateV1Settings,
  },
}))

vi.mock('../../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

import { useDialogueStore } from '../../stores/dialogueStore'
import { useSettingsStore } from '../../stores/settingsStore'
import { showToast } from '../../components/ui/Toast/index'

describe('dialogueStore - 首次修习完成检测 (F08-T010)', () => {
  beforeEach(() => {
    useDialogueStore.getState().reset()
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

  describe('endDialogue - 引导完成检测', () => {
    it('用户未完成引导且获得卡牌时，应调用 completeOnboarding 并显示 toast', async () => {
      useSettingsStore.setState({ onboardingCompleted: false })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: { id: 1, name: '二分查找' },
        },
      })
      mockUpdateV1Settings.mockResolvedValue({ code: 200 })

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(mockUpdateV1Settings).toHaveBeenCalledWith({ onboarding_completed: true })
      expect(showToast).toHaveBeenCalledWith('恭喜完成新手引导！', 'success')
    })

    it('用户已完成引导时，不应调用 completeOnboarding', async () => {
      useSettingsStore.setState({ onboardingCompleted: true })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: { id: 1, name: '二分查找' },
        },
      })

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(mockUpdateV1Settings).not.toHaveBeenCalled()
      expect(showToast).not.toHaveBeenCalledWith('恭喜完成新手引导！', 'success')
    })

    it('用户未完成引导但未获得卡牌时，不应调用 completeOnboarding', async () => {
      useSettingsStore.setState({ onboardingCompleted: false })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: null,
        },
      })

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(mockUpdateV1Settings).not.toHaveBeenCalled()
    })

    it('获得卡牌且未完成引导时，应更新 settingsStore 的 onboardingCompleted 状态', async () => {
      useSettingsStore.setState({ onboardingCompleted: false })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: { id: 1, name: '二分查找' },
        },
      })
      mockUpdateV1Settings.mockResolvedValue({ code: 200 })

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(useSettingsStore.getState().onboardingCompleted).toBe(true)
    })

    it('获得卡牌且未完成引导时，应同时更新 localStorage', async () => {
      useSettingsStore.setState({ onboardingCompleted: false })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: { id: 1, name: '二分查找' },
        },
      })
      mockUpdateV1Settings.mockResolvedValue({ code: 200 })

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(localStorageMock.setItem).toHaveBeenCalledWith('algomate_onboarding_completed', 'true')
    })

    it('completeOnboarding API 失败时，仍应更新 localStorage 作为降级', async () => {
      useSettingsStore.setState({ onboardingCompleted: false })
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: {
          card: { id: 1, name: '二分查找' },
        },
      })
      mockUpdateV1Settings.mockRejectedValue(new Error('API error'))

      const { endDialogue } = useDialogueStore.getState()
      await endDialogue()

      expect(localStorageMock.setItem).toHaveBeenCalledWith('algomate_onboarding_completed', 'true')
    })
  })
})
