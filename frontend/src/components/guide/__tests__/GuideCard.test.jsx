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
  default: ({ children, onClick, disabled, variant, ...rest }) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} {...rest}>{children}</button>
  ),
}))

import GuideCard from '../GuideCard'
import { useGuideStore } from '../../../stores/guideStore'

const GUIDE_TWO_AVAILABLE = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战巩固', target_path: '/boss', params: { card_id: 1 }, available: true },
    { action: 'go_workshop', label: '去卡牌工坊完善', target_path: '/workshop', params: { card_id: 1, expand: true }, available: true },
  ],
  message: '恭喜获得卡牌！',
}

const GUIDE_ONE_AVAILABLE_ONE_UNAVAILABLE = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战', target_path: '/boss', available: true },
    { action: 'continue_review', label: '继续修炼', target_path: '/review', available: false },
  ],
  message: '请选择下一步',
}

const GUIDE_ALL_UNAVAILABLE = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战', target_path: '/boss', available: false },
    { action: 'continue_review', label: '继续修炼', target_path: '/review', available: false },
  ],
  message: '请选择下一步',
}

const GUIDE_SINGLE_ACTION = {
  available_actions: [
    { action: 'go_workshop', label: '去卡牌工坊查看', target_path: '/workshop', available: true },
  ],
  message: '卡牌生成失败',
}

describe('GuideCard', () => {
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

  it('应渲染引导消息', () => {
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)
    expect(screen.getByText('恭喜获得卡牌！')).not.toBeNull()
  })

  it('应渲染所有可用引导按钮', () => {
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)
    expect(screen.getByRole('button', { name: /去 Boss 战巩固/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去卡牌工坊完善/ })).not.toBeNull()
  })

  it('available为false的按钮不渲染', () => {
    render(<GuideCard guide={GUIDE_ONE_AVAILABLE_ONE_UNAVAILABLE} scene="after_dialogue" />)
    expect(screen.getByRole('button', { name: /去 Boss 战/ })).not.toBeNull()
    expect(screen.queryByRole('button', { name: /继续修炼/ })).toBeNull()
  })

  it('所有action都不可用时不渲染引导按钮', () => {
    render(<GuideCard guide={GUIDE_ALL_UNAVAILABLE} scene="after_dialogue" />)
    expect(screen.queryByRole('button', { name: /去 Boss 战/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /继续修炼/ })).toBeNull()
  })

  it('仅一个可用action时渲染一个引导按钮', () => {
    render(<GuideCard guide={GUIDE_SINGLE_ACTION} scene="after_dialogue" />)
    expect(screen.getByRole('button', { name: /去卡牌工坊查看/ })).not.toBeNull()
  })

  it('应渲染跳过按钮', () => {
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)
    expect(screen.getByRole('button', { name: /跳过/ })).not.toBeNull()
  })

  it('点击跳过按钮应调用skipGuide并传入scene', async () => {
    const mockSkipGuide = vi.fn()
    useGuideStore.mockReturnValue({
      skipGuide: mockSkipGuide,
      shouldShowGuide: vi.fn(() => true),
    })
    const user = userEvent.setup()
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)

    await user.click(screen.getByRole('button', { name: /跳过/ }))

    expect(mockSkipGuide).toHaveBeenCalledWith('after_dialogue')
  })

  it('点击引导按钮应通过useGuideNavigation导航', async () => {
    const user = userEvent.setup()
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)

    await user.click(screen.getByRole('button', { name: /去 Boss 战巩固/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/boss?card_id=1')
  })

  it('点击带多参数的引导按钮应正确拼接查询参数', async () => {
    const user = userEvent.setup()
    render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)

    await user.click(screen.getByRole('button', { name: /去卡牌工坊完善/ }))

    expect(mockNavigate).toHaveBeenCalledWith('/workshop?card_id=1&expand=true')
  })

  it('shouldShowGuide返回false时不渲染', () => {
    useGuideStore.mockReturnValue({
      skipGuide: vi.fn(),
      shouldShowGuide: vi.fn(() => false),
    })
    const { container } = render(<GuideCard guide={GUIDE_TWO_AVAILABLE} scene="after_dialogue" />)
    expect(container.innerHTML).toBe('')
  })

  it('guide为null时不渲染', () => {
    const { container } = render(<GuideCard guide={null} scene="after_dialogue" />)
    expect(container.innerHTML).toBe('')
  })

  it('guide为undefined时不渲染', () => {
    const { container } = render(<GuideCard scene="after_dialogue" />)
    expect(container.innerHTML).toBe('')
  })

  it('所有action不可用时整体不渲染', () => {
    const { container } = render(<GuideCard guide={GUIDE_ALL_UNAVAILABLE} scene="after_dialogue" />)
    expect(container.innerHTML).toBe('')
  })
})
