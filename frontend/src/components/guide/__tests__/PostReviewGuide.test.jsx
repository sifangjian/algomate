import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../../../stores/guideStore', () => ({
  useGuideStore: vi.fn(),
}))

vi.mock('../../components/ui/Button/Button', () => ({
  __esModule: true,
  default: ({ children, onClick, disabled, variant, ...rest }) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} {...rest}>{children}</button>
  ),
}))

import PostReviewGuide from '../PostReviewGuide'
import { useGuideStore } from '../../../stores/guideStore'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

const GUIDE_BOTH_AVAILABLE = {
  available_actions: [
    { action: 'continue_review', label: '继续修炼', target_path: '/review', available: true },
    { action: 'go_boss', label: '去 Boss 战检验', target_path: '/boss', available: true },
  ],
  message: '还有 1 张卡牌濒危，是否继续修炼？',
}

const GUIDE_CONTINUE_UNAVAILABLE = {
  available_actions: [
    { action: 'continue_review', label: '继续修炼', target_path: '/review', available: false },
    { action: 'go_boss', label: '去 Boss 战检验', target_path: '/boss', available: true },
  ],
  message: '所有卡牌状态良好，去 Boss 战检验学习成果吧！',
}

describe('PostReviewGuide', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染引导消息', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    expect(screen.getByText(/还有 1 张卡牌濒危/)).toBeInTheDocument()
  })

  it('两个 action 都 available 时应渲染 2 个按钮', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    expect(screen.getByRole('button', { name: /继续修炼/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去 Boss 战检验/ })).not.toBeNull()
  })

  it('continue_review available=false 时不应渲染继续修炼按钮', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_CONTINUE_UNAVAILABLE} scene="after_review" />)
    expect(screen.queryByRole('button', { name: /继续修炼/ })).toBeNull()
    expect(screen.getByRole('button', { name: /去 Boss 战检验/ })).not.toBeNull()
  })

  it('点击继续修炼应导航到 /review', async () => {
    const user = userEvent.setup()
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    await user.click(screen.getByRole('button', { name: /继续修炼/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/review')
  })

  it('点击去 Boss 战检验应导航到 /boss', async () => {
    const user = userEvent.setup()
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    await user.click(screen.getByRole('button', { name: /去 Boss 战检验/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/boss')
  })

  it('应渲染跳过按钮', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    expect(screen.getByRole('button', { name: /跳过/ })).not.toBeNull()
  })

  it('点击跳过应调用 skipGuide', async () => {
    const user = userEvent.setup()
    const mockSkipGuide = vi.fn()
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: mockSkipGuide,
    })
    render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    await user.click(screen.getByRole('button', { name: /跳过/ }))
    expect(mockSkipGuide).toHaveBeenCalledWith('after_review')
  })

  it('shouldShowGuide 返回 false 时不渲染', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => false),
      skipGuide: vi.fn(),
    })
    const { container } = render(<PostReviewGuide guide={GUIDE_BOTH_AVAILABLE} scene="after_review" />)
    expect(container.innerHTML).toBe('')
  })

  it('guide 为 null 时不渲染', () => {
    useGuideStore.mockReturnValue({
      shouldShowGuide: vi.fn(() => true),
      skipGuide: vi.fn(),
    })
    const { container } = render(<PostReviewGuide guide={null} scene="after_review" />)
    expect(container.innerHTML).toBe('')
  })
})
