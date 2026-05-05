import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import OnboardingGuide from '../components/ui/OnboardingGuide/OnboardingGuide'

describe('OnboardingGuide', () => {
  const mockOnClose = vi.fn()
  const mockOnNavigate = vi.fn()

  beforeEach(() => {
    mockOnClose.mockClear()
    mockOnNavigate.mockClear()
    localStorage.clear()
  })

  it('renders nothing when open is false', () => {
    render(<OnboardingGuide open={false} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    expect(screen.queryByText('欢迎来到算法大陆')).not.toBeInTheDocument()
  })

  it('renders the first step when open is true', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
    expect(screen.getByText('开始冒险 →')).toBeInTheDocument()
  })

  it('advances to step 1 when clicking action button on step 0', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    fireEvent.click(screen.getByText('开始冒险 →'))
    expect(screen.getByText('探索新手森林')).toBeInTheDocument()
    expect(screen.getByText('前往新手森林 →')).toBeInTheDocument()
  })

  it('calls onNavigate with /npc/novice_forest on step 1 action', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    fireEvent.click(screen.getByText('开始冒险 →'))
    fireEvent.click(screen.getByText('前往新手森林 →'))
    expect(mockOnNavigate).toHaveBeenCalledWith('/npc/novice_forest')
    expect(screen.getByText('与导师对话')).toBeInTheDocument()
  })

  it('advances to step 3 from step 2', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    fireEvent.click(screen.getByText('开始冒险 →'))
    fireEvent.click(screen.getByText('前往新手森林 →'))
    fireEvent.click(screen.getByText('知道了 →'))
    expect(screen.getByText('查看卡牌工坊')).toBeInTheDocument()
    expect(screen.getByText('前往卡牌工坊 →')).toBeInTheDocument()
  })

  it('completes onboarding on step 3 action and sets localStorage', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    fireEvent.click(screen.getByText('开始冒险 →'))
    fireEvent.click(screen.getByText('前往新手森林 →'))
    fireEvent.click(screen.getByText('知道了 →'))
    fireEvent.click(screen.getByText('前往卡牌工坊 →'))
    expect(localStorage.getItem('algomate_onboarding_completed')).toBe('true')
    expect(mockOnNavigate).toHaveBeenCalledWith('/workshop')
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('skips onboarding and sets localStorage', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    fireEvent.click(screen.getByText('跳过'))
    expect(localStorage.getItem('algomate_onboarding_completed')).toBe('true')
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('renders step indicators with correct number of dots', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)
    const dialog = screen.getByRole('dialog')
    const dots = dialog.querySelectorAll('span[class*="dot"]')
    expect(dots.length).toBe(4)
  })

  it('renders all step titles in sequence', () => {
    render(<OnboardingGuide open={true} onClose={mockOnClose} onNavigate={mockOnNavigate} />)

    const expectedTitles = ['欢迎来到算法大陆', '探索新手森林', '与导师对话', '查看卡牌工坊']

    for (let i = 0; i < expectedTitles.length; i++) {
      expect(screen.getByText(expectedTitles[i])).toBeInTheDocument()
      if (i < expectedTitles.length - 1) {
        const buttons = screen.getAllByRole('button')
        const nextBtn = buttons.find(b => b.textContent.includes('→'))
        if (nextBtn) fireEvent.click(nextBtn)
      }
    }
  })
})
