import { create } from 'zustand'
import { dialogueService } from '../services/dialogueService'
import { useGuideStore } from './guideStore'
import { useSettingsStore } from './settingsStore'
import { showToast } from '../components/ui/Toast/index'

const HEARTBEAT_INTERVAL = 120000

export const useDialogueStore = create((set, get) => ({
  dialogueId: null,
  npcId: null,
  npcName: '',
  npcAvatar: '',
  topic: '',
  status: 'idle',
  messages: [],
  noteContent: '',
  noteId: null,
  suggestions: [],
  existingCard: null,
  earnedCard: null,
  isStreaming: false,
  error: null,
  heartbeatTimer: null,

  startDialogue: async (npcId, topic) => {
    set({ status: 'starting', error: null })
    try {
      const data = await dialogueService.start(npcId, topic)
      const dialogueData = data.data || data
      set({
        dialogueId: dialogueData.dialogue_id,
        npcId,
        npcName: dialogueData.npc_name || '',
        npcAvatar: dialogueData.npc_avatar || '',
        topic: dialogueData.topic || topic || '',
        status: 'active',
        messages: [{
          id: 'greeting',
          role: 'npc',
          content: dialogueData.greeting || '',
          timestamp: new Date().toISOString(),
          displayed: true,
        }],
        existingCard: dialogueData.existing_card || null,
      })
      get().startHeartbeat()
      return dialogueData
    } catch (err) {
      set({ status: 'error', error: err.message })
      throw err
    }
  },

  sendMessage: async (content) => {
    const { dialogueId, isStreaming } = get()
    if (!dialogueId || isStreaming) return null

    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      displayed: true,
    }

    const npcMsgId = `npc_${Date.now()}`
    const npcMsg = {
      id: npcMsgId,
      role: 'npc',
      content: '',
      timestamp: new Date().toISOString(),
      displayed: true,
      isStreaming: true,
      suggestions: [],
    }

    set((state) => ({
      messages: [...state.messages, userMsg, npcMsg],
      isStreaming: true,
      suggestions: [],
    }))

    let accumulatedContent = ''

    const controller = dialogueService.sendMessageStream(dialogueId, content, {
      onChunk: (token) => {
        accumulatedContent += token
        const currentContent = accumulatedContent
        set((state) => {
          const updated = [...state.messages]
          const idx = updated.findIndex((m) => m.id === npcMsgId)
          if (idx >= 0) {
            updated[idx] = { ...updated[idx], content: currentContent }
          }
          return { messages: updated }
        })
      },
      onSuggestions: (suggestions) => {
        set({ suggestions })
        set((state) => {
          const updated = [...state.messages]
          const idx = updated.findIndex((m) => m.id === npcMsgId)
          if (idx >= 0) {
            updated[idx] = { ...updated[idx], suggestions }
          }
          return { messages: updated }
        })
      },
      onOutOfDomain: (message) => {
        set((state) => {
          const updated = [...state.messages]
          const idx = updated.findIndex((m) => m.id === npcMsgId)
          if (idx >= 0) {
            updated[idx] = {
              ...updated[idx],
              content: accumulatedContent + `\n\n⚠️ ${message}`,
              isStreaming: false,
            }
          }
          return { messages: updated, isStreaming: false }
        })
      },
      onDone: () => {
        set((state) => {
          const updated = [...state.messages]
          const idx = updated.findIndex((m) => m.id === npcMsgId)
          if (idx >= 0) {
            updated[idx] = { ...updated[idx], isStreaming: false }
          }
          return { messages: updated, isStreaming: false }
        })
      },
      onError: (err) => {
        set((state) => {
          const updated = [...state.messages]
          const idx = updated.findIndex((m) => m.id === npcMsgId)
          if (idx >= 0) {
            updated[idx] = {
              ...updated[idx],
              content: `抱歉，遇到了一些问题：${err.message}。请稍后再试。`,
              isStreaming: false,
            }
          }
          return { messages: updated, isStreaming: false, error: err.message }
        })
      },
    })

    return controller
  },

  saveNote: async (content) => {
    const { dialogueId } = get()
    if (!dialogueId) return null
    try {
      const data = await dialogueService.saveNote(dialogueId, content)
      const noteData = data.data || data
      set({ noteContent: content, noteId: noteData.note_id })
      return noteData
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },

  endDialogue: async () => {
    const { dialogueId } = get()
    if (!dialogueId) return null
    get().stopHeartbeat()
    try {
      const data = await dialogueService.endDialogue(dialogueId)
      const endData = data.data || data
      set({
        status: 'ended',
        earnedCard: endData.card || null,
        error: endData.error || null,
      })
      if (endData.guides) {
        useGuideStore.getState().setGuide(endData.guides)
      }
      if (endData.card) {
        const { onboardingCompleted, completeOnboarding } = useSettingsStore.getState()
        if (!onboardingCompleted) {
          try {
            await completeOnboarding()
          } catch {
            localStorage.setItem('algomate_onboarding_completed', 'true')
            useSettingsStore.setState({ onboardingCompleted: true })
          }
          showToast('恭喜完成新手引导！', 'success')
        }
      }
      return endData
    } catch (err) {
      set({ status: 'error', error: err.message })
      throw err
    }
  },

  loadHistory: async (dialogueId) => {
    try {
      const data = await dialogueService.getHistory(dialogueId)
      const historyData = data.data || data
      set({
        dialogueId,
        messages: (historyData.messages || []).map((m) => ({
          ...m,
          displayed: true,
          isStreaming: false,
        })),
        noteContent: historyData.note?.content || '',
        noteId: historyData.note?.id || null,
        status: historyData.status || 'active',
        npcName: historyData.npc_name || '',
        npcAvatar: historyData.npc_avatar || '',
        topic: historyData.topic || '',
      })
      return historyData
    } catch (err) {
      set({ error: err.message })
      throw err
    }
  },

  startHeartbeat: () => {
    get().stopHeartbeat()
    const timer = setInterval(async () => {
      const { dialogueId, status } = get()
      if (!dialogueId || status !== 'active') {
        get().stopHeartbeat()
        return
      }
      try {
        await dialogueService.heartbeat(dialogueId)
      } catch (err) {
        console.error('Heartbeat failed:', err)
      }
    }, HEARTBEAT_INTERVAL)
    set({ heartbeatTimer: timer })
  },

  stopHeartbeat: () => {
    const { heartbeatTimer } = get()
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      set({ heartbeatTimer: null })
    }
  },

  reset: () => {
    get().stopHeartbeat()
    set({
      dialogueId: null,
      npcId: null,
      npcName: '',
      npcAvatar: '',
      topic: '',
      status: 'idle',
      messages: [],
      noteContent: '',
      noteId: null,
      suggestions: [],
      existingCard: null,
      earnedCard: null,
      isStreaming: false,
      error: null,
      heartbeatTimer: null,
    })
  },
}))
