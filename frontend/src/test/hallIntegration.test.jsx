import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useNavigate } from 'react-router-dom'

const { mockGetAll, mockGetHallStats, mockGetAlgorithmInfo } = vi.hoisted(() => ({
  mockGetAll: vi.fn(),
  mockGetHallStats: vi.fn(),
  mockGetAlgorithmInfo: vi.fn(),
}))

vi.mock('../services/npcService', () => ({
  npcService: {
    getAll: mockGetAll,
    getAlgorithmInfo: mockGetAlgorithmInfo,
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

import HallPage from '../pages/HallPage'
import { useHallStore } from '../stores/hallStore'

const MOCK_NPCS = [
  { id: 1, name: '基础数据结构', title: '基础数据结构', algorithm_type: 'basic_data_structure', specialties: ['数组与双指针', '链表', '哈希表'], avatar: '📚', card_count: 0 },
  { id: 2, name: '搜索与基础', title: '搜索与基础', algorithm_type: 'stack_queue_search', specialties: ['栈与队列', '二分查找'], avatar: '🔍', card_count: 2 },
  { id: 3, name: '树结构', title: '树结构', algorithm_type: 'tree', specialties: ['二叉树遍历'], avatar: '🌳', card_count: 1 },
]

const MOCK_LEARNING_PATH = [
  { order: 1, npc_name: '基础数据结构', algorithm_type: 'basic_data_structure', stage: '基础入门', goal: '掌握基础数据结构' },
  { order: 2, npc_name: '搜索与基础', algorithm_type: 'stack_queue_search', stage: '搜索基础', goal: '掌握栈队列与搜索' },
]

const MOCK_STATS = {
  total_cards: 3,
  endangered_cards: 0,
  pending_retake_cards: 0,
  cards_by_type: { basic_data_structure: 0, stack_queue_search: 2, tree: 1 },
  is_new_user: false,
}

const MOCK_ALGORITHM_INFO = {
  algorithm_types: ['数组与双指针', '链表', '哈希表', '栈与队列', '二分查找', '前缀和', '二叉树遍历'],
  topic_importance: {
    '数组与双指针': 'core',
    '链表': 'core',
    '哈希表': 'core',
    '栈与队列': 'core',
    '二分查找': 'core',
    '前缀和': 'important',
    '二叉树遍历': 'core',
  },
  topic_prerequisites: {
    '二叉树遍历': ['栈与队列'],
  },
  topic_progress: {
    '数组与双指针': { card_count: 0, avg_durability: 0, learned: false },
    '链表': { card_count: 0, avg_durability: 0, learned: false },
    '哈希表': { card_count: 0, avg_durability: 0, learned: false },
    '栈与队列': { card_count: 2, avg_durability: 60, learned: true },
    '二分查找': { card_count: 0, avg_durability: 0, learned: false },
    '前缀和': { card_count: 0, avg_durability: 0, learned: false },
    '二叉树遍历': { card_count: 1, avg_durability: 40, learned: true },
  },
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
      learningPath: [],
      stats: null,
      algorithmInfo: null,
      loading: false,
    })
    vi.clearAllMocks()
  })

  describe('页面加载流程', () => {
    it('应加载算法地图和统计数据', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)

      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('数组与双指针')).toBeInTheDocument()
      })
      expect(screen.getByText('链表')).toBeInTheDocument()
      expect(mockGetAll).toHaveBeenCalled()
      expect(mockGetHallStats).toHaveBeenCalled()
      expect(mockGetAlgorithmInfo).toHaveBeenCalled()
    })

    it('应渲染SVG算法地图', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)

      const { container } = renderHallPage()

      await waitFor(() => {
        const svg = container.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })
  })

  describe('已学习节点标记', () => {
    it('已学习的主题应显示已学习标记', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)

      renderHallPage()

      await waitFor(() => {
        const learnedIndicators = screen.getAllByText('✓')
        expect(learnedIndicators.length).toBeGreaterThan(0)
      })
    })
  })
})
