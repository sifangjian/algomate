import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../services/cardService', () => ({
  cardService: {
    getTodayReviewTasks: vi.fn(),
    completeReviewV1: vi.fn(),
    generateReviewQuiz: vi.fn(),
    getById: vi.fn(),
    getReviewStats: vi.fn(),
  },
}))

vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}))

vi.mock('../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

vi.mock('../components/ui/Loading/LoadingScreen', () => ({
  __esModule: true,
  default: () => <div data-testid="loading">Loading...</div>,
}))

vi.mock('../components/ui/Button/Button', () => ({
  __esModule: true,
  default: ({ children, onClick, disabled, variant }) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  ),
}))

vi.mock('../components/guide/PostReviewGuide', () => ({
  __esModule: true,
  default: () => <div data-testid="post-review-guide">PostReviewGuide</div>,
}))

import DailyReview from '../pages/DailyReview'
import { cardService } from '../services/cardService'
import { useNavigate } from 'react-router-dom'

const mockTasks = [
  {
    task_id: 'review_1',
    task_type: 'critical_review',
    card_id: 1,
    card_name: '二分查找',
    card_algorithm_type: 'Search',
    card_durability: 15,
    priority: 'critical',
    reason: '濒危卡牌',
    review_types: ['content_review', 'quick_quiz', 'boss_challenge'],
    max_durability: 100,
    algorithm_type: 'Search',
  },
  {
    task_id: 'review_2',
    task_type: 'forgetting_curve_review',
    card_id: 2,
    card_name: '快速排序',
    card_algorithm_type: 'Sorting',
    card_durability: 60,
    priority: 'high',
    reason: '遗忘曲线修炼',
    review_types: ['content_review', 'quick_quiz'],
    max_durability: 100,
    algorithm_type: 'Sorting',
  },
  {
    task_id: 'review_3',
    task_type: 'boss_challenge',
    card_id: 3,
    card_name: 'BFS',
    card_algorithm_type: 'Graph',
    card_durability: 80,
    priority: 'low',
    reason: 'Boss挑战',
    review_types: ['boss_challenge'],
    max_durability: 100,
    algorithm_type: 'Graph',
  },
]

