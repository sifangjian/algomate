import api from './api'

export const cardService = {
  getAll: (params) => {
    const searchParams = new URLSearchParams()
    if (params?.realm) searchParams.set('realm', params.realm)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.sort) searchParams.set('sort', params.sort)
    if (params?.order) searchParams.set('order', params.order)
    const query = searchParams.toString()
    return api.get(`/cards${query ? `?${query}` : ''}`)
  },

  getById: (id) => api.get(`/cards/${id}`),

  deleteCard: (id) => api.delete(`/cards/${id}`),

  getAvailable: () => api.get('/cards?available=true'),
}
