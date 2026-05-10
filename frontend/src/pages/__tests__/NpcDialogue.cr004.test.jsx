import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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

async function waitForDialogueReady() {
  await waitFor(() => {
    expect(useDialogueStore.getState().status).toBe('active')
    expect(useDialogueStore.getState().dialogueId).toBeTruthy()
  })
}

describe('NpcDialogue - CR-004 变更', () => {
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

  describe('CR-004-T01: header 中添加"结束修习"按钮', () => {
    it('页面 header 右侧应有"结束修习"按钮', async () => {
      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })
      await waitForDialogueReady()

      const endBtn = screen.getByRole('button', { name: /结束修习/ })
      expect(endBtn).toBeTruthy()

      const header = endBtn.closest('[class*="header"]')
      expect(header).toBeTruthy()
      expect(header.className).not.toContain('headerLeft')
    })

    it('点击 header "结束修习"按钮应弹出确认对话框"确定要结束本次修习吗？"', async () => {
      const user = userEvent.setup()

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })
      await waitForDialogueReady()

      const endBtn = screen.getByRole('button', { name: /结束修习/ })
      await user.click(endBtn)

      expect(await screen.findByText('确定要结束本次修习吗？')).toBeInTheDocument()
    })

    it('确认结束修习应自动保存笔记并触发 endDialogue', async () => {
      const user = userEvent.setup()

      mockSaveNote.mockResolvedValue({ data: { saved: true, note_id: 1, saved_at: '2026-05-10T10:00:00' } })
      mockEndDialogue.mockResolvedValue({
        data: { card: { id: 1, name: '二分查找' }, is_update: false, guides: { go_boss: true, go_workshop: true } },
      })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })
      await waitForDialogueReady()

      const noteEditor = screen.getByLabelText('修炼日记编辑器')
      await user.type(noteEditor, '二分查找的心得体会')

      const endBtn = screen.getByRole('button', { name: /结束修习/ })
      await user.click(endBtn)

      await screen.findByText('确定要结束本次修习吗？')
      const dialog = screen.getByRole('dialog')
      const confirmBtn = [...dialog.querySelectorAll('button')].find(
        (btn) => btn.textContent.includes('结束修习') && !btn.textContent.includes('本次')
      )
      await user.click(confirmBtn)

      await waitFor(() => {
        expect(mockSaveNote).toHaveBeenCalledWith('dlg_1', '二分查找的心得体会')
        expect(mockEndDialogue).toHaveBeenCalled()
      })
    })

    it('无笔记时确认结束修习应直接触发 endDialogue（不调用 saveNote）', async () => {
      const user = userEvent.setup()

      mockEndDialogue.mockResolvedValue({
        data: { card: { id: 1, name: '二分查找' }, is_update: false, guides: { go_boss: true, go_workshop: true } },
      })

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })
      await waitForDialogueReady()

      const endBtn = screen.getByRole('button', { name: /结束修习/ })
      await user.click(endBtn)

      await screen.findByText('确定要结束本次修习吗？')
      const dialog = screen.getByRole('dialog')
      const confirmBtn = [...dialog.querySelectorAll('button')].find(
        (btn) => btn.textContent.includes('结束修习') && !btn.textContent.includes('本次')
      )
      await user.click(confirmBtn)

      await waitFor(() => {
        expect(mockEndDialogue).toHaveBeenCalled()
      })
      expect(mockSaveNote).not.toHaveBeenCalled()
    })

    it('取消确认应关闭对话框，留在对话页面', async () => {
      const user = userEvent.setup()

      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })
      await waitForDialogueReady()

      const endBtn = screen.getByRole('button', { name: /结束修习/ })
      await user.click(endBtn)

      const cancelBtn = await screen.findByRole('button', { name: /继续修习/ })
      await user.click(cancelBtn)

      expect(screen.queryByText('确定要结束本次修习吗？')).not.toBeInTheDocument()
      expect(mockEndDialogue).not.toHaveBeenCalled()
    })
  })

  describe('CR-004-T02: 移除笔记区域的"保存心得"按钮和"结束修习"链接', () => {
    it('笔记区域不应存在"保存心得"按钮', async () => {
      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const saveBtn = [...noteSection.querySelectorAll('button')].find(
        (btn) => btn.textContent.includes('保存心得')
      )
      expect(saveBtn).toBeUndefined()
    })

    it('笔记区域不应存在"结束修习"链接', async () => {
      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      const noteSection = screen.getByLabelText('修炼日记区域')
      const endLink = noteSection.querySelector('[class*="endSessionLink"]')
      expect(endLink).toBeNull()
    })

    it('不应出现"心得已保存"选择对话框（showSaveNoteChoice）', async () => {
      renderNpcDialogue()
      await screen.findByText('老夫子', { selector: 'h2' })

      expect(screen.queryByText('心得已保存')).not.toBeInTheDocument()
      expect(screen.queryByText(/是否结束修习生成卡牌/)).not.toBeInTheDocument()
    })
  })
})
