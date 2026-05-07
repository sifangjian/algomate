import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

const { mockGetBosses, mockGetBossDetail, mockChallenge, mockSubmit } = vi.hoisted(() => ({
  mockGetBosses: vi.fn(),
  mockGetBossDetail: vi.fn(),
  mockChallenge: vi.fn(),
  mockSubmit: vi.fn(),
}))

vi.mock('../../services/bossService', () => ({
  bossService: {
    getBosses: mockGetBosses,
    getBossDetail: mockGetBossDetail,
    challenge: mockChallenge,
    submit: mockSubmit,
  },
}))

import { useBossStore } from '../../stores/bossStore'

const INITIAL_STATE = {
  bosses: [],
  selectedBoss: null,
  hasAnyCard: false,
  weaknessCards: [],
  otherCards: [],
  hasWeaknessCard: false,
  battlePhase: 'idle',
  battleState: null,
  currentQuestion: null,
  selectedCardId: null,
  battleResult: null,
  loading: false,
  error: null,
}

describe('bossStore', () => {
  beforeEach(() => {
    useBossStore.setState(INITIAL_STATE)
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应包含所有默认值', () => {
      const state = useBossStore.getState()
      expect(state.bosses).toEqual([])
      expect(state.selectedBoss).toBeNull()
      expect(state.hasAnyCard).toBe(false)
      expect(state.weaknessCards).toEqual([])
      expect(state.otherCards).toEqual([])
      expect(state.hasWeaknessCard).toBe(false)
      expect(state.battlePhase).toBe('idle')
      expect(state.battleState).toBeNull()
      expect(state.currentQuestion).toBeNull()
      expect(state.selectedCardId).toBeNull()
      expect(state.battleResult).toBeNull()
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })
  })

  describe('setSelectedCardId', () => {
    it('应设置选中的卡牌 ID', () => {
      const { setSelectedCardId } = useBossStore.getState()
      setSelectedCardId(42)
      expect(useBossStore.getState().selectedCardId).toBe(42)
    })

    it('应能重置选中卡牌 ID 为 null', () => {
      useBossStore.setState({ selectedCardId: 42 })
      const { setSelectedCardId } = useBossStore.getState()
      setSelectedCardId(null)
      expect(useBossStore.getState().selectedCardId).toBeNull()
    })
  })

  describe('setBattlePhase', () => {
    it('应切换战斗阶段到指定值', () => {
      const { setBattlePhase } = useBossStore.getState()
      setBattlePhase('selecting_card')
      expect(useBossStore.getState().battlePhase).toBe('selecting_card')
    })

    it('应能切换到 answering 阶段', () => {
      const { setBattlePhase } = useBossStore.getState()
      setBattlePhase('answering')
      expect(useBossStore.getState().battlePhase).toBe('answering')
    })

    it('应能切换到 result 阶段', () => {
      const { setBattlePhase } = useBossStore.getState()
      setBattlePhase('result')
      expect(useBossStore.getState().battlePhase).toBe('result')
    })
  })

  describe('resetBattle', () => {
    it('应重置战斗相关状态并回到 selecting_card 阶段', () => {
      useBossStore.setState({
        currentQuestion: { id: 1 },
        selectedCardId: 10,
        battleResult: { result: 'win' },
        battlePhase: 'result',
        error: 'some error',
      })

      const { resetBattle } = useBossStore.getState()
      resetBattle()

      const state = useBossStore.getState()
      expect(state.currentQuestion).toBeNull()
      expect(state.selectedCardId).toBeNull()
      expect(state.battleResult).toBeNull()
      expect(state.battlePhase).toBe('selecting_card')
      expect(state.error).toBeNull()
    })

    it('不应重置 selectedBoss 和卡牌信息', () => {
      const boss = { id: 1, name: 'Boss1' }
      useBossStore.setState({
        selectedBoss: boss,
        hasAnyCard: true,
        weaknessCards: [{ id: 1 }],
        otherCards: [{ id: 2 }],
        hasWeaknessCard: true,
      })

      const { resetBattle } = useBossStore.getState()
      resetBattle()

      const state = useBossStore.getState()
      expect(state.selectedBoss).toEqual(boss)
      expect(state.hasAnyCard).toBe(true)
      expect(state.weaknessCards).toEqual([{ id: 1 }])
      expect(state.otherCards).toEqual([{ id: 2 }])
      expect(state.hasWeaknessCard).toBe(true)
    })
  })

  describe('resetBoss', () => {
    it('应重置所有 Boss 选择和战斗状态', () => {
      useBossStore.setState({
        selectedBoss: { id: 1, name: 'Boss1' },
        hasAnyCard: true,
        weaknessCards: [{ id: 1 }],
        otherCards: [{ id: 2 }],
        hasWeaknessCard: true,
        currentQuestion: { id: 1 },
        selectedCardId: 10,
        battleResult: { result: 'win' },
        battlePhase: 'result',
        battleState: { some: 'state' },
        error: 'some error',
      })

      const { resetBoss } = useBossStore.getState()
      resetBoss()

      const state = useBossStore.getState()
      expect(state.selectedBoss).toBeNull()
      expect(state.hasAnyCard).toBe(false)
      expect(state.weaknessCards).toEqual([])
      expect(state.otherCards).toEqual([])
      expect(state.hasWeaknessCard).toBe(false)
      expect(state.currentQuestion).toBeNull()
      expect(state.selectedCardId).toBeNull()
      expect(state.battleResult).toBeNull()
      expect(state.battlePhase).toBe('idle')
      expect(state.battleState).toBeNull()
      expect(state.error).toBeNull()
    })

    it('不应清除 bosses 列表', () => {
      useBossStore.setState({
        bosses: [{ id: 1 }, { id: 2 }],
      })

      const { resetBoss } = useBossStore.getState()
      resetBoss()

      expect(useBossStore.getState().bosses).toEqual([{ id: 1 }, { id: 2 }])
    })
  })

  describe('saveBattleToLocalStorage', () => {
    it('battlePhase 非 idle 时应保存战斗状态到 localStorage', () => {
      const boss = { id: 1, name: 'Boss1' }
      const question = { id: 10, type: 'choice' }
      useBossStore.setState({
        selectedBoss: boss,
        selectedCardId: 5,
        currentQuestion: question,
        battlePhase: 'answering',
      })

      const { saveBattleToLocalStorage } = useBossStore.getState()
      saveBattleToLocalStorage()

      const saved = JSON.parse(localStorage.getItem('boss_battle_state'))
      expect(saved).toMatchObject({
        selectedBoss: boss,
        selectedCardId: 5,
        currentQuestion: question,
        battlePhase: 'answering',
      })
    })

    it('battlePhase 为 idle 时不应保存到 localStorage', () => {
      useBossStore.setState({
        selectedBoss: { id: 1 },
        battlePhase: 'idle',
      })

      const { saveBattleToLocalStorage } = useBossStore.getState()
      saveBattleToLocalStorage()

      expect(localStorage.getItem('boss_battle_state')).toBeNull()
    })
  })

  describe('restoreBattleFromLocalStorage', () => {
    it('应从 localStorage 恢复战斗状态并返回 true', () => {
      const savedState = {
        selectedBoss: { id: 1, name: 'Boss1' },
        selectedCardId: 5,
        currentQuestion: { id: 10 },
        battlePhase: 'answering',
      }
      localStorage.setItem('boss_battle_state', JSON.stringify(savedState))

      const { restoreBattleFromLocalStorage } = useBossStore.getState()
      const result = restoreBattleFromLocalStorage()

      expect(result).toBe(true)
      const state = useBossStore.getState()
      expect(state.selectedBoss).toEqual(savedState.selectedBoss)
      expect(state.selectedCardId).toBe(5)
      expect(state.currentQuestion).toEqual(savedState.currentQuestion)
      expect(state.battlePhase).toBe('answering')
      expect(state.battleState).toEqual(savedState)
    })

    it('localStorage 为空时应返回 false', () => {
      const { restoreBattleFromLocalStorage } = useBossStore.getState()
      const result = restoreBattleFromLocalStorage()
      expect(result).toBe(false)
    })

    it('localStorage 数据损坏时应返回 false 且不抛出异常', () => {
      localStorage.setItem('boss_battle_state', 'invalid-json{{{')

      const { restoreBattleFromLocalStorage } = useBossStore.getState()
      const result = restoreBattleFromLocalStorage()

      expect(result).toBe(false)
    })
  })

  describe('clearBattleLocalStorage', () => {
    it('应清除 localStorage 中的战斗状态', () => {
      localStorage.setItem('boss_battle_state', JSON.stringify({ battlePhase: 'answering' }))
      useBossStore.setState({ battleState: { battlePhase: 'answering' } })

      const { clearBattleLocalStorage } = useBossStore.getState()
      clearBattleLocalStorage()

      expect(localStorage.getItem('boss_battle_state')).toBeNull()
      expect(useBossStore.getState().battleState).toBeNull()
    })
  })

  describe('fetchBosses', () => {
    it('应成功获取 Boss 列表并更新状态', async () => {
      const mockBosses = [
        { id: 1, name: 'Boss1', difficulty: 'easy' },
        { id: 2, name: 'Boss2', difficulty: 'hard' },
      ]
      mockGetBosses.mockResolvedValue({ bosses: mockBosses })

      const { fetchBosses } = useBossStore.getState()
      await fetchBosses()

      const state = useBossStore.getState()
      expect(state.bosses).toHaveLength(2)
      expect(state.bosses[0]).toMatchObject({ id: 1, name: 'Boss1' })
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('应传递参数给 bossService.getBosses', async () => {
      mockGetBosses.mockResolvedValue({ bosses: [] })

      const { fetchBosses } = useBossStore.getState()
      await fetchBosses({ difficulty: 'hard' })

      expect(mockGetBosses).toHaveBeenCalledWith({ difficulty: 'hard' })
    })

    it('API 返回无 bosses 字段时应设为空数组', async () => {
      mockGetBosses.mockResolvedValue({})

      const { fetchBosses } = useBossStore.getState()
      await fetchBosses()

      expect(useBossStore.getState().bosses).toEqual([])
    })

    it('API 失败时应设置 error 且 loading 为 false', async () => {
      mockGetBosses.mockRejectedValue(new Error('Network error'))

      const { fetchBosses } = useBossStore.getState()
      await fetchBosses()

      const state = useBossStore.getState()
      expect(state.error).toBe('Network error')
      expect(state.loading).toBe(false)
    })

    it('请求过程中 loading 应为 true', async () => {
      let resolvePromise
      mockGetBosses.mockReturnValue(new Promise((resolve) => {
        resolvePromise = resolve
      }))

      const { fetchBosses } = useBossStore.getState()
      const promise = fetchBosses()

      expect(useBossStore.getState().loading).toBe(true)

      resolvePromise({ bosses: [] })
      await promise

      expect(useBossStore.getState().loading).toBe(false)
    })
  })

  describe('selectBoss', () => {
    it('应设置 selectedBoss 并获取 Boss 详情', async () => {
      const boss = { id: 1, name: 'Boss1' }
      const detail = {
        has_any_card: true,
        weakness_cards: [{ id: 10, name: 'Card1' }],
        other_cards: [{ id: 20, name: 'Card2' }],
        has_weakness_card: true,
      }
      mockGetBossDetail.mockResolvedValue(detail)

      const { selectBoss } = useBossStore.getState()
      await selectBoss(boss)

      const state = useBossStore.getState()
      expect(state.selectedBoss).toEqual(boss)
      expect(state.hasAnyCard).toBe(true)
      expect(state.weaknessCards).toEqual([{ id: 10, name: 'Card1' }])
      expect(state.otherCards).toEqual([{ id: 20, name: 'Card2' }])
      expect(state.hasWeaknessCard).toBe(true)
      expect(state.battlePhase).toBe('selecting_card')
      expect(state.selectedCardId).toBeNull()
      expect(state.loading).toBe(false)
    })

    it('应调用 bossService.getBossDetail 并传入 boss.id', async () => {
      mockGetBossDetail.mockResolvedValue({})

      const { selectBoss } = useBossStore.getState()
      await selectBoss({ id: 42, name: 'Boss42' })

      expect(mockGetBossDetail).toHaveBeenCalledWith(42)
    })

    it('API 失败时应设置 error', async () => {
      mockGetBossDetail.mockRejectedValue(new Error('Server error'))

      const { selectBoss } = useBossStore.getState()
      await selectBoss({ id: 1 })

      const state = useBossStore.getState()
      expect(state.error).toBe('Server error')
      expect(state.loading).toBe(false)
    })

    it('应清除之前的 currentQuestion 和 battleResult', async () => {
      useBossStore.setState({
        currentQuestion: { id: 99 },
        battleResult: { result: 'win' },
      })
      mockGetBossDetail.mockResolvedValue({})

      const { selectBoss } = useBossStore.getState()
      await selectBoss({ id: 1 })

      const state = useBossStore.getState()
      expect(state.currentQuestion).toBeNull()
      expect(state.battleResult).toBeNull()
    })
  })

  describe('startChallenge', () => {
    it('应调用 challenge API 并更新状态到 answering 阶段', async () => {
      const question = { id: 1, type: 'choice', content: 'What is BFS?' }
      mockChallenge.mockResolvedValue({ question })

      const { startChallenge } = useBossStore.getState()
      await startChallenge(5, 10)

      const state = useBossStore.getState()
      expect(mockChallenge).toHaveBeenCalledWith(5, { card_id: 10 })
      expect(state.currentQuestion).toEqual(question)
      expect(state.battlePhase).toBe('answering')
      expect(state.selectedCardId).toBe(10)
      expect(state.loading).toBe(false)
    })

    it('API 失败时应回退到 selecting_card 阶段并设置 error', async () => {
      mockChallenge.mockRejectedValue(new Error('Challenge failed'))

      const { startChallenge } = useBossStore.getState()
      await startChallenge(5, 10)

      const state = useBossStore.getState()
      expect(state.error).toBe('Challenge failed')
      expect(state.battlePhase).toBe('selecting_card')
      expect(state.loading).toBe(false)
    })
  })

  describe('submitAnswer', () => {
    it('应调用 submit API 并更新状态到 result 阶段', async () => {
      const battleResult = { result: 'win', score: 100 }
      mockSubmit.mockResolvedValue(battleResult)

      const { submitAnswer } = useBossStore.getState()
      await submitAnswer(5, { answer: 'A', card_id: 10 })

      const state = useBossStore.getState()
      expect(mockSubmit).toHaveBeenCalledWith(5, { answer: 'A', card_id: 10 })
      expect(state.battleResult).toEqual(battleResult)
      expect(state.battlePhase).toBe('result')
      expect(state.loading).toBe(false)
    })

    it('API 失败时应回退到 answering 阶段并设置 error', async () => {
      mockSubmit.mockRejectedValue(new Error('Submit failed'))

      const { submitAnswer } = useBossStore.getState()
      await submitAnswer(5, { answer: 'A' })

      const state = useBossStore.getState()
      expect(state.error).toBe('Submit failed')
      expect(state.battlePhase).toBe('answering')
      expect(state.loading).toBe(false)
    })
  })
})