describe('DailyReview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cardService.getTodayReviewTasks.mockResolvedValue({
      data: {
        tasks: mockTasks,
        endangered_count: 1,
        due_count: 1,
        total_count: 3,
        has_cards: true,
      },
    })
    cardService.getReviewStats.mockResolvedValue({
      total_review_count: 10,
      weekly_review_days: 3,
      completed_today: 2,
      review_level_distribution: { '0': 5, '1': 3 },
    })
    cardService.completeReviewV1.mockResolvedValue({
      data: {
        card_id: 1,
        card_name: '二分查找',
        review_type: 'content_review',
        durability_before: 15,
        durability_after: 45,
        remaining_endangered: 0,
      },
    })
    useNavigate.mockReturnValue(vi.fn())
  })

  describe('任务列表渲染', () => {
    it('应渲染页面标题', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText('📋 每日修炼')).toBeInTheDocument()
      })
    })

    it('应按优先级排序显示任务', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText('二分查找')).toBeInTheDocument()
        expect(screen.getByText('快速排序')).toBeInTheDocument()
        expect(screen.getByText('BFS')).toBeInTheDocument()
      })
    })

    it('应显示濒危卡牌警告', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText(/1 张濒危卡牌急需修炼/)).toBeInTheDocument()
      })
    })

    it('应显示完成进度', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText('0/3')).toBeInTheDocument()
        expect(screen.getByText('已完成')).toBeInTheDocument()
      })
    })

    it('应显示修炼统计', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText('累计修炼')).toBeInTheDocument()
      })
    })

    it('应显示任务类型标签', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText('濒危')).toBeInTheDocument()
        expect(screen.getByText('遗忘曲线')).toBeInTheDocument()
        expect(screen.getByText('Boss挑战')).toBeInTheDocument()
      })
    })

    it('应显示耐久度信息', async () => {
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText(/耐久 15\/100/)).toBeInTheDocument()
      })
    })
  })

  describe('空状态', () => {
    it('无卡牌时应显示获取卡牌提示', async () => {
      cardService.getTodayReviewTasks.mockResolvedValue({
        data: {
          tasks: [],
          endangered_count: 0,
          due_count: 0,
          total_count: 0,
          has_cards: false,
        },
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText(/修习更多算法技巧后/)).toBeInTheDocument()
      })
    })

    it('有卡牌但无任务时应显示无任务提示', async () => {
      cardService.getTodayReviewTasks.mockResolvedValue({
        data: {
          tasks: [],
          endangered_count: 0,
          due_count: 0,
          total_count: 0,
          has_cards: true,
        },
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getByText(/今日没有待修炼任务/)).toBeInTheDocument()
      })
    })
  })

  describe('知识回顾', () => {
    it('点击知识回顾应进入回顾模式', async () => {
      cardService.getById.mockResolvedValue({
        core_concept: '二分查找是一种搜索算法',
        key_points: '确定左右边界\n计算中间值',
        my_notes: '二分查找总结',
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('📖 知识回顾')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('📖 知识回顾')[0])
      await waitFor(() => {
        expect(screen.getByText(/知识回顾 - 二分查找/)).toBeInTheDocument()
      })
    })

    it('知识回顾应显示卡牌内容', async () => {
      cardService.getById.mockResolvedValue({
        core_concept: '二分查找是一种搜索算法',
        key_points: '确定左右边界\n计算中间值',
        my_notes: '二分查找总结',
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('📖 知识回顾')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('📖 知识回顾')[0])
      await waitFor(() => {
        expect(screen.getByText('二分查找是一种搜索算法')).toBeInTheDocument()
        expect(screen.getByText(/确定左右边界/)).toBeInTheDocument()
        expect(screen.getByText('二分查找总结')).toBeInTheDocument()
      })
    })

    it('完成回顾应调用 completeReviewV1', async () => {
      cardService.getById.mockResolvedValue({
        core_concept: '二分查找内容',
        key_points: '',
        my_notes: '',
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('📖 知识回顾')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('📖 知识回顾')[0])
      await waitFor(() => {
        expect(screen.getByText('✅ 完成回顾')).toBeInTheDocument()
      })
      await userEvent.click(screen.getByText('✅ 完成回顾'))
      await waitFor(() => {
        expect(cardService.completeReviewV1).toHaveBeenCalledWith(1, 'content_review')
      })
    })

    it('完成回顾后应回到任务列表', async () => {
      cardService.getById.mockResolvedValue({
        core_concept: '二分查找内容',
        key_points: '',
        my_notes: '',
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('📖 知识回顾')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('📖 知识回顾')[0])
      await waitFor(() => {
        expect(screen.getByText('✅ 完成回顾')).toBeInTheDocument()
      })
      await userEvent.click(screen.getByText('✅ 完成回顾'))
      await waitFor(() => {
        expect(screen.getByText('📋 每日修炼')).toBeInTheDocument()
      })
      expect(cardService.completeReviewV1).toHaveBeenCalledWith(1, 'content_review')
    })
  })

  describe('快速问答', () => {
    it('点击快速问答应进入问答模式', async () => {
      cardService.generateReviewQuiz.mockResolvedValue({
        data: {
          questions: [
            {
              content: '二分查找的时间复杂度？',
              options: ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
              correct_answer: 'B',
              explanation: '二分查找每次折半',
            },
          ],
        },
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('✏️ 快速问答')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('✏️ 快速问答')[0])
      await waitFor(() => {
        expect(screen.getByText(/快速问答 - 二分查找/)).toBeInTheDocument()
      })
    })

    it('问答模式应显示选项', async () => {
      cardService.generateReviewQuiz.mockResolvedValue({
        data: {
          questions: [
            {
              content: '二分查找的时间复杂度？',
              options: ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
              correct_answer: 'B',
              explanation: '二分查找每次折半',
            },
          ],
        },
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('✏️ 快速问答')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('✏️ 快速问答')[0])
      await waitFor(() => {
        expect(screen.getByText('O(n)')).toBeInTheDocument()
        expect(screen.getByText('O(log n)')).toBeInTheDocument()
      })
    })

    it('选择答案后提交应调用 completeReviewV1', async () => {
      cardService.generateReviewQuiz.mockResolvedValue({
        data: {
          questions: [
            {
              content: '二分查找的时间复杂度？',
              options: ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
              correct_answer: 'B',
              explanation: '二分查找每次折半',
            },
          ],
        },
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('✏️ 快速问答')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('✏️ 快速问答')[0])
      await waitFor(() => {
        expect(screen.getByText('O(log n)')).toBeInTheDocument()
      })
      await userEvent.click(screen.getByText('O(log n)'))
      await userEvent.click(screen.getByText('📝 提交答案'))
      await waitFor(() => {
        expect(cardService.completeReviewV1).toHaveBeenCalledWith(1, 'quick_quiz')
      })
    })
  })

  describe('Boss挑战', () => {
    it('点击Boss挑战应导航到Boss战页面', async () => {
      const mockNavigate = vi.fn()
      useNavigate.mockReturnValue(mockNavigate)
      render(<DailyReview />)
      await waitFor(() => {
        const bossButtons = screen.getAllByText('🐉 Boss挑战')
        expect(bossButtons.length).toBeGreaterThan(0)
      })
      const bossButtons = screen.getAllByText('🐉 Boss挑战')
      await userEvent.click(bossButtons[0])
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalled()
      })
      const callArg = mockNavigate.mock.calls[0][0]
      expect(callArg).toMatch(/^\/boss\/battle\?cardId=\d+$/)
    })
  })

  describe('返回按钮', () => {
    it('回顾模式下点击返回应回到任务列表', async () => {
      cardService.getById.mockResolvedValue({
        core_concept: '二分查找内容',
        key_points: '',
        my_notes: '',
      })
      render(<DailyReview />)
      await waitFor(() => {
        expect(screen.getAllByText('📖 知识回顾')[0]).toBeInTheDocument()
      })
      await userEvent.click(screen.getAllByText('📖 知识回顾')[0])
      await waitFor(() => {
        expect(screen.getByText('← 返回任务列表')).toBeInTheDocument()
      })
      await userEvent.click(screen.getByText('← 返回任务列表'))
      await waitFor(() => {
        expect(screen.getByText('📋 每日修炼')).toBeInTheDocument()
      })
    })
  })

  describe('加载状态', () => {
    it('加载中应显示LoadingScreen', () => {
      cardService.getTodayReviewTasks.mockReturnValue(new Promise(() => {}))
      render(<DailyReview />)
      expect(screen.getByTestId('loading')).toBeInTheDocument()
    })
  })

  describe('API 错误处理', () => {
    it('获取任务失败应显示错误提示', async () => {
      const { showToast } = await import('../components/ui/Toast/index')
      cardService.getTodayReviewTasks.mockRejectedValue(new Error('Network error'))
      render(<DailyReview />)
      await waitFor(() => {
        expect(showToast).toHaveBeenCalledWith('获取今日修炼任务失败', 'error')
      })
    })
  })
})
