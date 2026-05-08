import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import OnboardingController from '../OnboardingController'

vi.mock('../../../stores/settingsStore', () => ({
  useSettingsStore: vi.fn(),
}))

import { useSettingsStore } from '../../../stores/settingsStore'

describe('OnboardingController', () => {
  const mockSetOnboardingStep = vi.fn()
  const mockCompleteOnboarding = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })
  })

  it('renders nothing when onboarding is completed', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: true,
      onboardingStep: null,
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    const { container } = render(<OnboardingController />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when onboardingStep is null', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: null,
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    const { container } = render(<OnboardingController />)
    expect(container.innerHTML).toBe('')
  })

  it('renders WelcomeModal when step is welcome', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
  })

  it('transitions to select_npc step when clicking start in WelcomeModal', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    fireEvent.click(screen.getByRole('button', { name: /开始冒险/ }))
    expect(mockSetOnboardingStep).toHaveBeenCalledWith('select_npc')
  })

  it('calls completeOnboarding when skipping from WelcomeModal', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    fireEvent.click(screen.getByRole('button', { name: /跳过新手引导/ }))
    const confirmButtons = screen.getAllByRole('button', { name: /确认/ })
    fireEvent.click(confirmButtons[confirmButtons.length - 1])
    expect(mockCompleteOnboarding).toHaveBeenCalledTimes(1)
  })

  it('renders OnboardingSpotlight when step is select_npc', () => {
    const mockEl = document.createElement('div')
    mockEl.setAttribute('data-npc-name', '老夫子')
    mockEl.getBoundingClientRect = vi.fn(() => ({
      top: 100, left: 100, width: 200, height: 150, bottom: 250, right: 300,
    }))
    vi.spyOn(document, 'querySelector').mockReturnValue(mockEl)

    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'select_npc',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText('选择你的第一位导师')).toBeInTheDocument()

    vi.restoreAllMocks()
  })
})
