import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

Element.prototype.scrollIntoView = vi.fn()
HTMLDivElement.prototype.scrollIntoView = vi.fn()

const { mockStartDialogue, mockSendMessageStream, mockSaveNote, mockEndDialogue } = vi.hoisted(() => ({
  mockStartDialogue: vi.fn(),
  mockSendMessageStream: vi.fn(),
  mockSaveNote: vi.fn(),
  mockEndDialogue: vi.fn(),
}))

vi.mock('../../services/dialogueService', () => ({
  dialogueService: {
    start: mockStartDialogue,
    sendMessageStream: mockSendMessageStream,
    endDialogue: mockEndDialogue,
    saveNote: mockSaveNote,
    getHistory: vi.fn(),
    heartbeat: vi.fn(),
  },
}))

vi.mock('../../services/npcService', () => ({
  npcService: {
    getByRealmId: vi.fn().mockResolvedValue({
      data: {
        id: 1,
        name: '老夫子',
        avatar: '🧙',
        realm_id: 'binary_search',
        quickQuestions: [],
      },
    }),
    getAlgorithmInfo: vi.fn().mockResolvedValue({}),
  },
  REALM_ID_TO_NAME: {},
}))

vi.mock('../../components/ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

vi.mock('../../stores/guideStore', () => {
  const state = { currentGuide: null, visible: false, setGuide: vi.fn() }
  const useGuideStore = vi.fn(() => state)
  useGuideStore.getState = vi.fn(() => state)
  useGuideStore.subscribe = vi.fn()
  return { useGuideStore }
})

vi.mock('../../stores/settingsStore', () => ({
  useSettingsStore: {
    getState: vi.fn(() => ({
      onboardingCompleted: true,
      completeOnboarding: vi.fn(),
    })),
    subscribe: vi.fn(),
  },
}))

import NpcDialogue from '../NpcDialogue'
import { useDialogueStore } from '../../stores/dialogueStore'

function renderNpcDialogue(route = '/npc/binary_search') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/npc/:realmId" element={<NpcDialogue />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('NpcDialogue - CR-003 变更', () => {
  beforeEach(() => {
    useDialogueStore.getState().reset()
    vi.clearAllMocks()
    mockStartDialogue.mockResolvedValue({
      data: {
        dialogue_id: 'dlg_1',
        npc_name: '老夫子',
        npc_avatar: '🧙',
        greeting: '你好！我是老夫子',
        topics: ['二分查找'],
        existing_card: null,
      },
    })
  })

  describe('CR-003-T01: header 中不存在"结束修习"按钮', () => {
    it('页面 header 区域不应有"结束修习"按钮', async () => {
      renderNpcDialogue()

      await screen.findByText('老夫子', { selector: 'h2' })

      const backBtn = screen.getByLabelText('返回地图')
      const header = backBtn.closest('[class*="header"]')
      const endBtnInHeader = header
        ? [...header.querySelectorAll('button')].find((btn) =>
            btn.textContent.includes('结束修习')
          )
        : null
      expect(endBtnInHeader).toBeFalsy()
    })

    it('header 中不应有独立的"结束修习"Button 组件', async () => {
      renderNpcDialogue()

      await screen.findByText('老夫子', { selector: 'h2' })

      const backBtn = screen.getByLabelText('返回地图')
      const header = backBtn.closest('[class*="header"]')
      const headerButtons = header ? header.querySelectorAll('button') : []
      const endBtnInHeader = [...headerButtons].find((btn) =>
        btn.textContent.includes('结束修习') && btn.textContent.trim() === '结束修习'
      )
      expect(endBtnInHeader).toBeUndefined()
    })
  })

  describe('CR-003-T02: 保存心得按钮集成结束修习选择', () => {
    it('点击"保存心得"后应弹出选择对话框，包含"结束修习生成卡牌"和"继续修习完善卡牌"选项', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockSaveNote.mockResolvedValue({ data: { saved: true, note_id: 1, saved_at: '2026-05-10T10:00:00' } })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteEditor = screen.getByLabelText('修炼日记编辑器')
      await user.type(noteEditor, '二分查找的心得体会')

      const saveBtn = screen.getByRole('button', { name: /保存心得/ })
      await user.click(saveBtn)

      expect(await screen.findByText('心得已保存')).toBeInTheDocument()
      expect(screen.getByText(/是否结束修习生成卡牌/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /结束修习生成卡牌/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /继续修习完善卡牌/ })).toBeInTheDocument()
    })

    it('点击"结束修习生成卡牌"应触发 endDialogue', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockSaveNote.mockResolvedValue({ data: { saved: true, note_id: 1, saved_at: '2026-05-10T10:00:00' } })
      mockEndDialogue.mockResolvedValue({
        data: { card: { id: 1, name: '二分查找' }, is_update: false, guides: { go_boss: true, go_workshop: true } },
      })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteEditor = screen.getByLabelText('修炼日记编辑器')
      await user.type(noteEditor, '二分查找的心得体会')

      const saveBtn = screen.getByRole('button', { name: /保存心得/ })
      await user.click(saveBtn)

      const endBtn = await screen.findByRole('button', { name: /结束修习生成卡牌/ })
      await user.click(endBtn)

      expect(mockEndDialogue).toHaveBeenCalled()
    })

    it('点击"继续修习完善卡牌"应关闭对话框，留在对话页面', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockSaveNote.mockResolvedValue({ data: { saved: true, note_id: 1, saved_at: '2026-05-10T10:00:00' } })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteEditor = screen.getByLabelText('修炼日记编辑器')
      await user.type(noteEditor, '二分查找的心得体会')

      const saveBtn = screen.getByRole('button', { name: /保存心得/ })
      await user.click(saveBtn)

      const continueBtn = await screen.findByRole('button', { name: /继续修习完善卡牌/ })
      await user.click(continueBtn)

      expect(screen.queryByText('心得已保存')).not.toBeInTheDocument()
      expect(mockEndDialogue).not.toHaveBeenCalled()
    })

    it('保存心得失败时不应弹出选择对话框', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockSaveNote.mockRejectedValue(new Error('保存失败'))

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteEditor = screen.getByLabelText('修炼日记编辑器')
      await user.type(noteEditor, '二分查找的心得体会')

      const saveBtn = screen.getByRole('button', { name: /保存心得/ })
      await user.click(saveBtn)

      await new Promise((r) => setTimeout(r, 100))

      expect(screen.queryByText('心得已保存')).not.toBeInTheDocument()
    })
  })

  describe('CR-003-T03: 无心得内容时的结束修习入口', () => {
    it('笔记区域底部应有"结束修习"链接/按钮', async () => {
      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const endLink = noteSection.querySelector('[class*="endSessionLink"]')
      expect(endLink).toBeInTheDocument()
      expect(endLink.textContent).toContain('结束修习')
    })

    it('点击"结束修习"链接应弹出确认对话框', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const endLink = noteSection.querySelector('[class*="endSessionLink"]')
      await user.click(endLink)

      expect(await screen.findByText('确定要结束本次修习吗？')).toBeInTheDocument()
    })

    it('确认结束修习应触发 endDialogue', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      mockEndDialogue.mockResolvedValue({
        data: { card: { id: 1, name: '二分查找' }, is_update: false, guides: { go_boss: true, go_workshop: true } },
      })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const endLink = noteSection.querySelector('[class*="endSessionLink"]')
      await user.click(endLink)

      await screen.findByText('确定要结束本次修习吗？')
      const dialog = screen.getByRole('dialog')
      const confirmBtn = [...dialog.querySelectorAll('button')].find(
        (btn) => btn.textContent.includes('结束修习')
      )
      await user.click(confirmBtn)

      expect(mockEndDialogue).toHaveBeenCalled()
    })

    it('取消结束修习应关闭对话框', async () => {
      const user = userEvent.setup()
      useDialogueStore.setState({ dialogueId: 'dlg_1', status: 'active' })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const endLink = noteSection.querySelector('[class*="endSessionLink"]')
      await user.click(endLink)

      const cancelBtn = await screen.findByRole('button', { name: /继续修习/ })
      await user.click(cancelBtn)

      expect(screen.queryByText('确定要结束本次修习吗？')).not.toBeInTheDocument()
      expect(mockEndDialogue).not.toHaveBeenCalled()
    })
  })
})
