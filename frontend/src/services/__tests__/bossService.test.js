import { describe, it, expect, vi, afterEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('../api', () => ({
  default: {
    get: mockGet,
    post: mockPost,
  },
}))

import { bossService } from '../bossService'

describe('bossService', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('getBosses', () => {
    it('应调用 GET /v1/bosses 且不附带查询参数', async () => {
      mockGet.mockResolvedValue({ bosses: [] })
      await bossService.getBosses()
      expect(mockGet).toHaveBeenCalledWith('/v1/bosses')
    })

    it('应传递 difficulty 参数作为查询字符串', async () => {
      mockGet.mockResolvedValue({ bosses: [] })
      await bossService.getBosses({ difficulty: 'hard' })
      expect(mockGet).toHaveBeenCalledWith('/v1/bosses?difficulty=hard')
    })

    it('不传 difficulty 时不应附带查询字符串', async () => {
      mockGet.mockResolvedValue({ bosses: [] })
      await bossService.getBosses({})
      expect(mockGet).toHaveBeenCalledWith('/v1/bosses')
    })

    it('应返回 API 响应数据', async () => {
      const mockData = { bosses: [{ id: 1, name: 'Boss1' }] }
      mockGet.mockResolvedValue(mockData)
      const result = await bossService.getBosses()
      expect(result).toEqual(mockData)
    })
  })

  describe('getBossDetail', () => {
    it('应调用 GET /v1/bosses/{bossId}', async () => {
      mockGet.mockResolvedValue({ id: 42, name: 'Boss42' })
      await bossService.getBossDetail(42)
      expect(mockGet).toHaveBeenCalledWith('/v1/bosses/42')
    })

    it('应返回 Boss 详情数据', async () => {
      const mockDetail = { id: 1, name: 'Boss1', has_any_card: true }
      mockGet.mockResolvedValue(mockDetail)
      const result = await bossService.getBossDetail(1)
      expect(result).toEqual(mockDetail)
    })
  })

  describe('challenge', () => {
    it('应调用 POST /v1/bosses/{bossId}/challenge 并传递请求体', async () => {
      const body = { card_id: 10 }
      mockPost.mockResolvedValue({ question: {} })
      await bossService.challenge(5, body)
      expect(mockPost).toHaveBeenCalledWith('/v1/bosses/5/challenge', body)
    })

    it('应返回挑战响应数据', async () => {
      const mockResponse = { question: { id: 1, type: 'choice' } }
      mockPost.mockResolvedValue(mockResponse)
      const result = await bossService.challenge(5, { card_id: 10 })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('submit', () => {
    it('应调用 POST /v1/bosses/{bossId}/submit 并传递请求体', async () => {
      const body = { answer: 'A', card_id: 10 }
      mockPost.mockResolvedValue({ result: 'win' })
      await bossService.submit(5, body)
      expect(mockPost).toHaveBeenCalledWith('/v1/bosses/5/submit', body)
    })

    it('应返回提交结果数据', async () => {
      const mockResult = { result: 'win', score: 100 }
      mockPost.mockResolvedValue(mockResult)
      const result = await bossService.submit(5, { answer: 'A' })
      expect(result).toEqual(mockResult)
    })
  })
})
