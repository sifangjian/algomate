import { describe, it, expect, beforeEach, vi } from 'vitest'

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

import { useHallStore } from '../stores/hallStore'

describe('hallStore', () => {
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

  describe('setFilters', () => {
    it('应更新部分筛选条件', () => {
      const { setFilters } = useHallStore.getState()
      setFilters({ algorithm_type: 'tree' })
      const { filters } = useHallStore.getState()
      expect(filters.algorithm_type).toBe('tree')
      expect(filters.keyword).toBe('')
    })

    it('应保留未修改的筛选条件', () => {
      const { setFilters } = useHallStore.getState()
      setFilters({ keyword: '动态规划' })
      setFilters({ algorithm_type: 'greedy' })
      const { filters } = useHallStore.getState()
      expect(filters.keyword).toBe('动态规划')
      expect(filters.algorithm_type).toBe('greedy')
    })
  })

  describe('resetFilters', () => {
    it('应重置所有筛选条件', () => {
      const { setFilters, resetFilters } = useHallStore.getState()
      setFilters({ algorithm_type: 'tree', keyword: '搜索' })
      resetFilters()
      const { filters } = useHallStore.getState()
      expect(filters.algorithm_type).toBe('')
      expect(filters.keyword).toBe('')
    })
  })

  describe('setSelectedNpc', () => {
    it('应设置选中的 NPC 并打开弹窗', () => {
      const npc = { id: 1, name: '老夫子' }
      const { setSelectedNpc } = useHallStore.getState()
      setSelectedNpc(npc)
      const { selectedNpc, modalOpen } = useHallStore.getState()
      expect(selectedNpc).toEqual(npc)
      expect(modalOpen).toBe(true)
    })

    it('传入 null 应关闭弹窗', () => {
      const { setSelectedNpc } = useHallStore.getState()
      setSelectedNpc({ id: 1, name: '老夫子' })
      setSelectedNpc(null)
      const { selectedNpc, modalOpen } = useHallStore.getState()
      expect(selectedNpc).toBeNull()
      expect(modalOpen).toBe(false)
    })
  })

  describe('setModalOpen', () => {
    it('应设置弹窗状态', () => {
      const { setModalOpen } = useHallStore.getState()
      setModalOpen(true)
      expect(useHallStore.getState().modalOpen).toBe(true)
      setModalOpen(false)
      expect(useHallStore.getState().modalOpen).toBe(false)
    })
  })

  describe('resetHall', () => {
    it('应重置所有状态', () => {
      const { setFilters, setSelectedNpc, resetHall } = useHallStore.getState()
      setFilters({ algorithm_type: 'tree' })
      setSelectedNpc({ id: 1, name: '老夫子' })
      resetHall()
      const state = useHallStore.getState()
      expect(state.npcs).toEqual([])
      expect(state.selectedNpc).toBeNull()
      expect(state.learningPath).toEqual([])
      expect(state.stats).toBeNull()
      expect(state.filters).toEqual({ algorithm_type: '', keyword: '' })
      expect(state.loading).toBe(false)
      expect(state.modalOpen).toBe(false)
    })
  })

  describe('fetchNpcs', () => {
    it('应成功获取 NPC 列表和学习路径', async () => {
      const mockData = {
        npcs: [
          { id: 1, name: '老夫子', algorithm_type: 'basic_data_structure' },
          { id: 2, name: '栈语者', algorithm_type: 'stack_queue_search' },
        ],
        learning_path: [
          { order: 1, npc_name: '老夫子', stage: '基础入门' },
        ],
      }
      mockGetAll.mockResolvedValue(mockData)

      const { fetchNpcs } = useHallStore.getState()
      await fetchNpcs()

      const state = useHallStore.getState()
      expect(state.npcs).toHaveLength(2)
      expect(state.npcs[0].name).toBe('老夫子')
      expect(state.learningPath).toHaveLength(1)
      expect(state.loading).toBe(false)
    })

    it('应传递筛选参数给 API', async () => {
      mockGetAll.mockResolvedValue({ npcs: [], learning_path: [] })
      useHallStore.setState({ filters: { algorithm_type: 'tree', keyword: '树' } })

      const { fetchNpcs } = useHallStore.getState()
      await fetchNpcs()

      expect(mockGetAll).toHaveBeenCalledWith({
        algorithm_type: 'tree',
        keyword: '树',
      })
    })

    it('API 失败时应保持 loading=false', async () => {
      mockGetAll.mockRejectedValue(new Error('Network error'))

      const { fetchNpcs } = useHallStore.getState()
      await fetchNpcs()

      expect(useHallStore.getState().loading).toBe(false)
    })
  })

  describe('fetchNpcDetail', () => {
    it('应成功获取 NPC 详情', async () => {
      const mockDetail = {
        id: 1,
        name: '老夫子',
        title: '基础数据结构导师',
        specialties: ['数组与双指针', '链表', '哈希表'],
        card_count: 2,
      }
      mockGetById.mockResolvedValue(mockDetail)

      const { fetchNpcDetail } = useHallStore.getState()
      await fetchNpcDetail(1)

      const { selectedNpc } = useHallStore.getState()
      expect(selectedNpc.name).toBe('老夫子')
      expect(selectedNpc.card_count).toBe(2)
    })
  })

  describe('fetchStats', () => {
    it('应成功获取统计数据', async () => {
      const mockStats = {
        total_cards: 5,
        endangered_cards: 1,
        pending_retake_cards: 0,
        cards_by_type: { basic_data_structure: 3 },
        is_new_user: false,
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
