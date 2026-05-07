import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import BossCard from '../BossCard'

const mockBoss = {
  id: 1,
  name: '排序巨龙',
  difficulty: 'hard',
  weakness_type: 'dynamic_programming',
}

const mockEasyBoss = {
  id: 2,
  name: '数组小兵',
  difficulty: 'easy',
  weakness_type: 'basic_data_structure',
}

describe('BossCard', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染Boss名称、难度星级和弱点类型', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    expect(screen.getByText('排序巨龙')).not.toBeNull()
    expect(screen.getByText('★★★')).not.toBeNull()
    expect(screen.getByText('高级')).not.toBeNull()
    expect(screen.getByText(/动态规划/)).not.toBeNull()
  })

  it('应根据easy难度渲染1颗实星和2颗空星', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockEasyBoss} selected={false} onSelect={onSelect} />)

    expect(screen.getByText('★☆☆')).not.toBeNull()
    expect(screen.getByText('初级')).not.toBeNull()
  })

  it('点击应触发onSelect回调', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('键盘Enter应触发onSelect回调', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('键盘Space应触发onSelect回调', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' })
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('键盘其他按键不应触发onSelect', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Tab' })
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('selected为true时容器应包含selected样式类', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={true} onSelect={onSelect} />)

    const card = screen.getByRole('button')
    expect(card.className).toContain('selected')
  })

  it('selected为false时容器不应包含selected样式类', () => {
    const onSelect = vi.fn()
    render(<BossCard boss={mockBoss} selected={false} onSelect={onSelect} />)

    const card = screen.getByRole('button')
    expect(card.className).not.toContain('selected')
  })

  it('弱点类型不在映射中时应显示原始类型值', () => {
    const bossWithUnknownType = { id: 3, name: '未知Boss', difficulty: 'medium', weakness_type: 'unknown_type' }
    const onSelect = vi.fn()
    render(<BossCard boss={bossWithUnknownType} selected={false} onSelect={onSelect} />)

    expect(screen.getByText(/unknown_type/)).not.toBeNull()
  })
})
