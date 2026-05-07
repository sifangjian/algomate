import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

const STORAGE_KEY_PREFIX = 'guide_skipped_'

const sessionStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
    _store: () => store,
  }
})()

Object.defineProperty(globalThis, 'sessionStorage', { value: sessionStorageMock })

import { useGuideStore } from '../../stores/guideStore'

const SAMPLE_GUIDE = {
  available_actions: [
    { action: 'go_boss', label: '去 Boss 战巩固', target_path: '/boss', params: { card_id: 1 } },
    { action: 'go_workshop', label: '去卡牌工坊完善', target_path: '/workshop', params: { card_id: 1, expand: true } },
  ],
  message: '恭喜获得卡牌！',
}

const INITIAL_STATE = {
  currentGuide: null,
  visible: false,
  cardAcquired: {
    card: null,
    animating: false,
  },
}

describe('guideStore', () => {
  beforeEach(() => {
    useGuideStore.setState(INITIAL_STATE)
    vi.clearAllMocks()
    sessionStorageMock.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应包含所有默认值', () => {
      const state = useGuideStore.getState()
      expect(state.currentGuide).toBeNull()
      expect(state.visible).toBe(false)
      expect(state.cardAcquired).toEqual({ card: null, animating: false })
    })
  })

  describe('setGuide', () => {
    it('应设置 currentGuide 并将 visible 设为 true', () => {
      const { setGuide } = useGuideStore.getState()
      setGuide(SAMPLE_GUIDE)

      const state = useGuideStore.getState()
      expect(state.currentGuide).toEqual(SAMPLE_GUIDE)
      expect(state.visible).toBe(true)
    })

    it('应替换之前的引导数据', () => {
      const { setGuide } = useGuideStore.getState()
      setGuide(SAMPLE_GUIDE)
      setGuide({ available_actions: [], message: '新引导' })

      const state = useGuideStore.getState()
      expect(state.currentGuide.message).toBe('新引导')
      expect(state.currentGuide.available_actions).toEqual([])
    })
  })

  describe('setCardAcquired', () => {
    it('应设置 cardAcquired.card 并在 card 非 null 时设 animating 为 true', () => {
      const card = { id: 1, name: '测试卡牌' }
      const { setCardAcquired } = useGuideStore.getState()
      setCardAcquired(card)

      const state = useGuideStore.getState()
      expect(state.cardAcquired.card).toEqual(card)
      expect(state.cardAcquired.animating).toBe(true)
    })

    it('card 为 null 时应设 animating 为 false', () => {
      const { setCardAcquired } = useGuideStore.getState()
      setCardAcquired(null)

      const state = useGuideStore.getState()
      expect(state.cardAcquired.card).toBeNull()
      expect(state.cardAcquired.animating).toBe(false)
    })
  })

  describe('setAnimating', () => {
    it('应更新 animating 状态', () => {
      useGuideStore.setState({
        cardAcquired: { card: { id: 1, name: '测试' }, animating: true },
      })

      const { setAnimating } = useGuideStore.getState()
      setAnimating(false)

      expect(useGuideStore.getState().cardAcquired.animating).toBe(false)
      expect(useGuideStore.getState().cardAcquired.card).toEqual({ id: 1, name: '测试' })
    })
  })

  describe('dismissGuide', () => {
    it('应将 currentGuide 设为 null 并将 visible 设为 false', () => {
      useGuideStore.setState({ currentGuide: SAMPLE_GUIDE, visible: true })

      const { dismissGuide } = useGuideStore.getState()
      dismissGuide()

      const state = useGuideStore.getState()
      expect(state.currentGuide).toBeNull()
      expect(state.visible).toBe(false)
    })
  })

  describe('resetGuide', () => {
    it('应重置所有状态到初始值', () => {
      useGuideStore.setState({
        currentGuide: SAMPLE_GUIDE,
        visible: true,
        cardAcquired: { card: { id: 1, name: '测试' }, animating: true },
      })

      const { resetGuide } = useGuideStore.getState()
      resetGuide()

      const state = useGuideStore.getState()
      expect(state.currentGuide).toBeNull()
      expect(state.visible).toBe(false)
      expect(state.cardAcquired).toEqual({ card: null, animating: false })
    })
  })

  describe('skipGuide', () => {
    it('应将跳过记录写入 sessionStorage', () => {
      const { skipGuide } = useGuideStore.getState()
      skipGuide('after_dialogue')

      expect(sessionStorageMock.setItem).toHaveBeenCalledWith(
        'guide_skipped_after_dialogue',
        'true'
      )
    })

    it('应同时 dismissGuide', () => {
      useGuideStore.setState({ currentGuide: SAMPLE_GUIDE, visible: true })

      const { skipGuide } = useGuideStore.getState()
      skipGuide('after_dialogue')

      const state = useGuideStore.getState()
      expect(state.currentGuide).toBeNull()
      expect(state.visible).toBe(false)
    })

    it('应支持多个场景的跳过记录', () => {
      const { skipGuide } = useGuideStore.getState()
      skipGuide('after_dialogue')
      skipGuide('after_boss')

      expect(sessionStorageMock.setItem).toHaveBeenCalledWith(
        'guide_skipped_after_dialogue',
        'true'
      )
      expect(sessionStorageMock.setItem).toHaveBeenCalledWith(
        'guide_skipped_after_boss',
        'true'
      )
    })
  })

  describe('shouldShowGuide', () => {
    it('未跳过的场景应返回 true', () => {
      const { shouldShowGuide } = useGuideStore.getState()
      expect(shouldShowGuide('after_dialogue')).toBe(true)
    })

    it('已跳过的场景应返回 false', () => {
      const { skipGuide, shouldShowGuide } = useGuideStore.getState()
      skipGuide('after_dialogue')

      const result = shouldShowGuide('after_dialogue')
      expect(result).toBe(false)
    })

    it('不同场景的跳过互不影响', () => {
      const { skipGuide, shouldShowGuide } = useGuideStore.getState()
      skipGuide('after_dialogue')

      expect(shouldShowGuide('after_dialogue')).toBe(false)
      expect(shouldShowGuide('after_boss')).toBe(true)
    })
  })
})
