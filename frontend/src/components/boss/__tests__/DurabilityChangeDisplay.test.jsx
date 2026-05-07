import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import DurabilityChangeDisplay from '../DurabilityChangeDisplay'

describe('DurabilityChangeDisplay', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('change为正数时应显示+30格式', () => {
    const { container } = render(<DurabilityChangeDisplay change={30} />)

    expect(screen.getByText('卡牌耐久')).not.toBeNull()
    expect(screen.getByText('+30')).not.toBeNull()
  })

  it('change为负数时应显示-5格式（不带+号）', () => {
    render(<DurabilityChangeDisplay change={-5} />)

    expect(screen.getByText('卡牌耐久')).not.toBeNull()
    expect(screen.getByText('-5')).not.toBeNull()
  })

  it('change为0时应显示0（不带+号）', () => {
    render(<DurabilityChangeDisplay change={0} />)

    expect(screen.getByText('0')).not.toBeNull()
  })

  it('change为null时不应渲染任何内容', () => {
    const { container } = render(<DurabilityChangeDisplay change={null} />)

    expect(container.innerHTML).toBe('')
  })

  it('change为undefined时不应渲染任何内容', () => {
    const { container } = render(<DurabilityChangeDisplay change={undefined} />)

    expect(container.innerHTML).toBe('')
  })

  it('正数变更值应包含positive样式类', () => {
    render(<DurabilityChangeDisplay change={30} />)

    const valueEl = screen.getByText('+30')
    expect(valueEl.className).toContain('positive')
  })

  it('负数变更值应包含negative样式类', () => {
    render(<DurabilityChangeDisplay change={-5} />)

    const valueEl = screen.getByText('-5')
    expect(valueEl.className).toContain('negative')
  })
})
