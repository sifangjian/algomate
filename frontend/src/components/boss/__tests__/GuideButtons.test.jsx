import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import GuideButtons from '../GuideButtons'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled || loading ? 'true' : undefined} {...rest}>{children}</button>
  ),
}))

describe('GuideButtons', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染"继续挑战"和"去修炼"两个按钮', () => {
    const onContinue = vi.fn()
    const onGoPractice = vi.fn()
    render(<GuideButtons onContinue={onContinue} onGoPractice={onGoPractice} />)

    expect(screen.getByRole('button', { name: /继续挑战/ })).not.toBeNull()
    expect(screen.getByRole('button', { name: /去修炼/ })).not.toBeNull()
  })

  it('点击"继续挑战"应触发onContinue', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    const onGoPractice = vi.fn()
    render(<GuideButtons onContinue={onContinue} onGoPractice={onGoPractice} />)

    await user.click(screen.getByRole('button', { name: /继续挑战/ }))

    expect(onContinue).toHaveBeenCalledTimes(1)
    expect(onGoPractice).not.toHaveBeenCalled()
  })

  it('点击"去修炼"应触发onGoPractice', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    const onGoPractice = vi.fn()
    render(<GuideButtons onContinue={onContinue} onGoPractice={onGoPractice} />)

    await user.click(screen.getByRole('button', { name: /去修炼/ }))

    expect(onGoPractice).toHaveBeenCalledTimes(1)
    expect(onContinue).not.toHaveBeenCalled()
  })
})
