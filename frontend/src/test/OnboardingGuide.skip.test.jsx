import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import OnboardingGuide from '../components/ui/OnboardingGuide/OnboardingGuide'

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

describe('OnboardingGuide - 跳过引导按钮 (F08-T011)', () => {
  const mockOnClose = vi.fn()
  const mockOnNavigate = vi.fn()

  beforeEach(() => {
    mockOnClose.mockClear()
    mockOnNavigate.mockClear()
    vi.clearAllMocks()
    localStorageMock.clear()
    useSettingsStore.setState({
      settings: null,
      onboardingCompleted: false,
      loading: false,
    })
    mockUpdateV1Settings.mockResolvedValue({ code: 200 })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('点击跳过按钮应显示确认弹窗', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))

    expect(screen.getByText('是否跳过引导？')).toBeInTheDocument()
  })

  it('确认跳过后应调用 completeOnboarding', async () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))

    const confirmBtn = screen.getByText('确认跳过')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockUpdateV1Settings).toHaveBeenCalledWith({ onboarding_completed: true })
    })
  })

  it('确认跳过后应更新 localStorage', async () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))
    fireEvent.click(screen.getByText('确认跳过'))

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith('algomate_onboarding_completed', 'true')
    })
  })

  it('确认跳过后应关闭引导', async () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))
    fireEvent.click(screen.getByText('确认跳过'))

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  it('取消跳过后不应调用 completeOnboarding', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))
    fireEvent.click(screen.getByText('继续引导'))

    expect(mockUpdateV1Settings).not.toHaveBeenCalled()
    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
  })

  it('取消跳过后确认弹窗应关闭', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('跳过'))
    fireEvent.click(screen.getByText('继续引导'))

    expect(screen.queryByText('是否跳过引导？')).not.toBeInTheDocument()
  })

  it('完成最后一步时应调用 completeOnboarding', async () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('开始冒险 →'))
    fireEvent.click(screen.getByText('前往新手森林 →'))
    fireEvent.click(screen.getByText('知道了 →'))
    fireEvent.click(screen.getByText('前往卡牌工坊 →'))

    await waitFor(() => {
      expect(mockUpdateV1Settings).toHaveBeenCalledWith({ onboarding_completed: true })
    })
  })

  it('完成最后一步时应更新 localStorage', async () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    fireEvent.click(screen.getByText('开始冒险 →'))
    fireEvent.click(screen.getByText('前往新手森林 →'))
    fireEvent.click(screen.getByText('知道了 →'))
    fireEvent.click(screen.getByText('前往卡牌工坊 →'))

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith('algomate_onboarding_completed', 'true')
    })
  })
})
