const BASE_URL = '/api/v1/quick-ask'

export const quickAskService = {
  askStream: (npcId, npcName, content, history, { onChunk, onDone, onError }) => {
    const controller = new AbortController()
    const token = localStorage.getItem('auth_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`

    fetch(BASE_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({ npc_id: npcId, npc_name: npcName, content, history }),
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
        } catch {
          // ignore parse errors
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
}
