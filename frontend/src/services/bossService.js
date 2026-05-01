import api from './api'

export const bossService = {
  getBoss: (bossId) => api.get(`/boss/${bossId}`),

  generateForCard: (cardId) =>
    api.post('/boss/generate-for-card', { card_id: cardId }),

  submitAnswer: (bossId, data) =>
    api.post(`/boss/${bossId}/submit`, data),
}
