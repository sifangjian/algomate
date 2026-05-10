import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
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
  default: ({ children, onClick, disabled, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled ? 'true' : undefined} data-variant={variant} {...rest}>{children}</button>
  ),
}))

import PostDialogueGuide from '../PostDialogueGuide'
import { useGuideStore } from '../../../stores/guideStore'

const GUIDE_WITH_TWO_ACTIONS = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战巩固', target_path: '/boss/battle', params: { cardId: 1 }, available: true },
    { action: 'go_workshop', label: '去卡牌工坊完善', target_path: '/workshop', params: { cardId: 1, expand: true }, available: true },
  ],
  message: '恭喜获得卡牌「背包问题」！',
}

const GUIDE_WITH_BOSS_UNAVAILABLE = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战巩固', target_path: '/boss/battle', params: { cardId: 1 }, available: false },
    { action: 'go_workshop', label: '去卡牌工坊完善', target_path: '/workshop', params: { cardId: 1, expand: true }, available: true },
  ],
  message: '恭喜获得卡牌「背包问题」！',
}

const GUIDE_WITH_ONLY_WORKSHOP = {
  available_actions: [
    { action: 'go_workshop', label: '去卡牌工坊查看', target_path: '/workshop', available: true },
  ],
  message: '卡牌生成失败，对话记录已保存',
}

describe('PostDialogueGuide', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGuideStore.mockReturnValue({
      currentGuide: null,
      visible: false,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('当 visible 为 false 时不渲染', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: false,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    const { container } = render(<PostDialogueGuide />)
    expect(container.innerHTML).toBe('')
  })

  it('当 currentGuide 为 null 时不渲染', () => {
    useGuideStore.mockReturnValue({
      currentGuide: null,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    const { container } = render(<PostDialogueGuide />)
    expect(container.innerHTML).toBe('')
  })

  it('渲染两个可用引导按钮', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    render(<PostDialogueGuide />)

    expect(screen.getByRole('button', { name: /去 Boss 战巩固/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去卡牌工坊完善/ })).not.toBeNull()
  })

  it('go_boss 不可用时仅显示 go_workshop 按钮', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_BOSS_UNAVAILABLE,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    render(<PostDialogueGuide />)

    expect(screen.queryByRole('button', { name: /去 Boss 战巩固/ })).toBeNull()
    expect(screen.getByRole('button', { name: /去卡牌工坊完善/ })).not.toBeNull()
  })

  it('仅有一个可用动作时只渲染一个按钮', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_ONLY_WORKSHOP,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    render(<PostDialogueGuide />)

    expect(screen.getByRole('button', { name: /去卡牌工坊查看/ })).not.toBeNull()
    const guideButtons = screen.getAllByRole('button').filter(b => b.textContent !== '跳过')
    expect(guideButtons.length).toBe(1)
  })

  it('渲染跳过按钮', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    render(<PostDialogueGuide />)

    expect(screen.getByRole('button', { name: /跳过/ })).not.toBeNull()
  })

  it('点击跳过按钮调用 skipGuide', async () => {
    const mockSkipGuide = vi.fn()
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: mockSkipGuide,
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    const user = userEvent.setup()
    render(<PostDialogueGuide />)

    await user.click(screen.getByRole('button', { name: /跳过/ }))

    expect(mockSkipGuide).toHaveBeenCalledWith('after_dialogue')
  })

  it('点击引导按钮跳转到对应路径并携带参数', async () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    const user = userEvent.setup()
    render(<PostDialogueGuide />)

    await user.click(screen.getByRole('button', { name: /去 Boss 战巩固/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/boss/battle?cardId=1')
  })

  it('点击 go_workshop 按钮跳转并携带 cardId 和 expand 参数', async () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    const user = userEvent.setup()
    render(<PostDialogueGuide />)

    await user.click(screen.getByRole('button', { name: /去卡牌工坊完善/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/workshop?cardId=1&expand=true')
  })

  it('渲染引导消息文本', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => true),
      dismissGuide: vi.fn(),
    })
    render(<PostDialogueGuide />)

    expect(screen.getByText(/恭喜获得卡牌「背包问题」！/)).not.toBeNull()
  })

  it('已跳过的场景不渲染', () => {
    useGuideStore.mockReturnValue({
      currentGuide: GUIDE_WITH_TWO_ACTIONS,
      visible: true,
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => false),
      dismissGuide: vi.fn(),
    })
    const { container } = render(<PostDialogueGuide />)
    expect(container.innerHTML).toBe('')
  })
})
