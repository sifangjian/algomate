import api from './api'

export const npcService = {
  getAll: async () => {
    return await api.get('/v1/algorithm-info')
  },
}
