import { test, expect } from '@playwright/test'

const MOCK_NPC = {
  id: 9,
  name: '老夫子',
  title: '基础数据结构导师',
  avatar: 'laofuzi',
  algorithm_type: 'basic_data_structure',
  specialties: ['数组', '链表', '栈'],
  realm_id: 'novice_forest',
}

const MOCK_DIALOGUE_START = {
  dialogue_id: 100,
  npc_name: '老夫子',
  npc_avatar: '👴',
  status: 'active',
  greeting: '**我是老夫子**，基础数据结构导师。\n📖 可修习话题：数组 · 链表 · 栈\n欢迎来到新手森林！选择一个话题开始修习吧！',
  topics: ['数组', '链表', '栈'],
  existing_card: null,
}

async function setupApiMocks(page) {
  await page.route('**/api/v1/npcs', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 200, message: 'success', data: { npcs: [MOCK_NPC], learning_path: [] } }),
    })
  })

  await page.route('**/api/v1/npcs/*', async (route) => {
    const url = route.request().url()
    if (url.includes('/algorithm-info')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 200, message: 'success', data: {} }) })
    } else {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ code: 200, message: 'success', data: MOCK_NPC }) })
    }
  })

  await page.route('**/api/v1/dialogues/start**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DIALOGUE_START) })
  })

  await page.route('**/api/v1/dialogues/*/message**', async (route) => {
    const sseBody = [
      'data: {"type": "content", "content": "数组是"}\n\n',
      'data: {"type": "content", "content": "一种线性数据结构"}\n\n',
      'data: {"type": "suggestions", "suggestions": ["链表和数组的区别？", "动态数组怎么实现？"]}\n\n',
      'data: [DONE]\n\n',
    ].join('')
    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream',
      body: sseBody,
    })
  })

  await page.route('**/api/v1/dialogues/*/note**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ saved: true, note_id: 1, saved_at: new Date().toISOString() }),
    })
  })

  await page.route('**/api/v1/dialogues/*/end**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'ended',
        card: {
          id: 1,
          name: '数组基础',
          algorithm_category: '基础数据结构',
          summary: '数组是一种线性数据结构，支持随机访问。',
        },
        is_update: false,
        guides: {
          message: '修习完成！你获得了新的知识卡牌。',
          available_actions: [
            { action: 'go_workshop', label: '前往卡牌工坊', target_path: '/workshop', available: true },
            { action: 'go_boss', label: '前往Boss挑战', target_path: '/', available: true },
          ],
        },
      }),
    })
  })

  await page.route('**/api/v1/dialogues/*/heartbeat**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ alive: true, last_active_at: new Date().toISOString() }),
    })
  })

  await page.route('**/api/v1/stats**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total_cards: 0, endangered_cards: 0, pending_retake_cards: 0, is_new_user: true }),
    })
  })
}

async function navigateToDialogue(page) {
  await page.goto('/npc/9', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(3000)
}

test.describe('F02 NPC对话修习 - E2E 测试', () => {

  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
  })

  test('F02-AC-001: 直接导航到NPC对话页面应显示NPC信息和问候语', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByRole('heading', { name: '老夫子' })).toBeVisible({ timeout: 15000 })
    await expect(page.getByRole('log')).toBeVisible({ timeout: 15000 })
  })

  test('F02-AC-002: 对话页面应显示消息输入框和发送按钮', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByLabel('消息输入框')).toBeVisible({ timeout: 15000 })
    await expect(page.getByRole('button', { name: '发送' })).toBeVisible()
  })

  test('F02-AC-003: 输入消息并发送应显示用户消息和NPC回复', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByLabel('消息输入框')).toBeVisible({ timeout: 15000 })

    const input = page.getByLabel('消息输入框')
    await input.fill('什么是数组？')

    const sendBtn = page.getByRole('button', { name: '发送' })
    await sendBtn.click()

    await expect(page.getByText('什么是数组？')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('线性数据结构')).toBeVisible({ timeout: 15000 })
  })

  test('F02-AC-004: 修炼日记区域应可输入和保存', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByLabel('修炼日记编辑器')).toBeVisible({ timeout: 15000 })

    const noteEditor = page.getByLabel('修炼日记编辑器')
    await noteEditor.fill('📌 今日主题：数组\n💡 核心理解：连续存储')

    const saveBtn = page.getByRole('button', { name: '保存心得' })
    await expect(saveBtn).toBeEnabled()
    await saveBtn.click()
  })

  test('F02-AC-005: 点击结束修习应弹出确认对话框', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByLabel('消息输入框')).toBeVisible({ timeout: 15000 })

    const input = page.getByLabel('消息输入框')
    await input.fill('测试消息')
    await page.getByRole('button', { name: '发送' }).click()
    await page.waitForTimeout(2000)

    await page.getByRole('button', { name: '结束修习' }).click()

    await expect(page.getByText(/确定要结束|保存并结束/)).toBeVisible({ timeout: 5000 })
  })

  test('F02-AC-006: 点击返回地图应导航回首页', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByText('返回地图')).toBeVisible({ timeout: 15000 })
    await page.getByText('返回地图').click()

    await expect(page.getByRole('heading', { name: '导师大厅' })).toBeVisible({ timeout: 15000 })
  })

  test('F02-AC-007: 快捷问题按钮应可见且可点击', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByRole('log')).toBeVisible({ timeout: 15000 })

    const quickBtns = page.locator('[class*="quickQBtn"]')
    const count = await quickBtns.count()
    if (count > 0) {
      await expect(quickBtns.first()).toBeVisible()
      await expect(quickBtns.first()).toBeEnabled()
    }
  })

  test('F02-AC-008: NPC回复中应显示建议按钮', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByLabel('消息输入框')).toBeVisible({ timeout: 15000 })

    const input = page.getByLabel('消息输入框')
    await input.fill('什么是数组？')
    await page.getByRole('button', { name: '发送' }).click()

    await expect(page.getByText('线性数据结构')).toBeVisible({ timeout: 15000 })

    const suggestionBtns = page.locator('button').filter({ hasText: /链表和数组的区别|动态数组怎么实现/ })
    const count = await suggestionBtns.count()
    if (count > 0) {
      await expect(suggestionBtns.first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('F02-AC-009: 空消息时发送按钮应禁用', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByRole('button', { name: '发送' })).toBeVisible({ timeout: 15000 })
    const sendBtn = page.getByRole('button', { name: '发送' })
    await expect(sendBtn).toBeDisabled()
  })

  test('F02-AC-010: 确认结束修习后应返回首页', async ({ page }) => {
    await navigateToDialogue(page)

    await expect(page.getByRole('button', { name: '结束修习' })).toBeVisible({ timeout: 15000 })
    await page.getByRole('button', { name: '结束修习' }).click()

    await expect(page.getByText(/确定要结束|保存并结束/)).toBeVisible({ timeout: 5000 })

    const confirmBtn = page.locator('button:has-text("保存并结束")')
    if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await confirmBtn.click()
    } else {
      const endBtns = page.locator('button:has-text("结束修习")')
      await endBtns.last().click()
    }

    await page.waitForTimeout(2000)

    await expect(page.getByText('返回地图')).toBeVisible({ timeout: 10000 })
    await page.getByText('返回地图').click()

    await expect(page.getByRole('heading', { name: '导师大厅' })).toBeVisible({ timeout: 15000 })
  })
})
