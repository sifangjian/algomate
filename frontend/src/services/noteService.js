import api from './api'

export const noteService = {
  getAll: (params) => {
    const searchParams = new URLSearchParams()
    if (params?.algorithm_type) searchParams.set('algorithm_type', params.algorithm_type)
    if (params?.difficulty) searchParams.set('difficulty', params.difficulty)
    if (params?.keyword) searchParams.set('keyword', params.keyword)
    if (params?.cardId) searchParams.set('cardId', params.cardId)
    if (params?.npcId) searchParams.set('npcId', params.npcId)
    if (params?.latest) searchParams.set('latest', '1')
    const query = searchParams.toString()
    return api.get(`/notes${query ? `?${query}` : ''}`)
  },

  getById: (id) => api.get(`/notes/${id}`),

  create: (data) => api.post('/notes', data),

  update: (id, data) => api.put(`/notes/${id}`, data),

  deleteNote: (id) => api.delete(`/notes/${id}`),

  analyze: (id) => api.post(`/notes/${id}/analyze`),
}
