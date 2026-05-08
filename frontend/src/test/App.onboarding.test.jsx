import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

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

const { mockGetV1Settings, mockUpdateV1Settings } = vi.hoisted(() => ({
  mockGetV1Settings: vi.fn(),
  mockUpdateV1Settings: vi.fn(),
}))

vi.mock('../services/settingService', () => ({
  settingService: {
    getV1Settings: mockGetV1Settings,
    updateV1Settings: mockUpdateV1Settings,
  },
}))

import { useSettingsStore } from '../stores/settingsStore'

describe('App - 引导完成判断 (F08-T012)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    useSettingsStore.setState({
      settings: null,
      onboardingCompleted: false,
      loading: false,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('onboardingCompleted=true 时不应显示引导弹窗', async () => {
    useSettingsStore.setState({ onboardingCompleted: true })
    mockGetV1Settings.mockResolvedValue({
      code: 200,
      data: { onboarding_completed: true, api_key_configured: false, theme: 'light', language: 'zh-CN' },
    })

    render(<App />)

    await new Promise((r) => setTimeout(r, 100))

    expect(screen.queryByText('欢迎来到算法大陆')).not.toBeInTheDocument()
  })

  it('onboardingCompleted=false 且 localStorage 无记录时应显示引导弹窗', async () => {
    useSettingsStore.setState({ onboardingCompleted: false })
    mockGetV1Settings.mockResolvedValue({
      code: 200,
      data: { onboarding_completed: false, api_key_configured: false, theme: 'light', language: 'zh-CN' },
    })

    render(<App />)

    await new Promise((r) => setTimeout(r, 200))

    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
  })

  it('onboardingCompleted=true 时即使 localStorage 无记录也不显示引导', async () => {
    useSettingsStore.setState({ onboardingCompleted: true })
    mockGetV1Settings.mockResolvedValue({
      code: 200,
      data: { onboarding_completed: true, api_key_configured: false, theme: 'light', language: 'zh-CN' },
    })

    render(<App />)

    await new Promise((r) => setTimeout(r, 100))

    expect(screen.queryByText('欢迎来到算法大陆')).not.toBeInTheDocument()
  })
})
