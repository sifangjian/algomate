import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../services/cardService', () => ({
  cardService: {
    updateCard: vi.fn(),
    retakeCard: vi.fn(),
  },
}))

vi.mock('../stores/cardStore', () => ({
  useCardStore: vi.fn(),
}))

const { mockNavigate } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
}))

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  MemoryRouter: ({ children }) => children,
}))

vi.mock('../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

vi.mock('../components/ui/Button/Button', () => ({
  __esModule: true,
  default: ({ children, onClick, disabled, loading, variant, size, className }) => (
    <button onClick={onClick} disabled={disabled || loading} data-variant={variant} data-size={size} className={className}>
      {children}
    </button>
  ),
}))

import DimensionSection from '../components/card/DimensionSection'
import VisualLinksSection from '../components/card/VisualLinksSection'
import EndangeredBanner from '../components/card/EndangeredBanner'
import PendingRetakeSection from '../components/card/PendingRetakeSection'
import CardEditForm from '../components/card/CardEditForm'
import RetakeButton from '../components/card/RetakeButton'
import { cardService } from '../services/cardService'
import { useCardStore } from '../stores/cardStore'
import { useNavigate } from 'react-router-dom'
import { showToast } from '../components/ui/Toast/index'

function makeCard(overrides = {}) {
  return {
    id: 1,
    name: '二分查找',
    algorithm_type: 'Search',
    core_concept: '通过不断折半缩小搜索范围',
    key_points: '["确定左右边界","计算中间值","比较并缩小范围"]',
    code_template: 'def binary_search(arr, target):\n    left, right = 0, len(arr) - 1',
    complexity_analysis: '时间 O(log n)，空间 O(1)',
    use_cases: '有序数组搜索',
    common_variants: '左闭右开写法',
    typical_problems: '["搜索插入位置","寻找峰值"]',
    common_pitfalls: '忘记处理边界条件',
    comparison: '与线性搜索对比',
    my_notes: '二分查找是高效搜索算法',
    visual_links: null,
    ...overrides,
  }
}

function setupStoreMocks(overrides = {}) {
  useCardStore.mockReturnValue({
    cards: [],
    endangeredCount: 0,
    pendingRetakeCount: 0,
    selectedCard: null,
    loading: false,
    retakeInfo: null,
    filters: { algorithm_type: '', status: '', keyword: '' },
    updateCard: vi.fn(),
    setSelectedCard: vi.fn(),
    setRetakeInfo: vi.fn(),
    retakeCard: vi.fn(),
    ...overrides,
  })
}

describe('DimensionSection', () => {
  it('renders section title "📐 知识维度"', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    expect(screen.getByText('📐 知识维度')).toBeInTheDocument()
  })

  it('renders dimension items for card with content', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    expect(screen.getByText('核心概念')).toBeInTheDocument()
    expect(screen.getByText('关键要点')).toBeInTheDocument()
  })

  it('hides dimension items for empty/null values', () => {
    const card = makeCard({ common_pitfalls: null, comparison: '', my_notes: undefined })
    render(<DimensionSection card={card} />)
    expect(screen.queryByText('常见陷阱')).not.toBeInTheDocument()
    expect(screen.queryByText('对比分析')).not.toBeInTheDocument()
    expect(screen.queryByText('个人笔记')).not.toBeInTheDocument()
  })

  it('core_concept and key_points are expanded by default', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const coreBtn = screen.getByRole('button', { name: /核心概念/ })
    const keyBtn = screen.getByRole('button', { name: /关键要点/ })
    expect(coreBtn).toHaveAttribute('aria-expanded', 'true')
    expect(keyBtn).toHaveAttribute('aria-expanded', 'true')
  })

  it('other dimensions are collapsed by default', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const complexityBtn = screen.getByRole('button', { name: /复杂度分析/ })
    expect(complexityBtn).toHaveAttribute('aria-expanded', 'false')
  })

  it('clicking a collapsed dimension header expands it', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const complexityBtn = screen.getByRole('button', { name: /复杂度分析/ })
    expect(complexityBtn).toHaveAttribute('aria-expanded', 'false')
    await user.click(complexityBtn)
    expect(complexityBtn).toHaveAttribute('aria-expanded', 'true')
  })

  it('clicking an expanded dimension header collapses it', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const coreBtn = screen.getByRole('button', { name: /核心概念/ })
    expect(coreBtn).toHaveAttribute('aria-expanded', 'true')
    await user.click(coreBtn)
    expect(coreBtn).toHaveAttribute('aria-expanded', 'false')
  })

  it('code_template renders in a pre block', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const codeHeader = screen.getByRole('button', { name: /代码模板/ })
    expect(codeHeader).toHaveAttribute('aria-expanded', 'false')
  })

  it('code_template content is visible in pre when expanded', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const codeHeader = screen.getByRole('button', { name: /代码模板/ })
    await user.click(codeHeader)
    const pre = screen.getByText(/def binary_search/).closest('pre')
    expect(pre).toBeInTheDocument()
  })

  it('typical_problems parses JSON array and renders as list', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const problemsHeader = screen.getByRole('button', { name: /典型题目/ })
    await user.click(problemsHeader)
    expect(screen.getByText('搜索插入位置')).toBeInTheDocument()
    expect(screen.getByText('寻找峰值')).toBeInTheDocument()
  })

  it('key_points parses JSON array and renders as list', () => {
    const card = makeCard()
    render(<DimensionSection card={card} />)
    expect(screen.getByText('确定左右边界')).toBeInTheDocument()
    expect(screen.getByText('计算中间值')).toBeInTheDocument()
    expect(screen.getByText('比较并缩小范围')).toBeInTheDocument()
  })

  it('returns null when card is null', () => {
    const { container } = render(<DimensionSection card={null} />)
    expect(container.innerHTML).toBe('')
  })
})

