import api, { apiWithRetry } from './api'

const REALM_TO_NPC_ID = {
    'novice_forest': 1,
    '新手森林': 1,
    'mist_swamp': 2,
    '迷雾沼泽': 2,
    'ancient_forest': 3,
    '古树森林': 3,
    'fate_maze': 4,
    '命运迷宫': 4,
    'greed_tower': 5,
    '贪婪之塔': 5,
    'wisdom_temple': 6,
    '智慧圣殿': 6,
    'split_mountain': 7,
    '分裂山脉': 7,
    'math_hall': 8,
    '数学殿堂': 8,
    'trial_ground': 9,
    '试炼之地': 9,
}

export const LOCATION_TO_REALM_ID = {
    '新手森林': 'novice_forest',
    '迷雾沼泽': 'mist_swamp',
    '古树森林': 'ancient_forest',
    '命运迷宫': 'fate_maze',
    '贪婪之塔': 'greed_tower',
    '智慧圣殿': 'wisdom_temple',
    '分裂山脉': 'split_mountain',
    '数学殿堂': 'math_hall',
    '试炼之地': 'trial_ground',
}

export const REALM_ID_TO_NAME = {
    'novice_forest': '新手森林',
    'mist_swamp': '迷雾沼泽',
    'ancient_forest': '古树森林',
    'fate_maze': '命运迷宫',
    'greed_tower': '贪婪之塔',
    'wisdom_temple': '智慧圣殿',
    'split_mountain': '分裂山脉',
    'math_hall': '数学殿堂',
    'trial_ground': '试炼之地',
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

    getAllNpcs: () => api.get('/npcs/'),

    getAlgorithmInfo: () => api.get('/algorithm-info'),

    chat: (npcId, message, sessionId) =>
        apiWithRetry(() => api.post(`/npc/${npcId}/chat`, { message, sessionId })),

    chatStream: (npcId, message, sessionId, { onChunk, onSuggestions, onDone, onError }) => {
        const baseURL = '/api'
        const url = `${baseURL}/npc/${npcId}/chat/stream`

        const controller = new AbortController()

        const body = JSON.stringify({ message, sessionId })

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body,
            signal: controller.signal,
        }).then(async (response) => {
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }))
                throw new Error(errorData.detail || `请求失败 (${response.status})`)
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim()
                        if (dataStr === '[DONE]') {
                            onDone?.()
                            return
                        }
                        try {
                            const data = JSON.parse(dataStr)
                            if (data.error) {
                                onError?.(new Error(data.error))
                                return
                            }
                            if (data.content) {
                                onChunk?.(data.content)
                            }
                            if (data.suggestions) {
                                onSuggestions?.(data.suggestions)
                            }
                            if (data.dialogue_id) {
                                onDone?.(data.dialogue_id)
                            }
                        } catch (e) {
                            // Ignore parse errors for incomplete chunks
                        }
                    }
                }
            }
        }).catch((err) => {
            if (err.name !== 'AbortError') {
                onError?.(err)
            }
        })

        return controller
    },
}
