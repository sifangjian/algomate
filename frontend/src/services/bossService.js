import api from './api'

export const bossService = {
  getBoss: (bossId) => api.get(`/boss/${bossId}`),

  submitAnswer: (bossId, code, cardId) =>
    api.post(`/boss/${bossId}/submit`, { code, cardId }),
}
