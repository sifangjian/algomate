import api from './api'

export const userService = {
  getUser: () => api.get('/user'),

  getStats: () => api.get('/dashboard/stats'),
}
