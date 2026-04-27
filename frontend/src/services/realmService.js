import api from './api'

export const realmService = {
  getAll: () => api.get('/realms'),

  getById: (id) => api.get(`/realms/${id}`),

  checkUnlock: (id) => api.post(`/realms/${id}/check-unlock`),
}
