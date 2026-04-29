import api, { apiWithRetry } from './api'

const REALM_TO_NPC_ID = {
    'novice_forest': 1,
    '新手森林': 1,
    'mist_swamp': 2,
    '迷雾沼泽': 2,
    'wisdom_temple': 3,
    '智慧圣殿': 3,
    'greed_tower': 4,
    '贪婪之塔': 4,
    'fate_maze': 5,
    '命运迷宫': 5,
    'split_mountain': 6,
    '分裂山脉': 6,
    'math_hall': 7,
    '数学殿堂': 7,
    'trial_ground': 8,
    '试炼之地': 8,
}

export const LOCATION_TO_REALM_ID = {
    '新手森林': 'novice_forest',
    '迷雾沼泽': 'mist_swamp',
    '智慧圣殿': 'wisdom_temple',
    '贪婪之塔': 'greed_tower',
    '命运迷宫': 'fate_maze',
    '分裂山脉': 'split_mountain',
    '数学殿堂': 'math_hall',
    '试炼之地': 'trial_ground',
}

export const npcService = {
    getByRealmId: (realmId) => {
        if (!realmId) {
            return Promise.reject(new Error('realmId is required'))
        }
        const numericId = Number(realmId)
        const npcId = !isNaN(numericId) && String(numericId) === String(realmId) ? numericId : REALM_TO_NPC_ID[realmId]
        if (!npcId) {
            return Promise.reject(new Error(`Unknown realm: ${realmId}`))
        }
        return api.get(`/npc/${npcId}`)
    },

    getNpcIdByRealm: (realmId) => {
        if (!realmId) return null
        const numericId = Number(realmId)
        if (!isNaN(numericId) && String(numericId) === String(realmId)) {
            return numericId
        }
        return REALM_TO_NPC_ID[realmId] || null
    },

    getUnlockedNpcs: () => api.get('/npcs/unlocked'),

    chat: (npcId, message, sessionId) =>
        apiWithRetry(() => api.post(`/npc/${npcId}/chat`, { message, sessionId })),
}