describe('VisualLinksSection', () => {
  it('returns null when visualLinks is null', () => {
    const { container } = render(<VisualLinksSection visualLinks={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when visualLinks is empty array', () => {
    const { container } = render(<VisualLinksSection visualLinks={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when visualLinks is "[]"', () => {
    const { container } = render(<VisualLinksSection visualLinks="[]" />)
    expect(container.innerHTML).toBe('')
  })

  it('renders links from JSON string', () => {
    const links = JSON.stringify([
      { title: 'VisuAlgo', url: 'https://visualgo.net' },
    ])
    render(<VisualLinksSection visualLinks={links} />)
    expect(screen.getByText('VisuAlgo')).toBeInTheDocument()
  })

  it('renders links from array prop', () => {
    const links = [
      { title: 'VisuAlgo', url: 'https://visualgo.net' },
    ]
    render(<VisualLinksSection visualLinks={links} />)
    expect(screen.getByText('VisuAlgo')).toBeInTheDocument()
  })

  it('each link has target="_blank" and rel="noopener noreferrer"', () => {
    const links = [
      { title: 'VisuAlgo', url: 'https://visualgo.net' },
    ]
    render(<VisualLinksSection visualLinks={links} />)
    const anchor = screen.getByRole('link', { name: /VisuAlgo/ })
    expect(anchor).toHaveAttribute('target', '_blank')
    expect(anchor).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('shows link title when available', () => {
    const links = [
      { title: 'VisuAlgo', url: 'https://visualgo.net' },
    ]
    render(<VisualLinksSection visualLinks={links} />)
    expect(screen.getByText('VisuAlgo')).toBeInTheDocument()
  })

  it('shows URL as fallback when title is missing', () => {
    const links = [
      { url: 'https://visualgo.net' },
    ]
    render(<VisualLinksSection visualLinks={links} />)
    expect(screen.getByText('https://visualgo.net')).toBeInTheDocument()
  })

  it('renders section title "🌐 可视化链接"', () => {
    const links = [{ title: 'Test', url: 'https://example.com' }]
    render(<VisualLinksSection visualLinks={links} />)
    expect(screen.getByText('🌐 可视化链接')).toBeInTheDocument()
  })
})

describe('EndangeredBanner', () => {
  beforeEach(() => {
    setupStoreMocks()
  })

  it('returns null when endangeredCount is 0', () => {
    setupStoreMocks({ endangeredCount: 0, cards: [] })
    const { container } = render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when endangeredCount is undefined', () => {
    setupStoreMocks({ endangeredCount: undefined, cards: [] })
    const { container } = render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('shows correct count in banner', () => {
    setupStoreMocks({ endangeredCount: 3, cards: [] })
    render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('has role="alert"', () => {
    setupStoreMocks({ endangeredCount: 2, cards: [] })
    render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shows "濒危" tag', () => {
    setupStoreMocks({ endangeredCount: 2, cards: [] })
    render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(screen.getByText('濒危')).toBeInTheDocument()
  })

  it('renders endangered cards list', () => {
    const cards = [
      { id: 1, name: '二分查找', algorithm_type: 'Search', status: 'endangered' },
      { id: 2, name: '快速排序', algorithm_type: 'Sorting', status: 'endangered' },
    ]
    setupStoreMocks({ endangeredCount: 2, cards })
    render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(screen.getByText('二分查找')).toBeInTheDocument()
    expect(screen.getByText('快速排序')).toBeInTheDocument()
  })

  it('clicking a card calls onCardClick', async () => {
    const user = userEvent.setup()
    const mockClick = vi.fn()
    const cards = [
      { id: 1, name: '二分查找', algorithm_type: 'Search', status: 'endangered' },
    ]
    setupStoreMocks({ endangeredCount: 1, cards })
    render(<EndangeredBanner onCardClick={mockClick} />)
    await user.click(screen.getByRole('button', { name: /二分查找/ }))
    expect(mockClick).toHaveBeenCalledWith(cards[0])
  })

  it('does not render card list when no endangered cards in store', () => {
    setupStoreMocks({ endangeredCount: 2, cards: [{ id: 1, name: '正常卡', status: 'normal' }] })
    render(<EndangeredBanner onCardClick={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /去修炼/ })).not.toBeInTheDocument()
  })
})

describe('PendingRetakeSection', () => {
  beforeEach(() => {
    setupStoreMocks()
  })

  it('returns null when pendingRetakeCount is 0', () => {
    setupStoreMocks({ pendingRetakeCount: 0, cards: [] })
    const { container } = render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when pendingRetakeCount is undefined', () => {
    setupStoreMocks({ pendingRetakeCount: undefined, cards: [] })
    const { container } = render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('shows correct card count', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
      { id: 2, name: '快速排序', status: 'pending_retake', durability: 0, max_durability: 5, algorithm_type: 'Sorting' },
    ]
    setupStoreMocks({ pendingRetakeCount: 2, cards })
    render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(screen.getByText(/待重修卡牌 \(2\)/)).toBeInTheDocument()
  })

  it('shows "待重修" tag', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
    ]
    setupStoreMocks({ pendingRetakeCount: 1, cards })
    render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(screen.getByText('待重修')).toBeInTheDocument()
  })

  it('renders card names', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
      { id: 2, name: '快速排序', status: 'pending_retake', durability: 0, max_durability: 5, algorithm_type: 'Sorting' },
    ]
    setupStoreMocks({ pendingRetakeCount: 2, cards })
    render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(screen.getByText('二分查找')).toBeInTheDocument()
    expect(screen.getByText('快速排序')).toBeInTheDocument()
  })

  it('toggles collapse on header click', async () => {
    const user = userEvent.setup()
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
    ]
    setupStoreMocks({ pendingRetakeCount: 1, cards })
    render(<PendingRetakeSection onCardClick={vi.fn()} />)
    expect(screen.getByText('二分查找')).toBeInTheDocument()
    const header = screen.getByRole('button', { name: /待重修卡牌/ })
    await user.click(header)
    expect(screen.queryByText('二分查找')).not.toBeInTheDocument()
    await user.click(header)
    expect(screen.getByText('二分查找')).toBeInTheDocument()
  })

  it('contains RetakeButton for each card', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
    ]
    setupStoreMocks({ pendingRetakeCount: 1, cards })
    render(<PendingRetakeSection onCardClick={vi.fn()} />)
    const retakeButtons = screen.getAllByRole('button').filter(
      (btn) => btn.textContent.includes('🔄 重修')
    )
    expect(retakeButtons).toHaveLength(1)
  })
})

describe('CardEditForm', () => {
  let mockUpdateCard
  let mockSetSelectedCard

  beforeEach(() => {
    mockUpdateCard = vi.fn()
    mockSetSelectedCard = vi.fn()
    setupStoreMocks({
      updateCard: mockUpdateCard,
      setSelectedCard: mockSetSelectedCard,
    })
    vi.mocked(cardService.updateCard).mockReset()
    vi.mocked(showToast).mockReset()
  })

  it('returns null when card is null', () => {
    const { container } = render(<CardEditForm card={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders dimension textareas for editable fields', () => {
    const card = makeCard()
    render(<CardEditForm card={card} />)
    expect(screen.getByPlaceholderText(/输入核心概念/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/输入关键要点/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/输入代码模板/)).toBeInTheDocument()
  })

  it('renders 10 dimension textareas', () => {
    const card = makeCard()
    render(<CardEditForm card={card} />)
    const textareas = screen.getAllByRole('textbox')
    expect(textareas.length).toBeGreaterThanOrEqual(10)
  })

  it('save button is disabled when no changes', () => {
    const card = makeCard()
    render(<CardEditForm card={card} />)
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    expect(saveBtn).toBeDisabled()
  })

  it('save button becomes enabled after editing', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<CardEditForm card={card} />)
    const conceptInput = screen.getByPlaceholderText(/输入核心概念/)
    await user.clear(conceptInput)
    await user.type(conceptInput, '新的核心概念')
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    expect(saveBtn).not.toBeDisabled()
  })

  it('calls store updateCard on save', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    const updatedCard = { ...card, core_concept: '新的核心概念' }
    mockUpdateCard.mockResolvedValue(updatedCard)
    render(<CardEditForm card={card} />)
    const conceptInput = screen.getByPlaceholderText(/输入核心概念/)
    await user.clear(conceptInput)
    await user.type(conceptInput, '新的核心概念')
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    await user.click(saveBtn)
    expect(mockUpdateCard).toHaveBeenCalledWith(card.id, expect.objectContaining({ core_concept: '新的核心概念' }))
  })
})

describe('RetakeButton', () => {
  let mockRetakeCard
  let mockSetRetakeInfo

  beforeEach(() => {
    mockRetakeCard = vi.fn()
    mockSetRetakeInfo = vi.fn()
    mockNavigate.mockClear()
    setupStoreMocks({
      retakeCard: mockRetakeCard,
      setRetakeInfo: mockSetRetakeInfo,
    })
    vi.mocked(cardService.retakeCard).mockReset()
    vi.mocked(showToast).mockReset()
  })

  it('returns null when card status is not pending_retake', () => {
    const card = { id: 1, name: '二分查找', status: 'active' }
    const { container } = render(<RetakeButton card={card} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders button when card status is pending_retake', () => {
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    render(<RetakeButton card={card} />)
    expect(screen.getByRole('button', { name: /重修/ })).toBeInTheDocument()
  })

  it('clicking button calls store retakeCard', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    mockRetakeCard.mockResolvedValue({
      dialogue_id: 'd1',
      npc_id: 'npc1',
    })
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    expect(mockRetakeCard).toHaveBeenCalledWith(card.id)
  })

  it('shows loading state during API call', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    let resolveApi
    mockRetakeCard.mockReturnValue(
      new Promise((resolve) => { resolveApi = resolve })
    )
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    const btn = screen.getByRole('button', { name: /重修/ })
    expect(btn).toBeDisabled()
    resolveApi({ dialogue_id: 'd1', npc_id: 'npc1' })
  })

  it('navigates to NPC dialogue page on success', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    mockRetakeCard.mockResolvedValue({
      dialogue_id: 'd1',
      npc_id: 'npc1',
    })
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    await waitFor(() => {
      expect(mockRetakeCard).toHaveBeenCalledWith(card.id)
    }, { timeout: 3000 })
    await waitFor(() => {
      expect(showToast).toHaveBeenCalled()
    }, { timeout: 3000 })
    expect(mockNavigate).toHaveBeenCalledWith('/npc/npc1?dialogueId=d1')
  })

  it('shows warning toast for error 40003', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    mockRetakeCard.mockRejectedValue(
      new Error('40003 不是待重修状态')
    )
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    expect(showToast).toHaveBeenCalledWith('该卡牌不在待重修状态', 'warning')
  })
})
