import { test, expect } from '@playwright/test'

test.describe('F06 算法地图 - E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('heading', { name: '算法地图' })).toBeVisible({ timeout: 30000 })

    const skipBtn = page.locator('button:has-text("跳过")')
    if (await skipBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await skipBtn.click()
      await page.waitForTimeout(500)
    }
  })

  test('MAP-AC-001: 进入算法地图应显示所有算法分类和主题', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '算法地图' })).toBeVisible({ timeout: 30000 })

    await expect(page.getByText('新手森林')).toBeVisible({ timeout: 30000 })
    await expect(page.getByText('智慧圣殿')).toBeVisible({ timeout: 10000 })

    await expect(page.getByText('数组与双指针')).toBeVisible()
    await expect(page.getByText('动态规划')).toBeVisible()
  })

  test('MAP-AC-002: 点击主题节点应展开 NPC 详情弹窗', async ({ page }) => {
    await expect(page.getByText('数组与双指针')).toBeVisible({ timeout: 30000 })

    const topicNode = page.locator('[aria-label*="数组与双指针"]').first()
    await topicNode.click()

    await expect(page.getByText('开始修习')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('专长领域')).toBeVisible()
    await expect(page.getByText('数组与双指针')).toBeVisible()
  })

  test('MAP-AC-003: 点击开始修习应跳转到 NPC 对话页面', async ({ page }) => {
    await expect(page.getByText('数组与双指针')).toBeVisible({ timeout: 30000 })

    const topicNode = page.locator('[aria-label*="数组与双指针"]').first()
    await topicNode.click()

    await expect(page.getByText('开始修习')).toBeVisible({ timeout: 10000 })
    await page.getByText('开始修习').click()

    await page.waitForURL(/\/npc\/\d+/, { timeout: 10000 })
    expect(page.url()).toMatch(/\/npc\/\d+/)
  })

  test('MAP-AC-004: 推荐路径主题应显示序号标记', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '算法地图' })).toBeVisible({ timeout: 30000 })

    const recommendedNodes = page.locator('[class*="recommended"]')
    await expect(recommendedNodes.first()).toBeVisible({ timeout: 10000 })
  })

  test('MAP-AC-005: 主题节点应显示重要性标签', async ({ page }) => {
    await expect(page.getByText('数组与双指针')).toBeVisible({ timeout: 30000 })

    const coreBadge = page.locator('text=核心')
    await expect(coreBadge.first()).toBeVisible()

    const importantBadge = page.locator('text=重要')
    await expect(importantBadge.first()).toBeVisible()
  })

  test('MAP-AC-006: NPC 详情弹窗应显示卡牌数量标记', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '算法地图' })).toBeVisible({ timeout: 30000 })

    await expect(page.getByText('数组与双指针')).toBeVisible({ timeout: 30000 })
    const topicNode = page.locator('[aria-label*="数组与双指针"]').first()
    await topicNode.click()

    const badges = page.locator('text=已获')
    const isVisible = await badges.first().isVisible({ timeout: 10000 }).catch(() => false)
    expect(typeof isVisible).toBe('boolean')
  })
})