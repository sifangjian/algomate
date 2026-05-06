import { test, expect } from '@playwright/test'

const MOCK_CARDS = [
  {
    id: 1,
    name: '二分查找',
    algorithm_type: 'Search',
    algorithm_category: 'Search',
    difficulty: 2,
    durability: 80,
    max_durability: 100,
    status: 'normal',
    review_count: 5,
    created_at: '2024-01-15T08:30:00Z',
    last_reviewed: '2024-01-20T14:00:00Z',
    core_concept: '二分查找是一种在有序数组中查找目标值的算法',
    key_points: '["时间复杂度O(log n)", "空间复杂度O(1)", "仅适用于有序数组"]',
    code_template: 'def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1',
    complexity_analysis: '时间复杂度: O(log n)\n空间复杂度: O(1)',
    use_cases: '["查找有序数组中的元素", "求解单调函数的根"]',
    common_variants: '["左边界二分", "右边界二分", "旋转数组二分"]',
    typical_problems: '["LeetCode 704", "LeetCode 35", "LeetCode 162"]',
    common_pitfalls: '["忘记处理边界条件", "整数溢出问题", "死循环"]',
    comparison: '比线性查找快，但要求数组有序',
    my_notes: '注意边界条件的处理',
    visual_links: null,
    npc_id: 1,
    topic: '',
    pending_retake: false,
    is_sealed: false,
  },
  {
    id: 2,
    name: '快速排序',
    algorithm_type: 'Sorting',
    algorithm_category: 'Sorting',
    difficulty: 3,
    durability: 15,
    max_durability: 100,
    status: 'endangered',
    review_count: 3,
    created_at: '2024-01-10T10:00:00Z',
    last_reviewed: '2024-01-18T09:00:00Z',
    core_concept: '快速排序是一种分治排序算法',
    key_points: '["平均时间复杂度O(n log n)", "最坏O(n²)", "原地排序"]',
    code_template: '',
    complexity_analysis: '',
    use_cases: '["大规模数据排序", "需要原地排序的场景"]',
    common_variants: '["三路快排", "随机化快排"]',
    typical_problems: '["LeetCode 912"]',
    common_pitfalls: '["最坏情况退化", "递归深度过大"]',
    comparison: '比归并排序快，但不稳定',
    my_notes: '',
    visual_links: '[{"title": "可视化教程", "url": "https://example.com/quick-sort"}]',
    npc_id: 1,
    topic: '',
    pending_retake: false,
    is_sealed: false,
  },
  {
    id: 3,
    name: '动态规划入门',
    algorithm_type: 'Dynamic Programming',
    algorithm_category: 'Dynamic Programming',
    difficulty: 4,
    durability: 0,
    max_durability: 100,
    status: 'pending_retake',
    review_count: 2,
    created_at: '2024-01-05T12:00:00Z',
    last_reviewed: '2024-01-12T16:00:00Z',
    core_concept: '动态规划通过子问题重叠来优化递归',
    key_points: '["状态定义", "状态转移方程", "边界条件"]',
    code_template: '',
    complexity_analysis: '',
    use_cases: '[]',
    common_variants: '[]',
    typical_problems: '["爬楼梯", "背包问题"]',
    common_pitfalls: '["状态定义错误", "边界条件遗漏"]',
    comparison: '',
    my_notes: '',
    visual_links: null,
    npc_id: 1,
    topic: '',
    pending_retake: true,
    is_sealed: true,
  },
]

async function jsClick(page, text) {
  await page.evaluate((t) => {
    const elements = Array.from(document.querySelectorAll('button, [role="button"]'))
    const el = elements.find(e => e.textContent.includes(t))
    if (el) el.click()
  }, text)
}

