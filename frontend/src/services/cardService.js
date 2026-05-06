import api from './api'

export const cardService = {
  getAll: (params) => {
    const searchParams = new URLSearchParams()
    if (params?.algorithm_type) searchParams.set('algorithm_type', params.algorithm_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.keyword) searchParams.set('keyword', params.keyword)
    if (params?.realm) searchParams.set('domain', params.realm)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.sort) searchParams.set('sort', params.sort)
    if (params?.order) searchParams.set('order', params.order)
    const query = searchParams.toString()
    return api.get(`/cards/${query ? `?${query}` : ''}`)
  },

  getById: (id) => api.get(`/cards/${id}`),

  deleteCard: (id) => api.delete(`/cards/${id}`),

  getAvailable: () => api.get('/cards?available=true'),

  createCard: (data) => api.post('/cards/', data),

  getByAlgorithmType: (algorithmType) => {
    if (!algorithmType) return Promise.resolve([])
    return api.get(`/cards/?algorithm_category=${encodeURIComponent(algorithmType)}`)
  },

  getByAlgorithmTypeField: (algorithmType) => {
    if (!algorithmType) return Promise.resolve([])
    return api.get(`/cards/?algorithm_type=${encodeURIComponent(algorithmType)}`)
  },

  updateCard: (id, data) => api.put(`/cards/${id}`, data),

  unsealCard: (id) => api.post(`/cards/${id}/unseal`),

  retakeCard: (id) => api.post(`/cards/${id}/retake`),

  polishCard: (data) => api.post('/cards/polish', data),

  startReview: (cardId) => api.post(`/review/start/${cardId}`),

  completeReview: (cardId, action) => api.post(`/review/complete/${cardId}`, { action }),

  skipReview: (cardId) => api.post(`/review/skip/${cardId}`),

  getReviewSchedule: (cardId) => api.get(`/review/schedule/${cardId}`),

  getTodayReviewPlan: () => api.get('/review/plan'),

  getWeakPoints: (threshold) => api.get(`/review/weak-points?threshold=${threshold || 30}`),

  getReviewStats: () => api.get('/review/statistics'),
}
