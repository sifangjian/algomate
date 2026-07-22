import { describe, it, expect, beforeEach, vi } from 'vitest'

const { mockGetAll, mockGetHallStats } = vi.hoisted(() => ({
  mockGetAll: vi.fn(),
  mockGetHallStats: vi.fn(),
}))

vi.mock('../services/npcService', () => ({
  npcService: {
    getAll: mockGetAll,
  },
}))

vi.mock('../services/statsService', () => ({
  statsService: {
    getHallStats: mockGetHallStats,
  },
}))

import { useHallStore } from '../stores/hallStore'

describe('hallStore', () => {
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

  describe('resetHall', () => {
    it('应重置所有状态', () => {
      useHallStore.setState({
        npcs: [{ id: 1, name: '基础数据结构' }],
        learningPath: [{ order: 1, npc_name: '基础数据结构' }],
        stats: { total_cards: 5 },
        algorithmInfo: { algorithm_types: [] },
        loading: false,
      })
      const { resetHall } = useHallStore.getState()
      resetHall()
      const state = useHallStore.getState()
      expect(state.npcs).toEqual([])
      expect(state.learningPath).toEqual([])
      expect(state.stats).toBeNull()
      expect(state.algorithmInfo).toBeNull()
      expect(state.loading).toBe(false)
    })
  })

  describe('fetchNpcs', () => {
    it('应成功获取 NPC 列表和学习路径', async () => {
      const mockData = {
        data: {
          npcs: [
            { id: 1, name: '基础数据结构', algorithm_type: 'basic_data_structure' },
            { id: 2, name: '搜索与基础', algorithm_type: 'stack_queue_search' },
          ],
          learning_path: [
            { order: 1, npc_name: '基础数据结构', stage: '基础入门' },
          ],
        },
      }
      mockGetAll.mockResolvedValue(mockData)

      const { fetchNpcs } = useHallStore.getState()
      await fetchNpcs()

      const state = useHallStore.getState()
      expect(state.npcs).toHaveLength(2)
      expect(state.npcs[0].name).toBe('基础数据结构')
      expect(state.learningPath).toHaveLength(1)
      expect(state.loading).toBe(false)
    })

    it('API 失败时应保持 loading=false', async () => {
      mockGetAll.mockRejectedValue(new Error('Network error'))

      const { fetchNpcs } = useHallStore.getState()
      await fetchNpcs()

      expect(useHallStore.getState().loading).toBe(false)
    })
  })

  describe('fetchStats', () => {
    it('应成功获取统计数据', async () => {
      const mockStats = {
        data: {
          total_cards: 5,
          endangered_cards: 1,
          pending_retake_cards: 0,
          cards_by_type: { basic_data_structure: 3 },
          is_new_user: false,
        },
      }
      mockGetHallStats.mockResolvedValue(mockStats)

      const { fetchStats } = useHallStore.getState()
      await fetchStats()

      const { stats } = useHallStore.getState()
      expect(stats.total_cards).toBe(5)
      expect(stats.is_new_user).toBe(false)
    })

    it('API 失败时应设置默认统计数据', async () => {
      mockGetHallStats.mockRejectedValue(new Error('Network error'))

      const { fetchStats } = useHallStore.getState()
      await fetchStats()

      const { stats } = useHallStore.getState()
      expect(stats.total_cards).toBe(0)
      expect(stats.is_new_user).toBe(false)
    })
  })
})