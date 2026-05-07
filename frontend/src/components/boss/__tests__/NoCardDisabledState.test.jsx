import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NoCardDisabledState from '../NoCardDisabledState'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled || loading ? 'true' : undefined} {...rest}>{children}</button>
  ),
}))

describe('NoCardDisabledState', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应显示提示文字"需要至少1张卡牌才能挑战Boss"', () => {
    const onGoPractice = vi.fn()
    render(<NoCardDisabledState onGoPractice={onGoPractice} />)

    expect(screen.getByText('需要至少1张卡牌才能挑战Boss')).not.toBeNull()
  })

  it('应显示卡牌图标', () => {
    const onGoPractice = vi.fn()
    render(<NoCardDisabledState onGoPractice={onGoPractice} />)

    expect(screen.getByText('🎴')).not.toBeNull()
  })

  it('点击"前往修习"按钮应触发onGoPractice', async () => {
    const user = userEvent.setup()
    const onGoPractice = vi.fn()
    render(<NoCardDisabledState onGoPractice={onGoPractice} />)

    await user.click(screen.getByRole('button', { name: /前往修习/ }))

    expect(onGoPractice).toHaveBeenCalledTimes(1)
  })
})
