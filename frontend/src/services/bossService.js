import api from './api'

export const bossService = {
  getBosses: (params) => {
    const searchParams = new URLSearchParams()
    if (params?.difficulty) searchParams.set('difficulty', params.difficulty)
    const query = searchParams.toString()
    return api.get(`/v1/bosses${query ? `?${query}` : ''}`)
  },
  getBossDetail: (bossId) => api.get(`/v1/bosses/${bossId}`),
  challenge: (bossId, body) => api.post(`/v1/bosses/${bossId}/challenge`, body),
  submit: (bossId, body) => api.post(`/v1/bosses/${bossId}/submit`, body),
}
