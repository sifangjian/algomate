import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ShortAnswerQuestion from '../ShortAnswerQuestion'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled || loading ? 'true' : undefined} {...rest}>{children}</button>
  ),
}))

vi.mock('../../ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

import { showToast } from '../../ui/Toast/index'

const mockQuestion = {
  content: '请解释什么是动态规划?',
}

describe('ShortAnswerQuestion', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染题目内容和textarea', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('请解释什么是动态规划?')).not.toBeNull()
    expect(screen.getByPlaceholderText('请输入你的答案...')).not.toBeNull()
  })

  it('应渲染简答题类型标签', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('简答题')).not.toBeNull()
  })

  it('输入答案应更新字数统计', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const textarea = screen.getByPlaceholderText('请输入你的答案...')
    await user.type(textarea, '动态规划是一种算法思想')

    expect(screen.getByText((text) => text.includes('11/2000'))).not.toBeNull()
  })

  it('初始字数统计应为0/2000', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('0/2000')).not.toBeNull()
  })

  it('空答案提交应显示警告toast', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    await user.click(submitBtn)

    expect(showToast).toHaveBeenCalledWith('请输入答案', 'warning')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('仅输入空格提交应显示警告toast', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const textarea = screen.getByPlaceholderText('请输入你的答案...')
    await user.type(textarea, '   ')
    await user.click(screen.getByRole('button', { name: /提交挑战/ }))

    expect(showToast).toHaveBeenCalledWith('请输入答案', 'warning')
  })

  it('输入答案后提交应调用onSubmit并传递trim后的答案', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const textarea = screen.getByPlaceholderText('请输入你的答案...')
    await user.type(textarea, '动态规划是一种算法思想')
    await user.click(screen.getByRole('button', { name: /提交挑战/ }))

    expect(onSubmit).toHaveBeenCalledWith({ answer: '动态规划是一种算法思想' })
  })

  it('提交时答案应被trim', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const textarea = screen.getByPlaceholderText('请输入你的答案...')
    await user.type(textarea, '  答案  ')
    await user.click(screen.getByRole('button', { name: /提交挑战/ }))

    expect(onSubmit).toHaveBeenCalledWith({ answer: '答案' })
  })

  it('输入超过2000字应被截断', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const textarea = screen.getByPlaceholderText('请输入你的答案...')
    const longText = 'a'.repeat(2005)
    fireEvent.change(textarea, { target: { value: longText } })

    expect(textarea.value.length).toBe(2000)
    expect(screen.getByText((text) => text.includes('2000/2000'))).not.toBeNull()
  })

  it('loading为true时textarea应被禁用', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={true} />)

    expect(screen.getByPlaceholderText('请输入你的答案...').disabled).toBe(true)
  })

  it('loading为true时提交按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={true} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    expect(submitBtn.getAttribute('data-disabled')).toBe('true')
  })

  it('未输入答案时提交按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    render(<ShortAnswerQuestion question={mockQuestion} onSubmit={onSubmit} loading={false} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    expect(submitBtn.getAttribute('data-disabled')).toBe('true')
  })
})
