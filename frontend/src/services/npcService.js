import api from './api'

export const npcService = {
  getByRealmId: (realmId) => api.get(`/npc/${realmId}`),

  chat: (npcId, message, sessionId) =>
    api.post(`/npc/${npcId}/chat`, { message, sessionId }),
}
