import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import NpcCard from '../../hall/NpcCard'

vi.mock('../../../stores/hallStore', () => ({
  useHallStore: vi.fn(() => ({
    setSelectedNpc: vi.fn(),
  })),
}))

describe('NpcCard - 老夫子高亮推荐 (F08-T009)', () => {
  const laofuziNpc = {
    id: 'novice_forest',
    name: '老夫子',
    title: '基础算法导师',
    avatar: '🧙',
    specialties: ['排序', '搜索'],
    card_count: 0,
  }

  const otherNpc = {
    id: 'advanced_master',
    name: '张三丰',
    title: '高级算法导师',
    avatar: '⚔️',
    specialties: ['动态规划', '贪心'],
    card_count: 5,
  }

  it('shows golden border and recommend tip for 老夫子 when isNewUser is true', () => {
    render(<NpcCard npc={laofuziNpc} isNewUser={true} />)

    const card = screen.getByRole('button', { name: /老夫子/ })
    expect(card).toHaveAttribute('data-npc-name', '老夫子')
    expect(card.className).toContain('recommended')
    expect(screen.getByText('推荐新手从这里开始')).toBeInTheDocument()
  })

  it('does not show recommend tip for 老夫子 when isNewUser is false', () => {
    render(<NpcCard npc={laofuziNpc} isNewUser={false} />)

    const card = screen.getByRole('button', { name: /老夫子/ })
    expect(card.className).not.toContain('recommended')
    expect(screen.queryByText('推荐新手从这里开始')).not.toBeInTheDocument()
  })

  it('does not show recommend tip for other NPCs even when isNewUser is true', () => {
    render(<NpcCard npc={otherNpc} isNewUser={true} />)

    const card = screen.getByRole('button', { name: /张三丰/ })
    expect(card.className).not.toContain('recommended')
    expect(screen.queryByText('推荐新手从这里开始')).not.toBeInTheDocument()
  })

  it('has data-npc-name attribute for spotlight targeting', () => {
    render(<NpcCard npc={laofuziNpc} isNewUser={true} />)

    const card = screen.getByRole('button', { name: /老夫子/ })
    expect(card).toHaveAttribute('data-npc-name', '老夫子')
  })

  it('all NPC cards have data-npc-name attribute', () => {
    render(<NpcCard npc={otherNpc} isNewUser={false} />)

    const card = screen.getByRole('button', { name: /张三丰/ })
    expect(card).toHaveAttribute('data-npc-name', '张三丰')
  })
})
