import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LeetCodeChallenge from '../LeetCodeChallenge'

vi.mock('../../ui/Button/Button', () => ({
  default: ({ children, onClick, disabled, loading, variant, size, fullWidth, ...rest }) => (
    <button onClick={onClick} data-disabled={disabled || loading ? 'true' : undefined} {...rest}>{children}</button>
  ),
}))

const mockQuestion = {
  leetcode_title: '两数之和',
  leetcode_url: 'https://leetcode.cn/problems/two-sum/',
  leetcode_difficulty: 'easy',
  content: '给定一个整数数组，找出和为目标值的两个数',
}

const mockQuestionNoUrl = {
  leetcode_title: '无链接题目',
  content: '这是一道没有链接的题目',
}

describe('LeetCodeChallenge', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应渲染LeetCode标题', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('两数之和')).not.toBeNull()
  })

  it('应渲染LeetCode挑战类型标签', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('LeetCode挑战')).not.toBeNull()
  })

  it('leetcode_url存在时应显示链接', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    const link = screen.getByText('前往 LeetCode 解题 →')
    expect(link).not.toBeNull()
    expect(link.href).toBe('https://leetcode.cn/problems/two-sum/')
    expect(link.target).toBe('_blank')
  })

  it('leetcode_url不存在时不应显示链接', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestionNoUrl} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.queryByText('前往 LeetCode 解题 →')).toBeNull()
  })

  it('点击"我已解决"应调用onSubmit并传递{is_solved:true}', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    await user.click(screen.getByRole('button', { name: /我已解决/ }))

    expect(onSubmit).toHaveBeenCalledWith({ is_solved: true })
  })

  it('点击"暂时放弃"应调用onGiveUp', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    await user.click(screen.getByRole('button', { name: /暂时放弃/ }))

    expect(onGiveUp).toHaveBeenCalledTimes(1)
  })

  it('loading为true时"我已解决"按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={true} />)

    const btn = screen.getByRole('button', { name: /我已解决/ })
    expect(btn.getAttribute('data-disabled')).toBe('true')
  })

  it('loading为true时"暂时放弃"按钮应标记为禁用', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={true} />)

    const btn = screen.getByRole('button', { name: /暂时放弃/ })
    expect(btn.getAttribute('data-disabled')).toBe('true')
  })

  it('leetcode_difficulty为easy时应显示"简单"', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('简单')).not.toBeNull()
  })

  it('leetcode_difficulty为medium时应显示"中等"', () => {
    const mediumQuestion = { ...mockQuestion, leetcode_difficulty: 'medium' }
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mediumQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('中等')).not.toBeNull()
  })

  it('leetcode_difficulty为hard时应显示"困难"', () => {
    const hardQuestion = { ...mockQuestion, leetcode_difficulty: 'hard' }
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={hardQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('困难')).not.toBeNull()
  })

  it('没有leetcode_title时应显示默认标题"LeetCode 挑战"', () => {
    const noTitleQuestion = { content: '测试', leetcode_url: 'https://leetcode.cn' }
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={noTitleQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('LeetCode 挑战')).not.toBeNull()
  })

  it('content存在时应显示题目描述', () => {
    const onSubmit = vi.fn()
    const onGiveUp = vi.fn()
    render(<LeetCodeChallenge question={mockQuestion} onSubmit={onSubmit} onGiveUp={onGiveUp} loading={false} />)

    expect(screen.getByText('给定一个整数数组，找出和为目标值的两个数')).not.toBeNull()
  })
})
