import api from './api'

export const userService = {
  getStats: () => api.get('/v1/dashboard/stats'),
}