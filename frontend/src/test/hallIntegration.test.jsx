import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const { mockGetAll, mockGetById, mockGetHallStats } = vi.hoisted(() => ({
  mockGetAll: vi.fn(),
  mockGetById: vi.fn(),
  mockGetHallStats: vi.fn(),
}))

vi.mock('../services/npcService', () => ({
  npcService: {
    getAll: mockGetAll,
    getById: mockGetById,
  },
}))

vi.mock('../services/statsService', () => ({
  statsService: {
    getHallStats: mockGetHallStats,
  },
}))

vi.mock('../components/ui/Loading/LoadingScreen', () => ({
  default: () => React.createElement('div', { 'data-testid': 'loading' }, 'Loading...'),
}))

vi.mock('../components/ui/Modal/Modal', () => ({
  default: ({ open, children, title }) => open ? React.createElement('div', { 'data-testid': 'modal' }, children) : null,
}))

vi.mock('../components/ui/Button/Button', () => ({
  default: ({ children, onClick, loading, fullWidth }) =>
    React.createElement('button', { onClick, disabled: loading, 'data-testid': 'button' }, children),
}))

vi.mock('../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

vi.mock('../components/hall/NpcDetailModal', () => ({
  __esModule: true,
  default: () => React.createElement('div', { 'data-testid': 'npc-detail-modal' }, 'NpcDetailModal'),
}))

import HallPage from '../pages/HallPage'
import { useHallStore } from '../stores/hallStore'

const MOCK_NPCS = [
  { id: 1, name: '老夫子', title: '基础数据结构导师', algorithm_type: 'basic_data_structure', specialties: ['数组与双指针', '链表', '哈希表'], avatar: 'laofuzi', card_count: 0 },
  { id: 2, name: '栈语者', title: '栈队列与搜索导师', algorithm_type: 'stack_queue_search', specialties: ['栈与队列', '二分查找'], avatar: 'zhanzhe', card_count: 2 },
  { id: 3, name: '树语者', title: '树结构导师', algorithm_type: 'tree', specialties: ['二叉树遍历'], avatar: 'shuzhe', card_count: 1 },
]

const MOCK_LEARNING_PATH = [
  { order: 1, npc_name: '老夫子', algorithm_type: 'basic_data_structure', stage: '基础入门', goal: '掌握基础数据结构' },
  { order: 2, npc_name: '栈语者', algorithm_type: 'stack_queue_search', stage: '搜索基础', goal: '掌握栈队列与搜索' },
]

const MOCK_STATS = {
  total_cards: 3,
  endangered_cards: 0,
  pending_retake_cards: 0,
  cards_by_type: { basic_data_structure: 0, stack_queue_search: 2, tree: 1 },
  is_new_user: false,
}

const MOCK_NPC_DETAIL = {
  id: 1,
  name: '老夫子',
  title: '基础数据结构导师',
  algorithm_type: 'basic_data_structure',
  specialties: ['数组与双指针', '链表', '哈希表'],
  avatar: 'laofuzi',
  description: '基础数据结构的导师',
  topics: [
    { name: '数组与双指针', has_card: false },
    { name: '链表', has_card: true },
    { name: '哈希表', has_card: false },
  ],
  card_count: 1,
}

function renderHallPage() {
  return render(
    React.createElement(MemoryRouter, null,
      React.createElement(HallPage)
    )
  )
}

describe('HallPage 集成测试', () => {
  beforeEach(() => {
    useHallStore.setState({
      npcs: [],
      selectedNpc: null,
      learningPath: [],
      stats: null,
      filters: { algorithm_type: '', keyword: '' },
      loading: false,
      modalOpen: false,
    })
    vi.clearAllMocks()
  })

  describe('页面加载流程', () => {
    it('应加载 NPC 列表和统计数据', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('老夫子')).toBeInTheDocument()
      })
      expect(screen.getByText('栈语者')).toBeInTheDocument()
      expect(screen.getByText('树语者')).toBeInTheDocument()
      expect(mockGetAll).toHaveBeenCalled()
      expect(mockGetHallStats).toHaveBeenCalled()
    })

    it('应显示学习路径卡片', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('推荐学习路径')).toBeInTheDocument()
      })
    })

    it('应显示有卡牌的 NPC 的卡牌数量', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('已获2张卡牌')).toBeInTheDocument()
      })
    })
  })

  describe('NPC 详情交互流程', () => {
    it('点击 NPC 卡片应设置选中 NPC', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('老夫子')).toBeInTheDocument()
      })

      await userEvent.click(screen.getByText('老夫子'))

      await waitFor(() => {
        const { selectedNpc, modalOpen } = useHallStore.getState()
        expect(selectedNpc).not.toBeNull()
        expect(selectedNpc.name).toBe('老夫子')
        expect(modalOpen).toBe(true)
      })
    })
  })

  describe('筛选交互流程', () => {
    it('选择算法类型应触发新的 API 请求', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('老夫子')).toBeInTheDocument()
      })

      const treeTag = screen.getByText('树结构')
      await userEvent.click(treeTag)

      expect(useHallStore.getState().filters.algorithm_type).toBe('tree')
    })
  })

  describe('新用户体验流程', () => {
    it('新用户应看到老夫子的推荐提示', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: { ...MOCK_STATS, is_new_user: true } })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('推荐新手从这里开始')).toBeInTheDocument()
      })
    })
  })

  describe('学习路径交互流程', () => {
    it('展开学习路径应显示步骤详情', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('推荐学习路径')).toBeInTheDocument()
      })

      await userEvent.click(screen.getByText('推荐学习路径'))

      await waitFor(() => {
        expect(screen.getByText('基础入门')).toBeInTheDocument()
        expect(screen.getByText('掌握基础数据结构')).toBeInTheDocument()
      })
    })
  })
})
