import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
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

vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}))

vi.mock('../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
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
    time_complexity: 'O(log n)',
    space_complexity: 'O(1)',
    typical_problems: '["搜索插入位置","寻找峰值"]',
    common_mistakes: '忘记处理边界条件',
    optimization: '可以使用位运算替代除法',
    extensions: '变体：查找第一个/最后一个等于目标值的元素',
    summary: '二分查找是高效搜索算法',
    ...overrides,
  }
}

function setupStoreMocks() {
  useCardStore.mockReturnValue({
    updateCard: vi.fn(),
    setSelectedCard: vi.fn(),
    setRetakeInfo: vi.fn(),
  })
  useNavigate.mockReturnValue(vi.fn())
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
    const card = makeCard({ common_mistakes: null, optimization: '', extensions: undefined })
    render(<DimensionSection card={card} />)
    expect(screen.queryByText('常见错误')).not.toBeInTheDocument()
    expect(screen.queryByText('优化思路')).not.toBeInTheDocument()
    expect(screen.queryByText('扩展知识')).not.toBeInTheDocument()
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
    const timeBtn = screen.getByRole('button', { name: /时间复杂度/ })
    expect(timeBtn).toHaveAttribute('aria-expanded', 'false')
  })

  it('clicking a collapsed dimension header expands it', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<DimensionSection card={card} />)
    const timeBtn = screen.getByRole('button', { name: /时间复杂度/ })
    expect(timeBtn).toHaveAttribute('aria-expanded', 'false')
    await user.click(timeBtn)
    expect(timeBtn).toHaveAttribute('aria-expanded', 'true')
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
  it('returns null when count is 0', () => {
    const { container } = render(
      <EndangeredBanner count={0} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('returns null when count is undefined', () => {
    const { container } = render(
      <EndangeredBanner count={undefined} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('shows correct count in banner', () => {
    render(
      <EndangeredBanner count={3} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('has role="alert"', () => {
    render(
      <EndangeredBanner count={2} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shows "濒危" tag', () => {
    render(
      <EndangeredBanner count={2} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(screen.getByText('濒危')).toBeInTheDocument()
  })

  it('renders endangered cards list', () => {
    const cards = [
      { id: 1, name: '二分查找', algorithm_type: 'Search' },
      { id: 2, name: '快速排序', algorithm_type: 'Sorting' },
    ]
    render(
      <EndangeredBanner count={2} endangeredCards={cards} onCardClick={vi.fn()} />
    )
    expect(screen.getByText('二分查找')).toBeInTheDocument()
    expect(screen.getByText('快速排序')).toBeInTheDocument()
  })

  it('clicking a card calls onCardClick', async () => {
    const user = userEvent.setup()
    const mockClick = vi.fn()
    const cards = [
      { id: 1, name: '二分查找', algorithm_type: 'Search' },
    ]
    render(
      <EndangeredBanner count={1} endangeredCards={cards} onCardClick={mockClick} />
    )
    await user.click(screen.getByRole('button', { name: /二分查找/ }))
    expect(mockClick).toHaveBeenCalledWith(cards[0])
  })

  it('does not render card list when endangeredCards is empty', () => {
    render(
      <EndangeredBanner count={2} endangeredCards={[]} onCardClick={vi.fn()} />
    )
    expect(screen.queryByRole('button', { name: /去修炼/ })).not.toBeInTheDocument()
  })
})

describe('PendingRetakeSection', () => {
  beforeEach(() => {
    setupStoreMocks()
  })

  it('returns null when cards is undefined', () => {
    const { container } = render(<PendingRetakeSection cards={undefined} onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('returns null when cards is empty array', () => {
    const { container } = render(<PendingRetakeSection cards={[]} onCardClick={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('shows correct card count', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
      { id: 2, name: '快速排序', status: 'pending_retake', durability: 0, max_durability: 5, algorithm_type: 'Sorting' },
    ]
    render(<PendingRetakeSection cards={cards} onCardClick={vi.fn()} />)
    expect(screen.getByText(/待重修卡牌 \(2\)/)).toBeInTheDocument()
  })

  it('shows "待重修" tag', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
    ]
    render(<PendingRetakeSection cards={cards} onCardClick={vi.fn()} />)
    expect(screen.getByText('待重修')).toBeInTheDocument()
  })

  it('renders card names', () => {
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
      { id: 2, name: '快速排序', status: 'pending_retake', durability: 0, max_durability: 5, algorithm_type: 'Sorting' },
    ]
    render(<PendingRetakeSection cards={cards} onCardClick={vi.fn()} />)
    expect(screen.getByText('二分查找')).toBeInTheDocument()
    expect(screen.getByText('快速排序')).toBeInTheDocument()
  })

  it('toggles collapse on header click', async () => {
    const user = userEvent.setup()
    const cards = [
      { id: 1, name: '二分查找', status: 'pending_retake', durability: 1, max_durability: 5, algorithm_type: 'Search' },
    ]
    render(<PendingRetakeSection cards={cards} onCardClick={vi.fn()} />)
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
    render(<PendingRetakeSection cards={cards} onCardClick={vi.fn()} />)
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
    useCardStore.mockReturnValue({
      updateCard: mockUpdateCard,
      setSelectedCard: mockSetSelectedCard,
    })
    vi.mocked(cardService.updateCard).mockReset()
    vi.mocked(showToast).mockReset()
  })

  it('returns null when card is null', () => {
    const { container } = render(<CardEditForm card={null} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders name input with card name', () => {
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const nameInput = screen.getByPlaceholderText('卡牌名称')
    expect(nameInput).toHaveValue('二分查找')
  })

  it('renders algorithm_type input', () => {
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const typeInput = screen.getByPlaceholderText('如：Dynamic Programming')
    expect(typeInput).toHaveValue('Search')
  })

  it('renders 10 dimension textareas', () => {
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const placeholders = [
      '输入核心概念...', '输入关键要点...', '输入代码模板...', '输入时间复杂度...',
      '输入空间复杂度...', '输入典型题目...', '输入常见错误...', '输入优化思路...',
      '输入扩展知识...', '输入总结...',
    ]
    placeholders.forEach((ph) => {
      expect(screen.getByPlaceholderText(ph)).toBeInTheDocument()
    })
  })

  it('save button is disabled when no changes', () => {
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    expect(saveBtn).toBeDisabled()
  })

  it('save button becomes enabled after editing', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const nameInput = screen.getByPlaceholderText('卡牌名称')
    await user.clear(nameInput)
    await user.type(nameInput, '新名称')
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    expect(saveBtn).not.toBeDisabled()
  })

  it('clicking cancel calls onCancel', async () => {
    const user = userEvent.setup()
    const mockCancel = vi.fn()
    const card = makeCard()
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={mockCancel} />)
    const cancelBtn = screen.getByRole('button', { name: '取消' })
    await user.click(cancelBtn)
    expect(mockCancel).toHaveBeenCalled()
  })

  it('calls cardService.updateCard on save', async () => {
    const user = userEvent.setup()
    const card = makeCard()
    const updatedCard = { ...card, name: '新名称' }
    vi.mocked(cardService.updateCard).mockResolvedValue({ data: updatedCard })
    render(<CardEditForm card={card} onSave={vi.fn()} onCancel={vi.fn()} />)
    const nameInput = screen.getByPlaceholderText('卡牌名称')
    await user.clear(nameInput)
    await user.type(nameInput, '新名称')
    const saveBtn = screen.getByRole('button', { name: /保存/ })
    await user.click(saveBtn)
    expect(cardService.updateCard).toHaveBeenCalledWith(card.id, expect.objectContaining({ name: '新名称' }))
  })
})

describe('RetakeButton', () => {
  let mockNavigate
  let mockSetRetakeInfo

  beforeEach(() => {
    mockNavigate = vi.fn()
    mockSetRetakeInfo = vi.fn()
    useNavigate.mockReturnValue(mockNavigate)
    useCardStore.mockReturnValue({ setRetakeInfo: mockSetRetakeInfo })
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

  it('clicking button calls cardService.retakeCard', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    vi.mocked(cardService.retakeCard).mockResolvedValue({
      dialogue_id: 'd1',
      npc_id: 'npc1',
    })
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    expect(cardService.retakeCard).toHaveBeenCalledWith(card.id)
  })

  it('shows loading state during API call', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    let resolveApi
    vi.mocked(cardService.retakeCard).mockReturnValue(
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
    vi.mocked(cardService.retakeCard).mockResolvedValue({
      dialogue_id: 'd1',
      npc_id: 'npc1',
    })
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/npc/npc1?dialogueId=d1')
  })

  it('shows warning toast for error 40003', async () => {
    const user = userEvent.setup()
    const card = { id: 1, name: '二分查找', status: 'pending_retake' }
    vi.mocked(cardService.retakeCard).mockRejectedValue(
      new Error('40003 不是待重修状态')
    )
    render(<RetakeButton card={card} />)
    await user.click(screen.getByRole('button', { name: /重修/ }))
    expect(showToast).toHaveBeenCalledWith('该卡牌不在待重修状态', 'warning')
  })
})
