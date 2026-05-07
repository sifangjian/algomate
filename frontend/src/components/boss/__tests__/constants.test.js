import { describe, it, expect } from 'vitest'
import {
  DIFFICULTY_DISPLAY,
  ALGORITHM_TYPE_LABELS,
  QUESTION_TYPE_LABELS,
} from '../constants'

describe('DIFFICULTY_DISPLAY', () => {
  it('应包含 easy/medium/hard 三个难度等级', () => {
    const keys = Object.keys(DIFFICULTY_DISPLAY)
    expect(keys).toEqual(['easy', 'medium', 'hard'])
  })

  it('每个难度应包含 label、emoji 和 stars 字段', () => {
    for (const key of Object.keys(DIFFICULTY_DISPLAY)) {
      const entry = DIFFICULTY_DISPLAY[key]
      expect(entry).toHaveProperty('label')
      expect(entry).toHaveProperty('emoji')
      expect(entry).toHaveProperty('stars')
      expect(typeof entry.label).toBe('string')
      expect(typeof entry.emoji).toBe('string')
      expect(typeof entry.stars).toBe('number')
    }
  })

  it('easy 难度应为 1 星', () => {
    expect(DIFFICULTY_DISPLAY.easy.stars).toBe(1)
  })

  it('medium 难度应为 2 星', () => {
    expect(DIFFICULTY_DISPLAY.medium.stars).toBe(2)
  })

  it('hard 难度应为 3 星', () => {
    expect(DIFFICULTY_DISPLAY.hard.stars).toBe(3)
  })
})

describe('ALGORITHM_TYPE_LABELS', () => {
  const EXPECTED_TYPES = [
    'basic_data_structure',
    'stack_queue_search',
    'search_traversal',
    'tree',
    'graph',
    'backtracking',
    'greedy',
    'dynamic_programming',
  ]

  it('应包含全部 8 种算法类型', () => {
    const keys = Object.keys(ALGORITHM_TYPE_LABELS)
    expect(keys).toEqual(EXPECTED_TYPES)
    expect(keys).toHaveLength(8)
  })

  it('每个算法类型标签应为非空字符串', () => {
    for (const key of EXPECTED_TYPES) {
      expect(typeof ALGORITHM_TYPE_LABELS[key]).toBe('string')
      expect(ALGORITHM_TYPE_LABELS[key].length).toBeGreaterThan(0)
    }
  })
})

describe('QUESTION_TYPE_LABELS', () => {
  it('应包含 choice/short_answer/leetcode 三种题型', () => {
    const keys = Object.keys(QUESTION_TYPE_LABELS)
    expect(keys).toEqual(['choice', 'short_answer', 'leetcode'])
  })

  it('choice 应映射为"选择题"', () => {
    expect(QUESTION_TYPE_LABELS.choice).toBe('选择题')
  })

  it('short_answer 应映射为"简答题"', () => {
    expect(QUESTION_TYPE_LABELS.short_answer).toBe('简答题')
  })

  it('leetcode 应映射为"LeetCode挑战"', () => {
    expect(QUESTION_TYPE_LABELS.leetcode).toBe('LeetCode挑战')
  })
})
