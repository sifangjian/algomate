import api from './api'

export const settingService = {
  getSettings: () => api.get('/v1/settings'),

  saveSettings: (data) => api.post('/v1/settings/legacy', data),

  testApi: (apiKey) => api.post('/v1/settings/test-api', { apiKey }),

  testEmail: (emailConfig) => api.post('/v1/settings/test-email', emailConfig),

  getV1Settings: () => api.get('/v1/settings'),

  updateV1Settings: (data) => api.put('/v1/settings', data),
}

export const dashboardService = {
  getTodayReview: (date) => {
    const query = date ? `?target_date=${date}` : ''
    return api.get(`/v1/dashboard/today-review${query}`)
  },

  getWeakPoints: (threshold, limit) => {
    const params = new URLSearchParams()
    if (threshold) params.set('threshold', threshold)
    if (limit) params.set('limit', limit)
    return api.get(`/v1/dashboard/weak-points?${params.toString()}`)
  },

  startReview: (noteId) => api.post(`/v1/dashboard/review/start/${noteId}`),

  completeReview: (noteId, data) =>
    api.post(`/v1/dashboard/review/complete/${noteId}`, data),

  skipReview: (noteId, reason) =>
    api.post(`/v1/dashboard/review/skip/${noteId}`, { reason }),

  getStatistics: (date) => {
    const query = date ? `?target_date=${date}` : ''
    return api.get(`/v1/dashboard/review/statistics${query}`)
  },
}
