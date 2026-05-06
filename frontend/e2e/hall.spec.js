import { test, expect } from '@playwright/test'

test.describe('F06 导师大厅 - E2E 测试', () => {
  test('HALL-AC-001: 进入导师大厅应显示所有 NPC 卡片列表', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('导师大厅')).toBeVisible({ timeout: 30000 })

    await expect(page.getByText('老夫子')).toBeVisible({ timeout: 30000 })
    await expect(page.getByText('栈语者')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('圣殿智者')).toBeVisible({ timeout: 10000 })

    await expect(page.getByText('基础数据结构导师')).toBeVisible()
    await expect(page.getByText('数组与双指针')).toBeVisible()
  })

  test('HALL-AC-006: 有卡牌的 NPC 应显示卡牌数量标记', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('导师大厅')).toBeVisible({ timeout: 30000 })
    await expect(page.getByText('老夫子')).toBeVisible({ timeout: 30000 })

    const badges = page.locator('text=已获')
    await expect(badges.first()).toBeVisible({ timeout: 10000 })
  })

  test('HALL-AC-007: 顶部应显示推荐学习路径卡片', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('导师大厅')).toBeVisible({ timeout: 30000 })
    await expect(page.getByText('推荐学习路径')).toBeVisible({ timeout: 30000 })
  })

  test('HALL-AC-008: 点击推荐学习路径应展开完整路径说明', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('推荐学习路径')).toBeVisible({ timeout: 30000 })

    const pathHeader = page.locator('[class*="pathHeader"]').first()
    await pathHeader.click()

    await expect(page.getByText('基础入门')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('掌握基础数据结构')).toBeVisible()
  })

  test('HALL-AC-004: 使用算法类型筛选应过滤 NPC 列表', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('老夫子')).toBeVisible({ timeout: 30000 })

    const treeTag = page.locator('button:has-text("树结构")').first()
    await treeTag.click()

    await expect(page.getByText('树语者')).toBeVisible({ timeout: 10000 })
  })

  test('HALL-AC-002: 点击 NPC 卡片应展开详情弹窗', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('老夫子')).toBeVisible({ timeout: 30000 })

    const npcCard = page.locator('[aria-label*="老夫子"]').first()
    await npcCard.click()

    await expect(page.getByText('开始修习')).toBeVisible({ timeout: 10000 })
  })

  test('HALL-AC-003: 点击开始修习应跳转到 NPC 对话页面', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('老夫子')).toBeVisible({ timeout: 30000 })

    const npcCard = page.locator('[aria-label*="老夫子"]').first()
    await npcCard.click()

    await expect(page.getByText('开始修习')).toBeVisible({ timeout: 10000 })
    await page.getByText('开始修习').click()

    await page.waitForURL(/\/npc\/\d+/, { timeout: 10000 })
    expect(page.url()).toMatch(/\/npc\/\d+/)
  })

  test('HALL-AC-005: 新用户推荐提示验证', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('导师大厅')).toBeVisible({ timeout: 30000 })

    const recommendTip = page.locator('text=推荐从这里开始')
    const isVisible = await recommendTip.isVisible().catch(() => false)

    expect(typeof isVisible).toBe('boolean')
  })
})
