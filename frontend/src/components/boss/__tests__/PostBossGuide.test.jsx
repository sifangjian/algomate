import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock('../../../stores/guideStore', () => ({
  useGuideStore: vi.fn(),
}))

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} disabled={disabled || loading} {...rest}>{children}</button>
  ),
}))

import PostBossGuide from '../PostBossGuide'
import { useGuideStore } from '../../../stores/guideStore'

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

describe('PostBossGuide', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGuideStore.mockReturnValue({
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('胜利时渲染"继续挑战"和"去修炼巩固"按钮', () => {
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    expect(screen.getByRole('button', { name: /继续挑战/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去修炼巩固/ })).not.toBeNull()
  })

  it('失败时渲染"去修炼巩固"和"去重新修习"按钮', () => {
    render(<PostBossGuide guide={defeatGuide} scene="after_boss" />)

    expect(screen.getByRole('button', { name: /去修炼巩固/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去重新修习/ })).not.toBeNull()
  })

  it('点击引导按钮应通过useGuideNavigation导航', async () => {
    const user = userEvent.setup()
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    await user.click(screen.getByRole('button', { name: /继续挑战/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/boss')
  })

  it('点击"去修炼巩固"按钮应导航到/review', async () => {
    const user = userEvent.setup()
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    await user.click(screen.getByRole('button', { name: /去修炼巩固/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/review')
  })

  it('点击带params的引导按钮应携带查询参数导航', async () => {
    const user = userEvent.setup()
    render(<PostBossGuide guide={defeatGuide} scene="after_boss" />)

    await user.click(screen.getByRole('button', { name: /去重新修习/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/?npc_id=2')
  })

  it('available为false的按钮不渲染', () => {
    const guideWithDisabled = {
      available_actions: [
        { action: 'continue_challenge', label: '继续挑战', target_path: '/boss', params: null, available: false },
        { action: 'go_review', label: '去修炼巩固', target_path: '/review', params: null, available: true },
      ],
      message: '挑战成功！',
    }
    render(<PostBossGuide guide={guideWithDisabled} scene="after_boss" />)

    expect(screen.queryByRole('button', { name: /继续挑战/ })).toBeNull()
    expect(screen.getByRole('button', { name: /去修炼巩固/ })).not.toBeNull()
  })

  it('guide为null时不渲染任何内容', () => {
    const { container } = render(<PostBossGuide guide={null} scene="after_boss" />)

    expect(container.innerHTML).toBe('')
  })

  it('渲染引导消息', () => {
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    expect(screen.getByText('挑战成功！')).not.toBeNull()
  })

  it('应渲染跳过按钮', () => {
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    expect(screen.getByRole('button', { name: /跳过/ })).not.toBeNull()
  })

  it('点击跳过按钮应调用skipGuide并传入scene', async () => {
    const mockSkipGuide = vi.fn()
    useGuideStore.mockReturnValue({
      skipGuide: mockSkipGuide,
      shouldShowGuide: vi.fn(() => true),
    })
    const user = userEvent.setup()
    render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    await user.click(screen.getByRole('button', { name: /跳过/ }))

    expect(mockSkipGuide).toHaveBeenCalledWith('after_boss')
  })

  it('shouldShowGuide返回false时不渲染', () => {
    useGuideStore.mockReturnValue({
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => false),
    })
    const { container } = render(<PostBossGuide guide={victoryGuide} scene="after_boss" />)

    expect(container.innerHTML).toBe('')
  })

  it('无可引导目标时（所有available为false）不渲染引导按钮', () => {
    const guideAllUnavailable = {
      available_actions: [
        { action: 'continue_challenge', label: '继续挑战', target_path: '/boss', params: null, available: false },
        { action: 'go_review', label: '去修炼巩固', target_path: '/review', params: null, available: false },
      ],
      message: '挑战成功！',
    }
    render(<PostBossGuide guide={guideAllUnavailable} scene="after_boss" />)

    expect(screen.queryByRole('button', { name: /继续挑战/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /去修炼巩固/ })).toBeNull()
  })
})
