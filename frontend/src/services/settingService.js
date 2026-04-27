import api from './api'

export const settingService = {
  getSettings: () => api.get('/settings/'),

  saveSettings: (data) => api.post('/settings/', data),

  testApi: (apiKey) => api.post('/settings/test-api', { apiKey }),

  testEmail: (emailConfig) => api.post('/settings/test-email', emailConfig),
}

export const dashboardService = {
  getTodayReview: (date) => {
    const query = date ? `?target_date=${date}` : ''
    return api.get(`/dashboard/today-review${query}`)
  },

  getWeakPoints: (threshold, limit) => {
    const params = new URLSearchParams()
    if (threshold) params.set('threshold', threshold)
    if (limit) params.set('limit', limit)
    return api.get(`/dashboard/weak-points?${params.toString()}`)
  },

  startReview: (noteId) => api.post(`/dashboard/review/start/${noteId}`),

  completeReview: (noteId, data) =>
    api.post(`/dashboard/review/complete/${noteId}`, data),

  skipReview: (noteId, reason) =>
    api.post(`/dashboard/review/skip/${noteId}`, { reason }),

  getStatistics: (date) => {
    const query = date ? `?target_date=${date}` : ''
    return api.get(`/dashboard/review/statistics${query}`)
  },
}
