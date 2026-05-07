import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import NoWeaknessHint from '../NoWeaknessHint'

describe('NoWeaknessHint', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应显示警告图标', () => {
    render(<NoWeaknessHint />)

    expect(screen.getByText('⚠️')).not.toBeNull()
  })

  it('应显示无弱点提示文字', () => {
    render(<NoWeaknessHint />)

    expect(screen.getByText('你没有此Boss弱点类型的卡牌，使用其他卡牌挑战将更困难')).not.toBeNull()
  })
})
