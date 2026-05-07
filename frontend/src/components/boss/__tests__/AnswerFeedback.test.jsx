import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import AnswerFeedback from '../AnswerFeedback'

describe('AnswerFeedback', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('result为null时不应渲染任何内容', () => {
    const { container } = render(<AnswerFeedback result={null} />)

    expect(container.innerHTML).toBe('')
  })

  it('result为undefined时不应渲染任何内容', () => {
    const { container } = render(<AnswerFeedback result={undefined} />)

    expect(container.innerHTML).toBe('')
  })

  it('有feedback时应显示"错误分析"标题和内容', () => {
    const result = { feedback: '你忽略了边界条件' }
    render(<AnswerFeedback result={result} />)

    expect(screen.getByText('错误分析')).not.toBeNull()
    expect(screen.getByText('你忽略了边界条件')).not.toBeNull()
  })

  it('有improvement时应显示"改进建议"标题和内容', () => {
    const result = { improvement: '建议先画出状态转移图' }
    render(<AnswerFeedback result={result} />)

    expect(screen.getByText('改进建议')).not.toBeNull()
    expect(screen.getByText('建议先画出状态转移图')).not.toBeNull()
  })

  it('有explanation时应显示"正确解析"标题和内容', () => {
    const result = { explanation: '动态规划的核心是最优子结构' }
    render(<AnswerFeedback result={result} />)

    expect(screen.getByText('正确解析')).not.toBeNull()
    expect(screen.getByText('动态规划的核心是最优子结构')).not.toBeNull()
  })

  it('同时包含三个字段时应全部显示', () => {
    const result = {
      feedback: '错误分析内容',
      improvement: '改进建议内容',
      explanation: '正确解析内容',
    }
    render(<AnswerFeedback result={result} />)

    expect(screen.getByText('错误分析')).not.toBeNull()
    expect(screen.getByText('改进建议')).not.toBeNull()
    expect(screen.getByText('正确解析')).not.toBeNull()
    expect(screen.getByText('错误分析内容')).not.toBeNull()
    expect(screen.getByText('改进建议内容')).not.toBeNull()
    expect(screen.getByText('正确解析内容')).not.toBeNull()
  })

  it('result为空对象时不应显示任何section', () => {
    const result = {}
    render(<AnswerFeedback result={result} />)

    expect(screen.queryByText('错误分析')).toBeNull()
    expect(screen.queryByText('改进建议')).toBeNull()
    expect(screen.queryByText('正确解析')).toBeNull()
  })

  it('只有feedback时不应显示其他section', () => {
    const result = { feedback: '仅错误分析' }
    render(<AnswerFeedback result={result} />)

    expect(screen.getByText('错误分析')).not.toBeNull()
    expect(screen.queryByText('改进建议')).toBeNull()
    expect(screen.queryByText('正确解析')).toBeNull()
  })
})
