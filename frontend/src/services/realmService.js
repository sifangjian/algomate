import api from './api'

export const realmService = {
  getAll: () => api.get('/v1/realms'),

  getById: (id) => api.get(`/v1/realms/${id}`),

  checkUnlock: (id) => api.post(`/v1/realms/${id}/check-unlock`),
}
