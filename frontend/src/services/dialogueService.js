import api from './api'

export const dialogueService = {
  start: (npcId, topic) =>
    api.post('/v1/dialogues/start', { npc_id: npcId, topic: topic || null }),

  sendMessage: (dialogueId, content) =>
    api.post(`/v1/dialogues/${dialogueId}/message`, { content }),

  sendMessageStream: (dialogueId, content, { onChunk, onSuggestions, onOutOfDomain, onDone, onError }) => {
    const baseURL = '/api'
    const url = `${baseURL}/v1/dialogues/${dialogueId}/message`
    const controller = new AbortController()
    const token = localStorage.getItem('auth_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`

    fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content }),
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || errorData.message || `请求失败 (${response.status})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const processLine = (line) => {
        if (!line.startsWith('data: ')) return false
        const dataStr = line.slice(6).trim()
        if (dataStr === '[DONE]') {
          onDone?.()
          return true
        }
        try {
          const data = JSON.parse(dataStr)
          if (data.error) {
            onError?.(new Error(data.error))
            return true
          }
          if (data.content) {
            onChunk?.(data.content)
          }
          if (data.suggestions) {
            onSuggestions?.(data.suggestions)
          }
          if (data.out_of_domain) {
            onOutOfDomain?.(data.out_of_domain.message || data.out_of_domain || '超出修习范围')
          }
        } catch (e) {
          console.warn('[SSE] Failed to parse data:', dataStr, e)
        }
        return false
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (processLine(line)) return
        }
      }

      if (buffer.trim()) {
        processLine(buffer)
      }

      onDone?.()
    }).catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })

    return controller
  },

  saveNote: (dialogueId, content) =>
    api.post(`/v1/dialogues/${dialogueId}/note`, { content }),

  endDialogue: (dialogueId) =>
    api.post(`/v1/dialogues/${dialogueId}/end`),

  getHistory: (dialogueId) =>
    api.get(`/v1/dialogues/${dialogueId}/history`),

  heartbeat: (dialogueId) =>
    api.post(`/v1/dialogues/${dialogueId}/heartbeat`),
}
