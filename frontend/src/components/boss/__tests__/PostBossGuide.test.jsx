import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PostBossGuide from '../PostBossGuide'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} disabled={disabled || loading} {...rest}>{children}</button>
  ),
}))

describe('PostBossGuide', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  const victoryGuide = {
    available_actions: [
      { action: 'continue_challenge', label: '继续挑战', target_path: '/boss', params: null, available: true },
      { action: 'go_review', label: '去修炼巩固', target_path: '/review', params: null, available: true },
    ],
    message: '挑战成功！',
  }

  const defeatGuide = {
    available_actions: [
      { action: 'go_review', label: '去修炼巩固', target_path: '/review', params: null, available: true },
      { action: 'go_dialogue', label: '去重新修习', target_path: '/', params: { npc_id: 2 }, available: true },
    ],
    message: '挑战失败，建议修炼巩固',
  }

  it('胜利时渲染"继续挑战"和"去修炼巩固"按钮', () => {
    const onAction = vi.fn()
    render(<PostBossGuide guide={victoryGuide} onAction={onAction} />)

    expect(screen.getByRole('button', { name: /继续挑战/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去修炼巩固/ })).not.toBeNull()
  })

  it('失败时渲染"去修炼巩固"和"去重新修习"按钮', () => {
    const onAction = vi.fn()
    render(<PostBossGuide guide={defeatGuide} onAction={onAction} />)

    expect(screen.getByRole('button', { name: /去修炼巩固/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去重新修习/ })).not.toBeNull()
  })

  it('点击引导按钮应触发onAction并传入对应action', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    render(<PostBossGuide guide={victoryGuide} onAction={onAction} />)

    await user.click(screen.getByRole('button', { name: /继续挑战/ }))

    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction).toHaveBeenCalledWith(victoryGuide.available_actions[0])
  })

  it('点击"去修炼巩固"按钮应触发onAction', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    render(<PostBossGuide guide={victoryGuide} onAction={onAction} />)

    await user.click(screen.getByRole('button', { name: /去修炼巩固/ }))

    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction).toHaveBeenCalledWith(victoryGuide.available_actions[1])
  })

  it('available为false的按钮应被禁用', () => {
    const guideWithDisabled = {
      available_actions: [
        { action: 'continue_challenge', label: '继续挑战', target_path: '/boss', params: null, available: false },
        { action: 'go_review', label: '去修炼巩固', target_path: '/review', params: null, available: true },
      ],
      message: '挑战成功！',
    }
    const onAction = vi.fn()
    render(<PostBossGuide guide={guideWithDisabled} onAction={onAction} />)

    const continueButton = screen.getByRole('button', { name: /继续挑战/ })
    expect(continueButton.disabled).toBe(true)
    const reviewButton = screen.getByRole('button', { name: /去修炼巩固/ })
    expect(reviewButton.disabled).toBe(false)
  })

  it('guide为null时不渲染任何内容', () => {
    const onAction = vi.fn()
    const { container } = render(<PostBossGuide guide={null} onAction={onAction} />)

    expect(container.innerHTML).toBe('')
  })

  it('渲染引导消息', () => {
    const onAction = vi.fn()
    render(<PostBossGuide guide={victoryGuide} onAction={onAction} />)

    expect(screen.getByText('挑战成功！')).not.toBeNull()
  })
})