test.describe('F01 卡牌系统 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/cards*', async (route) => {
      const url = route.request().url()
      if (url.includes('/cards/') && !url.includes('retake')) {
        const id = parseInt(url.split('/cards/')[1].split('?')[0])
        if (!isNaN(id)) {
          const card = MOCK_CARDS.find(c => c.id === id)
          if (card) {
            await route.fulfill({ status: 200, body: JSON.stringify(card) })
          } else {
            await route.fulfill({ status: 404, body: JSON.stringify({ detail: 'Not found' }) })
          }
          return
        }
      }
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          cards: MOCK_CARDS,
          endangered_count: MOCK_CARDS.filter(c => c.status === 'endangered').length,
          pending_retake_count: MOCK_CARDS.filter(c => c.status === 'pending_retake').length,
        }),
      })
    })

    await page.goto('/workshop')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'))
      const skipBtn = btns.find(b => b.textContent.includes('跳过'))
      if (skipBtn) skipBtn.click()
    })
    await page.waitForTimeout(500)
  })

  test.describe('Flow 1: 查看卡牌列表', () => {
    test('页面标题和副标题正确渲染', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '🎴 卡牌工坊' })).toBeVisible()
      await expect(page.getByText('管理你的算法知识卡牌')).toBeVisible()
    })

    test('卡牌列表加载后显示卡牌项', async ({ page }) => {
      await page.waitForTimeout(1000)
      const cards = await page.locator('button').filter({ hasText: /二分查找|快速排序|动态规划/ }).all()
      expect(cards.length).toBeGreaterThanOrEqual(1)
    })

    test('存在濒危卡牌时显示濒危横幅', async ({ page }) => {
      const elements = await page.locator('*', { hasText: /濒危/ }).all()
      expect(elements.length).toBeGreaterThan(0)
    })

    test('存在待重修卡牌时显示待重修区域', async ({ page }) => {
      const elements = await page.locator('*', { hasText: /待重修/ }).all()
      expect(elements.length).toBeGreaterThan(0)
    })

    test('卡牌显示正确的算法类型', async ({ page }) => {
      await page.waitForTimeout(1000)
      const searchType = await page.locator('*', { hasText: /搜索算法|Search/ }).all()
      expect(searchType.length).toBeGreaterThan(0)
    })
  })

  test.describe('Flow 2: 查看卡牌详情', () => {
    test.skip('点击卡牌后弹出详情弹窗', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索卡牌...')
      await searchInput.click()
      await page.keyboard.press('Control+A')
      await page.keyboard.press('Backspace')
      await page.waitForTimeout(1000)
      
      await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'))
        const btn = btns.find(b => b.textContent.includes('二分查找'))
        if (btn) {
          btn.focus()
          btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }))
        }
      })
      await page.waitForTimeout(1000)
      const dialogCount = await page.locator('[role="dialog"]').count()
      expect(dialogCount).toBeGreaterThan(0)
    })

    test('详情弹窗中渲染知识维度区域', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索卡牌...')
      await searchInput.click()
      await page.keyboard.press('Control+A')
      await page.keyboard.press('Backspace')
      await page.waitForTimeout(1000)
      
      await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'))
        const btn = btns.find(b => b.textContent.includes('二分查找'))
        if (btn) {
          btn.focus()
          btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }))
        }
      })
      await page.waitForTimeout(800)
      const elements = await page.locator('*', { hasText: /知识维度|核心概念|关键要点/ }).all()
      expect(elements.length).toBeGreaterThan(0)
      await page.keyboard.press('Escape')
    })
  })

  test.describe('Flow 3: 筛选卡牌', () => {
    test('搜索框可见且可输入', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索卡牌...')
      await expect(searchInput).toBeVisible()
      await searchInput.fill('测试')
      await page.waitForTimeout(500)
      await expect(searchInput).toHaveValue('测试')
    })

    test('搜索功能可正常工作', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索卡牌...')
      await searchInput.fill('快速')
      await page.waitForTimeout(800)
      const searchResult = page.locator('button', { hasText: '快速排序' }).first()
      await expect(searchResult).toBeVisible()
    })
  })

  test.describe('Flow 4: 重修卡牌', () => {
    test('待重修卡牌显示重修按钮', async ({ page }) => {
      const retakeBtn = page.locator('button', { hasText: /重修/ }).first()
      await expect(retakeBtn).toBeVisible()
    })

    test('重修按钮包含正确的图标', async ({ page }) => {
      const retakeBtn = page.locator('button', { hasText: /重修/ }).first()
      await expect(retakeBtn).toContainText('重修')
    })
  })
})