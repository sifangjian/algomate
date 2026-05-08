import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import OnboardingController from '../OnboardingController'

vi.mock('../../../stores/settingsStore', () => ({
  useSettingsStore: vi.fn(),
}))

import { useSettingsStore } from '../../../stores/settingsStore'

describe('StepGuide - 5步引导流程', () => {
  const mockSetOnboardingStep = vi.fn()
  const mockCompleteOnboarding = vi.fn()

  function mockQuerySelectorWithNpc() {
    const mockEl = document.createElement('div')
    mockEl.setAttribute('data-npc-name', '老夫子')
    mockEl.getBoundingClientRect = vi.fn(() => ({
      top: 100, left: 100, width: 200, height: 150, bottom: 250, right: 300,
    }))
    return vi.spyOn(document, 'querySelector').mockReturnValue(mockEl)
  }

  beforeEach(() => {
    vi.clearAllMocks()
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })
  })

  it('step 1 (welcome): shows welcome modal with step indicator 1/5', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'welcome',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
    expect(screen.getByLabelText('引导步骤 1/5')).toBeInTheDocument()
  })

  it('step 2 (select_npc): shows spotlight with "选择导师" tooltip and step 2/5', () => {
    const spy = mockQuerySelectorWithNpc()

    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'select_npc',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText('选择你的第一位导师')).toBeInTheDocument()
    expect(screen.getByLabelText('引导步骤 2/5')).toBeInTheDocument()

    spy.mockRestore()
  })

  it('step 2 (select_npc): shows description about clicking 老夫子', () => {
    const spy = mockQuerySelectorWithNpc()

    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'select_npc',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText(/点击老夫子/)).toBeInTheDocument()

    spy.mockRestore()
  })

  it('step 3 (dialogue): renders nothing (dialogue handled by NpcDialogue page)', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'dialogue',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    const { container } = render(<OnboardingController />)
    expect(container.innerHTML).toBe('')
  })

  it('step 5 (view_workshop): shows spotlight with "查看卡牌" tooltip and step 5/5', () => {
    const spy = mockQuerySelectorWithNpc()

    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'view_workshop',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)
    expect(screen.getByText('查看你的卡牌')).toBeInTheDocument()
    expect(screen.getByLabelText('引导步骤 5/5')).toBeInTheDocument()

    spy.mockRestore()
  })

  it('step 5 (view_workshop): calls completeOnboarding on interact', () => {
    const mockEl = document.createElement('div')
    mockEl.setAttribute('data-card-id', 'card-1')
    mockEl.getBoundingClientRect = vi.fn(() => ({
      top: 100, left: 100, width: 200, height: 150, bottom: 250, right: 300,
    }))
    const spy = vi.spyOn(document, 'querySelector').mockReturnValue(mockEl)

    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'view_workshop',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    render(<OnboardingController />)

    act(() => {
      const clickEvent = new MouseEvent('click', { bubbles: true })
      mockEl.dispatchEvent(clickEvent)
      document.dispatchEvent(clickEvent)
    })

    spy.mockRestore()
  })

  it('step complete: renders nothing', () => {
    useSettingsStore.mockReturnValue({
      onboardingCompleted: false,
      onboardingStep: 'complete',
      setOnboardingStep: mockSetOnboardingStep,
      completeOnboarding: mockCompleteOnboarding,
    })

    const { container } = render(<OnboardingController />)
    expect(container.innerHTML).toBe('')
  })

  it('full flow: welcome -> select_npc transition via setOnboardingStep', () => {
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
})
