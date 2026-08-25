import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const { mockGetOverview, mockGetAlgorithmInfo, mockGetTodayTasks, mockGetDashboardStats, mockGetProgressStats, mockGetUpcomingTasks } = vi.hoisted(() => ({
  mockGetOverview: vi.fn(),
  mockGetAlgorithmInfo: vi.fn(),
  mockGetTodayTasks: vi.fn(),
  mockGetDashboardStats: vi.fn(),
  mockGetProgressStats: vi.fn(),
  mockGetUpcomingTasks: vi.fn(),
}))

vi.mock('../services/cardService', () => ({
  cardService: {
    getOverview: mockGetOverview,
    getAll: vi.fn(),
    getById: vi.fn(),
    getTodayTasks: mockGetTodayTasks,
    getDashboardStats: mockGetDashboardStats,
    getProgressStats: mockGetProgressStats,
    getUpcomingTasks: mockGetUpcomingTasks,
  },
}))

vi.mock('../services/api', () => ({
  default: {
    get: mockGetAlgorithmInfo,
  },
}))

vi.mock('../services/activityLogService', () => ({
  activityLogService: {
    getLogs: vi.fn().mockResolvedValue([]),
  },
}))

vi.mock('../components/ui/Loading/LoadingScreen', () => ({
  default: () => React.createElement('div', { 'data-testid': 'loading' }, 'Loading...'),
}))

import HallPage from '../pages/HallPage'
import { useHallStore } from '../stores/hallStore'

function renderHallPage() {
  return render(
    React.createElement(MemoryRouter, null,
      React.createElement(HallPage)
    )
  )
}

const mockTasks = {
  tasks: [
    { id: 1, name: 'LRU Cache 实现', type: 'problem', status: 'pending' },
    { id: 2, name: '快速幂算法模板', type: 'solution', status: 'in_progress' },
    { id: 3, name: '滑动窗口最大值', type: 'technique', status: 'done' },
    { id: 4, name: '二叉树 Morris 遍历', type: 'technique', status: 'pending' },
  ]
}

const mockDashboard = {
  due_count: 5,
  completed_count: 1,
  endangered_count: 2,
  weekly_progress: '5/7',
  total_review_count: 156,
  new_today: 0,
}

const mockProgress = {
  streak_days: 23,
  accuracy_rate: 87,
  learning_days: 23,
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
      overview: null,
      overviewLoading: false,
      todayStats: null,
      todayStatsLoading: false,
      cardGraph: null,
    })
    vi.clearAllMocks()

    mockGetOverview.mockResolvedValue({ total_cards: 47 })
    mockGetAlgorithmInfo.mockResolvedValue({ algorithm_types: [] })
    mockGetTodayTasks.mockResolvedValue(mockTasks)
    mockGetDashboardStats.mockResolvedValue(mockDashboard)
    mockGetProgressStats.mockResolvedValue(mockProgress)
    mockGetUpcomingTasks.mockResolvedValue({ days_until_next: 3 })
  })

  describe('页面加载流程', () => {
    it('应加载算法信息和概览数据', async () => {
      renderHallPage()

      await waitFor(() => {
        expect(mockGetOverview).toHaveBeenCalled()
      })
      expect(mockGetAlgorithmInfo).toHaveBeenCalled()
    })

    it('应渲染主要区块', async () => {
      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText(/system\.log/)).toBeInTheDocument()
      })
      expect(screen.getByText(/system\.status/)).toBeInTheDocument()
      expect(screen.getByText(/today\.tasks/)).toBeInTheDocument()
      expect(screen.getByText('总卡片')).toBeInTheDocument()
      expect(screen.getByText('待复习')).toBeInTheDocument()
    })
  })

  describe('状态面板显示', () => {
    it('应显示状态卡片', async () => {
      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('总卡片')).toBeInTheDocument()
      })
      expect(screen.getByText('濒危技巧')).toBeInTheDocument()
    })
  })

  describe('任务列表显示', () => {
    it('应显示任务列表', async () => {
      renderHallPage()

      await waitFor(() => {
        expect(screen.getByText('LRU Cache 实现')).toBeInTheDocument()
      })
      expect(screen.getByText('快速幂算法模板')).toBeInTheDocument()
    })
  })
})
