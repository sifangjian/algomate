import api from './api'

export const cardService = {
  // === 旧版（保留兼容） ===
  getAll: async (params) => {
    const searchParams = new URLSearchParams()
    if (params?.algorithm_type) searchParams.set('algorithm_type', params.algorithm_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.keyword) searchParams.set('keyword', params.keyword)
    const query = searchParams.toString()
    return await api.get(`/v1/cards${query ? `?${query}` : ''}`)
  },

  getById: async (id) => {
    return await api.get(`/v1/cards/${id}`)
  },

  createCard: async (data) => {
    return await api.post('/v1/cards', data)
  },

  // === 题目卡片 API ===
  createProblem: async (data) => {
    return await api.post('/v1/problems', data)
  },

  getProblems: async (params = {}) => {
    const searchParams = new URLSearchParams()
    if (params.tags) searchParams.set('tags', params.tags)
    if (params.status) searchParams.set('status', params.status)
    if (params.difficulty) searchParams.set('difficulty', params.difficulty)
    const query = searchParams.toString()
    return await api.get(`/v1/problems${query ? `?${query}` : ''}`)
  },

  getProblem: async (id) => {
    return await api.get(`/v1/problems/${id}`)
  },

  updateProblem: async (id, data) => {
    return await api.put(`/v1/problems/${id}`, data)
  },

  deleteProblem: async (id) => {
    return await api.delete(`/v1/problems/${id}`)
  },

  // === 解法卡片 API ===
  createSolution: async (data) => {
    return await api.post('/v1/solutions', data)
  },

  getSolution: async (id) => {
    return await api.get(`/v1/solutions/${id}`)
  },

  updateSolution: async (id, data) => {
    return await api.put(`/v1/solutions/${id}`, data)
  },

  deleteSolution: async (id) => {
    return await api.delete(`/v1/solutions/${id}`)
  },

  linkTechnique: async (solutionId, techniqueId) => {
    return await api.post(`/v1/solutions/${solutionId}/techniques`, { technique_id: techniqueId })
  },

  unlinkTechnique: async (solutionId, techniqueId) => {
    return await api.delete(`/v1/solutions/${solutionId}/techniques/${techniqueId}`)
  },

  getSolutionBacklinks: async (solutionId) => {
    return await api.get(`/v1/solutions/${solutionId}/backlinks`)
  },

  // === 技巧卡片 API ===
  createTechnique: async (data) => {
    return await api.post('/v1/techniques', data)
  },

  getTechniques: async (params = {}) => {
    const searchParams = new URLSearchParams()
    if (params.category) searchParams.set('category', params.category)
    if (params.due_only) searchParams.set('due_only', 'true')
    if (params.algorithm_type) searchParams.set('algorithm_type', params.algorithm_type)
    const query = searchParams.toString()
    return await api.get(`/v1/techniques${query ? `?${query}` : ''}`)
  },

  getTechnique: async (id) => {
    return await api.get(`/v1/techniques/${id}`)
  },

  updateTechnique: async (id, data) => {
    return await api.put(`/v1/techniques/${id}`, data)
  },

  deleteTechnique: async (id) => {
    return await api.delete(`/v1/techniques/${id}`)
  },

  selfReviewTechnique: async (id, selfRating) => {
    return await api.post(`/v1/techniques/${id}/review`, { self_rating: selfRating })
  },

  getTechniqueBacklinks: async (id) => {
    return await api.get(`/v1/techniques/${id}/backlinks`)
  },

  // === 通用删除卡片（根据类型路由） ===
  deleteCard: async (type, id) => {
    switch (type) {
      case 'problem':
        return await api.delete(`/v1/problems/${id}`)
      case 'solution':
        return await api.delete(`/v1/solutions/${id}`)
      case 'technique':
        return await api.delete(`/v1/techniques/${id}`)
      default:
        throw new Error(`Unknown card type: ${type}`)
    }
  },

  // === 概览 API ===
  getOverview: async () => {
    return await api.get('/v1/overview')
  },

  getTopicDetail: async (algorithmType) => {
    return await api.get(`/v1/overview/topic/${encodeURIComponent(algorithmType)}`)
  },

  getSolutions: async () => {
    return await api.get('/v1/solutions')
  },

  // === 复习相关（保留） ===
  startReview: (cardId) => api.post(`/v1/dashboard/review/start/${cardId}`),
  completeReview: (cardId, action) => api.post(`/v1/dashboard/review/complete/${cardId}`, { action }),
  skipReview: (cardId) => api.post(`/v1/dashboard/review/skip/${cardId}`),
  getReviewSchedule: (cardId) => api.get(`/v1/dashboard/review/schedule/${cardId}`),
  getTodayReviewPlan: () => api.get('/v1/dashboard/today-review'),
  getWeakPoints: (threshold) => api.get(`/v1/dashboard/weak-points?threshold=${threshold || 30}`),
  getTodayStats: () => api.get('/v1/stats/today'),
  getReviewStats: () => api.get('/v1/dashboard/review/statistics'),
  getTodayReviewTasks: () => api.get('/v1/reviews/today'),
  completeReviewV1: (cardId, reviewType) => api.post(`/v1/reviews/${cardId}/complete`, { review_type: reviewType }),
}
