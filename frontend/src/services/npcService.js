import api from './api'

export const npcService = {
  getAll: (params) => {
    const searchParams = new URLSearchParams()
    if (params?.algorithm_type)
      searchParams.set('algorithm_type', params.algorithm_type)
    if (params?.keyword)
      searchParams.set('keyword', params.keyword)
    const query = searchParams.toString()
    return api.get(`/v1/npcs${query ? `?${query}` : ''}`)
  },

  getById: (id) => api.get(`/v1/npcs/${id}`),

  getByRealmId: (realmId) => {
    const npcId = REALM_TO_NPC_ID[realmId]
    if (npcId) {
      return api.get(`/v1/npcs/${npcId}`)
    }
    if (typeof realmId === 'number' || !isNaN(Number(realmId))) {
      return api.get(`/v1/npcs/${realmId}`)
    }
    return Promise.reject(new Error(`未找到领域 ${realmId} 的导师`))
  },

  getAlgorithmInfo: () => api.get('/v1/algorithm-info'),

  chat: (npcId, message, sessionId) =>
    api.post(`/v1/npcs/${npcId}/chat`, { message, sessionId }),

  chatStream: (npcId, message, sessionId, { onChunk, onSuggestions, onDone, onError }) => {
    const baseURL = '/api'
    const url = `${baseURL}/v1/npcs/${npcId}/chat/stream`

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

const REALM_TO_NPC_ID = {
  'basic_data_structure': 1,
  '基础数据结构': 1,
  'stack_queue_search': 2,
  '搜索与基础': 2,
  'search_traversal': 3,
  '搜索进阶': 3,
  'tree': 4,
  '树结构': 4,
  'graph': 5,
  '图结构': 5,
  'backtracking': 6,
  '回溯算法': 6,
  'greedy': 7,
  '贪心算法': 7,
  'dynamic_programming': 8,
  '动态规划': 8,
  'divide_conquer': 9,
  '分治与排序': 9,
  'math_bit': 10,
  '数学与位运算': 10,
}

export const LOCATION_TO_REALM_ID = {
  '基础数据结构': 'basic_data_structure',
  '搜索与基础': 'stack_queue_search',
  '搜索进阶': 'search_traversal',
  '树结构': 'tree',
  '图结构': 'graph',
  '回溯算法': 'backtracking',
  '贪心算法': 'greedy',
  '动态规划': 'dynamic_programming',
  '分治与排序': 'divide_conquer',
  '数学与位运算': 'math_bit',
}

export const REALM_ID_TO_NAME = {
  'basic_data_structure': '基础数据结构',
  'stack_queue_search': '搜索与基础',
  'search_traversal': '搜索进阶',
  'tree': '树结构',
  'graph': '图结构',
  'backtracking': '回溯算法',
  'greedy': '贪心算法',
  'dynamic_programming': '动态规划',
  'divide_conquer': '分治与排序',
  'math_bit': '数学与位运算',
}

export function getRealmIdByNpcId(npcId) {
  for (const [realmId, id] of Object.entries(REALM_TO_NPC_ID)) {
    if (id === npcId && !realmId.match(/[一-鿿]/)) {
      return realmId
    }
  }
  return null
}