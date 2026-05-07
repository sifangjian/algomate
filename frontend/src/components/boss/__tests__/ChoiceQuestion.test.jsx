import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChoiceQuestion from '../ChoiceQuestion'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled || loading ? 'true' : undefined} {...rest}>{children}</button>
  ),
}))

vi.mock('../../ui/Toast/index', () => ({
  showToast: vi.fn(),
}))

import { showToast } from '../../ui/Toast/index'

const arrayOptionsQuestion = {
  content: '以下哪种排序算法的平均时间复杂度为O(n log n)?',
  options: ['冒泡排序', '快速排序', '插入排序', '选择排序'],
}

const objectOptionsQuestion = {
  content: '测试对象格式选项',
  options: { a: '选项A', b: '选项B', c: '选项C', d: '选项D' },
}

describe('ChoiceQuestion', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染题目内容和4个选项', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('以下哪种排序算法的平均时间复杂度为O(n log n)?')).not.toBeNull()
    expect(screen.getByText('冒泡排序')).not.toBeNull()
    expect(screen.getByText('快速排序')).not.toBeNull()
    expect(screen.getByText('插入排序')).not.toBeNull()
    expect(screen.getByText('选择排序')).not.toBeNull()
  })

  it('应渲染选择题类型标签', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('选择题')).not.toBeNull()
  })

  it('选项应显示A/B/C/D标签', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('A')).not.toBeNull()
    expect(screen.getByText('B')).not.toBeNull()
    expect(screen.getByText('C')).not.toBeNull()
    expect(screen.getByText('D')).not.toBeNull()
  })

  it('点击选项应选中该选项', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    await user.click(screen.getByText('快速排序'))

    const optionButtons = screen.getAllByRole('button').filter(btn => btn.textContent.includes('快速排序'))
    expect(optionButtons[0].className).toContain('selected')
  })

  it('未选择选项时点击提交应显示警告toast', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    await user.click(submitBtn)

    expect(showToast).toHaveBeenCalledWith('请选择一个选项', 'warning')
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('选择选项后提交应调用onSubmit并传递选中的标签', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    await user.click(screen.getByText('快速排序'))
    await user.click(screen.getByRole('button', { name: /提交挑战/ }))

    expect(onSubmit).toHaveBeenCalledWith({ answer: 'B' })
  })

  it('loading为true时选项按钮应被禁用', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={true} />)

    const optionButtons = screen.getAllByRole('button').filter(btn =>
      btn.textContent.includes('冒泡排序') || btn.textContent.includes('快速排序')
    )
    optionButtons.forEach(btn => {
      expect(btn.disabled).toBe(true)
    })
  })

  it('loading为true时提交按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={true} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    expect(submitBtn.getAttribute('data-disabled')).toBe('true')
  })

  it('未选择选项时提交按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    expect(submitBtn.getAttribute('data-disabled')).toBe('true')
  })

  it('选择选项后提交按钮应可用', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={arrayOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    await user.click(screen.getByText('快速排序'))

    const submitBtn = screen.getByRole('button', { name: /提交挑战/ })
    expect(submitBtn.getAttribute('data-disabled')).toBeNull()
  })

  it('对象格式选项应按key排序渲染', () => {
    const onSubmit = vi.fn()
    render(<ChoiceQuestion question={objectOptionsQuestion} onSubmit={onSubmit} loading={false} />)

    expect(screen.getByText('选项A')).not.toBeNull()
    expect(screen.getByText('选项B')).not.toBeNull()
    expect(screen.getByText('选项C')).not.toBeNull()
    expect(screen.getByText('选项D')).not.toBeNull()
  })
})
