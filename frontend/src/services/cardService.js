import api from './api'

export const cardService = {
  getAll: async (params) => {
    const searchParams = new URLSearchParams()
    if (params?.algorithm_type) searchParams.set('algorithm_type', params.algorithm_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.keyword) searchParams.set('keyword', params.keyword)
    const query = searchParams.toString()
    const result = await api.get(`/v1/cards${query ? `?${query}` : ''}`)
    return result.data
  },

  getById: async (id) => {
    const result = await api.get(`/v1/cards/${id}`)
    return result.data
  },

  update: async (id, data) => {
    const result = await api.put(`/v1/cards/${id}`, data)
    return result.data
  },

  delete: async (id) => {
    const result = await api.delete(`/v1/cards/${id}`)
    return result.data
  },

  retakeCard: async (id) => {
    const result = await api.post(`/v1/cards/${id}/retake`)
    return result.data
  },

  createCard: async (data) => {
    const result = await api.post('/v1/cards', data)
    return result.data
  },

  polishCard: async (data) => {
    const result = await api.post('/v1/cards/polish', data)
    return result.data
  },

  startReview: (cardId) => api.post(`/v1/dashboard/review/start/${cardId}`),

  completeReview: (cardId, action) => api.post(`/v1/dashboard/review/complete/${cardId}`, { action }),

  skipReview: (cardId) => api.post(`/v1/dashboard/review/skip/${cardId}`),

  getReviewSchedule: (cardId) => api.get(`/v1/dashboard/review/schedule/${cardId}`),

  getTodayReviewPlan: () => api.get('/v1/dashboard/today-review'),

  getWeakPoints: (threshold) => api.get(`/v1/dashboard/weak-points?threshold=${threshold || 30}`),

  getReviewStats: () => api.get('/v1/dashboard/review/statistics'),

  getTodayReviewTasks: () => api.get('/v1/reviews/today'),

  completeReviewV1: (cardId, reviewType) => api.post(`/v1/reviews/${cardId}/complete`, { review_type: reviewType }),

  generateReviewQuiz: (cardId, count = 2) => api.post(`/v1/reviews/${cardId}/quiz`, { count }),
}
