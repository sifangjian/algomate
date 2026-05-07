import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SelectableCard from '../SelectableCard'

const mockCard = {
  name: '二叉搜索树',
  algorithm_type: 'tree',
  durability: 80,
  max_durability: 100,
}

const mockLowDurCard = {
  name: '哈希表',
  algorithm_type: 'basic_data_structure',
  durability: 20,
  max_durability: 100,
}

describe('SelectableCard', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染卡牌名称、算法类型和耐久度', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.getByText('二叉搜索树')).not.toBeNull()
    expect(screen.getByText('tree')).not.toBeNull()
    expect(screen.getByText(/耐久 80\/100/)).not.toBeNull()
  })

  it('isWeakness为true时应显示"弱点"标签', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={true} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.getByText('弱点')).not.toBeNull()
  })

  it('isWeakness为false时不应显示"弱点"标签', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.queryByText('弱点')).toBeNull()
  })

  it('点击应触发onSelect回调', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('loading为true时点击不应触发onSelect', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={true} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('loading为true时tabIndex应为-1', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={true} />)

    expect(screen.getByRole('button').tabIndex).toBe(-1)
  })

  it('loading为false时tabIndex应为0', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.getByRole('button').tabIndex).toBe(0)
  })

  it('selected为true时容器应包含selected样式类', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={true} onSelect={onSelect} loading={false} />)

    expect(screen.getByRole('button').className).toContain('selected')
  })

  it('isWeakness为true时容器应包含weakness样式类', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={true} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.getByRole('button').className).toContain('weakness')
  })

  it('loading为true时容器应包含disabled样式类', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={true} />)

    expect(screen.getByRole('button').className).toContain('disabled')
  })

  it('键盘Enter应触发onSelect回调', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it('loading为true时键盘Enter不应触发onSelect', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={true} />)

    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' })
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('max_durability未提供时默认为100', () => {
    const cardNoMax = { name: '测试卡', algorithm_type: 'tree', durability: 50 }
    const onSelect = vi.fn()
    render(<SelectableCard card={cardNoMax} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    expect(screen.getByText(/耐久 50\/100/)).not.toBeNull()
  })

  it('耐久度百分比应正确计算并设置进度条宽度', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    const durFill = screen.getByRole('button').querySelector('[class*="durFill"]')
    expect(durFill).not.toBeNull()
    expect(durFill.style.width).toBe('80%')
  })

  it('低耐久度卡牌进度条宽度应正确', () => {
    const onSelect = vi.fn()
    render(<SelectableCard card={mockLowDurCard} isWeakness={false} selected={false} onSelect={onSelect} loading={false} />)

    const durFill = screen.getByRole('button').querySelector('[class*="durFill"]')
    expect(durFill.style.width).toBe('20%')
  })
})
