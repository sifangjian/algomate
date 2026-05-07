import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import BossDetailPanel from '../BossDetailPanel'

const mockBoss = {
  id: 1,
  name: '排序巨龙',
  difficulty: 'hard',
  weakness_type: 'dynamic_programming',
  description: '这是一只擅长排序算法的巨龙',
}

const mockBossNoDesc = {
  id: 2,
  name: '数组小兵',
  difficulty: 'easy',
  weakness_type: 'basic_data_structure',
}

describe('BossDetailPanel', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('boss为null时不应渲染任何内容', () => {
    const { container } = render(<BossDetailPanel boss={null} />)

    expect(container.innerHTML).toBe('')
  })

  it('boss为undefined时不应渲染任何内容', () => {
    const { container } = render(<BossDetailPanel boss={undefined} />)

    expect(container.innerHTML).toBe('')
  })

  it('应渲染Boss名称', () => {
    render(<BossDetailPanel boss={mockBoss} />)

    expect(screen.getByText('排序巨龙')).not.toBeNull()
  })

  it('应渲染难度标签和星级', () => {
    render(<BossDetailPanel boss={mockBoss} />)

    expect(screen.getByText('高级')).not.toBeNull()
    expect(screen.getByText('★★★')).not.toBeNull()
  })

  it('应渲染弱点属性', () => {
    render(<BossDetailPanel boss={mockBoss} />)

    expect(screen.getByText('弱点属性')).not.toBeNull()
    expect(screen.getByText('动态规划')).not.toBeNull()
  })

  it('有description时应显示描述', () => {
    render(<BossDetailPanel boss={mockBoss} />)

    expect(screen.getByText('这是一只擅长排序算法的巨龙')).not.toBeNull()
  })

  it('没有description时不应显示描述', () => {
    render(<BossDetailPanel boss={mockBossNoDesc} />)

    expect(screen.queryByText('这是一只擅长排序算法的巨龙')).toBeNull()
  })

  it('easy难度应渲染1颗实星', () => {
    render(<BossDetailPanel boss={mockBossNoDesc} />)

    expect(screen.getByText('★☆☆')).not.toBeNull()
    expect(screen.getByText('初级')).not.toBeNull()
  })

  it('弱点类型不在映射中时应显示原始类型值', () => {
    const bossWithUnknownType = { id: 3, name: '未知Boss', difficulty: 'medium', weakness_type: 'unknown_type' }
    render(<BossDetailPanel boss={bossWithUnknownType} />)

    expect(screen.getByText('unknown_type')).not.toBeNull()
  })

  it('应渲染难度对应的emoji', () => {
    render(<BossDetailPanel boss={mockBoss} />)

    expect(screen.getByText('🔴')).not.toBeNull()
  })
})
