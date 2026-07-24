import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useNavigate } from 'react-router-dom'

const { mockGetAll, mockGetHallStats, mockGetAlgorithmInfo, mockCardGetAll, mockGetGraph } = vi.hoisted(() => ({
  mockGetAll: vi.fn(),
  mockGetHallStats: vi.fn(),
  mockGetAlgorithmInfo: vi.fn(),
  mockCardGetAll: vi.fn(),
  mockGetGraph: vi.fn(),
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

vi.mock('../services/cardService', () => ({
  cardService: {
    getAll: mockCardGetAll,
    getGraph: mockGetGraph,
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
  learning_path: ['数组与双指针', '链表', '哈希表', '栈与队列', '二分查找', '前缀和', '二叉树遍历'],
  topic_importance: {},
  topic_prerequisites: {},
  topic_progress: {},
}

const MOCK_CARD_GRAPH = {
  nodes: [
    { id: 1, name: '数组与双指针', algorithm_type: '数组与双指针', durability: 0, review_level: 0, is_empty: false },
    { id: 2, name: '链表', algorithm_type: '链表', durability: 0, review_level: 0, is_empty: false },
    { id: 3, name: '哈希表', algorithm_type: '哈希表', durability: 0, review_level: 0, is_empty: false },
    { id: 4, name: '栈与队列', algorithm_type: '栈与队列', durability: 60, review_level: 1, is_empty: false },
    { id: 5, name: '二分查找', algorithm_type: '二分查找', durability: 0, review_level: 0, is_empty: false },
    { id: 6, name: '前缀和', algorithm_type: '前缀和', durability: 0, review_level: 0, is_empty: false },
    { id: 7, name: '二叉树遍历', algorithm_type: '二叉树遍历', durability: 40, review_level: 1, is_empty: false },
  ],
  edges: [
    { source: 4, target: 7, link_type: 'prerequisite', source_card_name: '栈与队列', target_card_name: '二叉树遍历' },
  ],
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
      selectedCard: null,
      cardGraph: null,
      emptyCards: [],
    })
    vi.clearAllMocks()
  })

  describe('页面加载流程', () => {
    it('应加载算法地图和统计数据', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)
      mockGetGraph.mockResolvedValue(MOCK_CARD_GRAPH)

      renderHallPage()

      await waitFor(() => {
        expect(screen.getAllByText('数组与双指针').length).toBeGreaterThan(0)
      })
      expect(screen.getAllByText('链表').length).toBeGreaterThan(0)
      expect(mockGetAll).toHaveBeenCalled()
      expect(mockGetHallStats).toHaveBeenCalled()
      expect(mockGetAlgorithmInfo).toHaveBeenCalled()
      expect(mockGetGraph).toHaveBeenCalled()
    })

    it('应渲染SVG算法地图', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)
      mockGetGraph.mockResolvedValue(MOCK_CARD_GRAPH)

      const { container } = renderHallPage()

      await waitFor(() => {
        const svg = container.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })
  })

  describe('节点点击行为', () => {
    it('点击节点应获取卡牌数据', async () => {
      mockGetAll.mockResolvedValue({ data: { npcs: MOCK_NPCS, learning_path: MOCK_LEARNING_PATH } })
      mockGetHallStats.mockResolvedValue({ data: MOCK_STATS })
      mockGetAlgorithmInfo.mockResolvedValue(MOCK_ALGORITHM_INFO)
      mockGetGraph.mockResolvedValue(MOCK_CARD_GRAPH)
      mockCardGetAll.mockResolvedValue([{ id: 1, name: '数组与双指针', algorithm_type: '数组与双指针' }])

      renderHallPage()

      await waitFor(() => {
        expect(screen.getAllByText('数组与双指针').length).toBeGreaterThan(0)
      })
      expect(mockCardGetAll).not.toHaveBeenCalled()
    })
  })
})
