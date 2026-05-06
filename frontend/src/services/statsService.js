import api from './api'

export const statsService = {
  getOverview: () => api.get('/stats/overview'),

  getHallStats: () => api.get('/v1/stats'),
}
