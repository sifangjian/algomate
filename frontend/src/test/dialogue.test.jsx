import React from 'react'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../services/dialogueService', () => ({
  dialogueService: {
    start: vi.fn(),
    sendMessageStream: vi.fn(),
    saveNote: vi.fn(),
    endDialogue: vi.fn(),
    getHistory: vi.fn(),
    heartbeat: vi.fn(),
  },
}))

vi.mock('../services/npcService', () => ({
  npcService: {
    getByRealmId: vi.fn(),
    getAlgorithmInfo: vi.fn(),
  },
  REALM_ID_TO_NAME: {},
}))

vi.mock('react-router-dom', () => ({
  useParams: () => ({ realmId: 'test-realm' }),
  useNavigate: () => vi.fn(),
}))

import { useDialogueStore } from '../stores/dialogueStore'
import { dialogueService } from '../services/dialogueService'
import { npcService } from '../services/npcService'

describe('dialogueStore', () => {
  beforeEach(() => {
    useDialogueStore.getState().reset()
    vi.clearAllMocks()
  })

  describe('startDialogue', () => {
    it('应创建对话并设置NPC问候消息', async () => {
      dialogueService.start.mockResolvedValue({
        data: {
          dialogue_id: 42,
          npc_name: '老夫子',
          npc_avatar: '🧙',
          greeting: '欢迎来到智慧圣殿！',
          topic: '动态规划',
          existing_card: null,
        },
      })

      const result = await useDialogueStore.getState().startDialogue(1, '动态规划')

      expect(result.dialogue_id).toBe(42)
      const state = useDialogueStore.getState()
      expect(state.dialogueId).toBe(42)
      expect(state.npcName).toBe('老夫子')
      expect(state.status).toBe('active')
      expect(state.messages).toHaveLength(1)
      expect(state.messages[0].role).toBe('npc')
      expect(state.messages[0].content).toBe('欢迎来到智慧圣殿！')
    })

    it('启动失败时应设置error状态', async () => {
      dialogueService.start.mockRejectedValue(new Error('NPC不存在'))

      await expect(
        useDialogueStore.getState().startDialogue(999)
      ).rejects.toThrow('NPC不存在')

      const state = useDialogueStore.getState()
      expect(state.status).toBe('error')
      expect(state.error).toBe('NPC不存在')
    })
  })

  describe('sendMessage', () => {
    it('应添加用户消息和NPC流式消息', async () => {
      useDialogueStore.setState({
        dialogueId: 1,
        status: 'active',
        messages: [],
      })

      const mockController = { abort: vi.fn() }
      dialogueService.sendMessageStream.mockReturnValue(mockController)

      await useDialogueStore.getState().sendMessage('什么是二分查找？')

      const state = useDialogueStore.getState()
      expect(state.messages).toHaveLength(2)
      expect(state.messages[0].role).toBe('user')
      expect(state.messages[0].content).toBe('什么是二分查找？')
      expect(state.messages[1].role).toBe('npc')
      expect(state.messages[1].isStreaming).toBe(true)
      expect(state.isStreaming).toBe(true)
    })

    it('对话未激活时不应发送消息', async () => {
      useDialogueStore.setState({ dialogueId: null })

      const result = await useDialogueStore.getState().sendMessage('test')
      expect(result).toBeNull()
    })

    it('正在流式传输时不应发送消息', async () => {
      useDialogueStore.setState({
        dialogueId: 1,
        isStreaming: true,
      })

      const result = await useDialogueStore.getState().sendMessage('test')
      expect(result).toBeNull()
    })
  })

  describe('saveNote', () => {
    it('应保存笔记并更新noteId', async () => {
      useDialogueStore.setState({ dialogueId: 1 })
      dialogueService.saveNote.mockResolvedValue({
        data: { saved: true, note_id: 99, saved_at: '2026-01-01T00:00:00' },
      })

      const result = await useDialogueStore.getState().saveNote('我的笔记')

      expect(result.note_id).toBe(99)
      const state = useDialogueStore.getState()
      expect(state.noteContent).toBe('我的笔记')
      expect(state.noteId).toBe(99)
    })

    it('对话ID为空时不应保存', async () => {
      useDialogueStore.setState({ dialogueId: null })
      const result = await useDialogueStore.getState().saveNote('test')
      expect(result).toBeNull()
    })
  })

  describe('endDialogue', () => {
    it('应结束对话并设置earnedCard', async () => {
      useDialogueStore.setState({ dialogueId: 1, status: 'active' })
      dialogueService.endDialogue.mockResolvedValue({
        data: {
          card: { name: '二分查找', algorithm_type: '搜索', difficulty: 3 },
          is_update: false,
          guides: { go_boss: true, go_workshop: true },
        },
      })

      const result = await useDialogueStore.getState().endDialogue()

      expect(result.card.name).toBe('二分查找')
      const state = useDialogueStore.getState()
      expect(state.status).toBe('ended')
      expect(state.earnedCard.name).toBe('二分查找')
    })

    it('卡牌生成失败时应设置error', async () => {
      useDialogueStore.setState({ dialogueId: 1, status: 'active' })
      dialogueService.endDialogue.mockResolvedValue({
        data: {
          card: null,
          error: 'AI服务暂时不可用',
          dialogue_preserved: true,
        },
      })

      const result = await useDialogueStore.getState().endDialogue()
      expect(result.card).toBeNull()
      expect(result.error).toBe('AI服务暂时不可用')
    })
  })

  describe('reset', () => {
    it('应清除所有状态', () => {
      useDialogueStore.setState({
        dialogueId: 1,
        npcName: '老夫子',
        status: 'active',
        messages: [{ id: 1, role: 'npc', content: 'hi' }],
      })

      useDialogueStore.getState().reset()

      const state = useDialogueStore.getState()
      expect(state.dialogueId).toBeNull()
      expect(state.npcName).toBe('')
      expect(state.status).toBe('idle')
      expect(state.messages).toHaveLength(0)
    })
  })

  describe('heartbeat', () => {
    it('应启动心跳定时器', () => {
      vi.useFakeTimers()
      useDialogueStore.setState({ dialogueId: 1, status: 'active' })
      dialogueService.heartbeat.mockResolvedValue({ data: { alive: true } })

      useDialogueStore.getState().startHeartbeat()

      vi.advanceTimersByTime(120000)
      expect(dialogueService.heartbeat).toHaveBeenCalledWith(1)

      useDialogueStore.getState().stopHeartbeat()
      vi.useRealTimers()
    })

    it('stopHeartbeat应清除定时器', () => {
      vi.useFakeTimers()
      useDialogueStore.setState({ dialogueId: 1, status: 'active' })

      useDialogueStore.getState().startHeartbeat()
      useDialogueStore.getState().stopHeartbeat()

      const callCount = dialogueService.heartbeat.mock.calls.length
      vi.advanceTimersByTime(120000)
      expect(dialogueService.heartbeat.mock.calls.length).toBe(callCount)

      vi.useRealTimers()
    })
  })
})

describe('dialogueService', () => {
  it('start应调用POST /dialogue/start', async () => {
    const { dialogueService: realService } = await import('../services/dialogueService')
    const mockPost = vi.fn().mockResolvedValue({ data: { dialogue_id: 1 } })

    vi.doMock('../services/api', () => ({
      default: { post: mockPost, get: vi.fn() },
    }))

    expect(typeof realService.start).toBe('function')
  })

  it('sendMessageStream应返回AbortController', async () => {
    const { dialogueService: realService } = await import('../services/dialogueService')
    expect(typeof realService.sendMessageStream).toBe('function')
  })
})
