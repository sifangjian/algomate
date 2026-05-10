import api from './api'

export const userService = {
  getUser: () => api.get('/v1/users'),

  getStats: () => api.get('/v1/dashboard/stats'),
}
