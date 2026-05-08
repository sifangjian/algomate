import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import WelcomeModal from '../WelcomeModal'

describe('WelcomeModal', () => {
  const mockOnStart = vi.fn()
  const mockOnSkip = vi.fn()

  beforeEach(() => {
    mockOnStart.mockClear()
    mockOnSkip.mockClear()
  })

  it('renders welcome modal with intro text and start button', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    expect(screen.getByText('欢迎来到算法大陆')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /开始冒险/ })).toBeInTheDocument()
  })

  it('renders story introduction paragraphs', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    expect(screen.getByText(/在这片神秘的大陆上/)).toBeInTheDocument()
    expect(screen.getByText(/跟随导师修习/)).toBeInTheDocument()
    expect(screen.getByText(/成为算法大陆的至强者/)).toBeInTheDocument()
  })

  it('renders skip button', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    expect(screen.getByRole('button', { name: /跳过新手引导/ })).toBeInTheDocument()
  })

  it('calls onStart when clicking start button', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    fireEvent.click(screen.getByRole('button', { name: /开始冒险/ }))
    expect(mockOnStart).toHaveBeenCalledTimes(1)
  })

  it('shows confirm dialog when clicking skip button', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    fireEvent.click(screen.getByRole('button', { name: /跳过新手引导/ }))
    expect(screen.getByText('是否跳过引导？')).toBeInTheDocument()
  })

  it('calls onSkip when confirming skip in dialog', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    fireEvent.click(screen.getByRole('button', { name: /跳过新手引导/ }))
    const confirmButtons = screen.getAllByRole('button', { name: /确认/ })
    fireEvent.click(confirmButtons[confirmButtons.length - 1])
    expect(mockOnSkip).toHaveBeenCalledTimes(1)
  })

  it('closes confirm dialog when clicking cancel', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    fireEvent.click(screen.getByRole('button', { name: /跳过新手引导/ }))
    expect(screen.getByText('是否跳过引导？')).toBeInTheDocument()

    const cancelButtons = screen.getAllByRole('button', { name: /取消/ })
    fireEvent.click(cancelButtons[cancelButtons.length - 1])
    expect(screen.queryByText('是否跳过引导？')).not.toBeInTheDocument()
  })

  it('renders step indicator showing step 1 of 5', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    const indicator = screen.getByLabelText('引导步骤 1/5')
    expect(indicator).toBeInTheDocument()
  })

  it('has correct ARIA attributes for accessibility', () => {
    render(<WelcomeModal onStart={mockOnStart} onSkip={mockOnSkip} />)

    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-label', '欢迎引导')
  })
})
