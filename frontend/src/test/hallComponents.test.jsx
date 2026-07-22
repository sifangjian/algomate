import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import SpecialtyTags from '../components/hall/SpecialtyTags'
import CardCountBadge from '../components/hall/CardCountBadge'
import NpcAvatar from '../components/hall/NpcAvatar'
import AlgorithmMap from '../components/hall/AlgorithmMap'
import { useHallStore } from '../stores/hallStore'

describe('SpecialtyTags', () => {
  it('应渲染所有专长标签', () => {
    render(<SpecialtyTags specialties={['数组与双指针', '链表', '哈希表']} />)
    expect(screen.getByText('数组与双指针')).toBeInTheDocument()
    expect(screen.getByText('链表')).toBeInTheDocument()
    expect(screen.getByText('哈希表')).toBeInTheDocument()
  })

  it('空数组不应渲染任何内容', () => {
    const { container } = render(<SpecialtyTags specialties={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('undefined 不应渲染任何内容', () => {
    const { container } = render(<SpecialtyTags specialties={undefined} />)
    expect(container.innerHTML).toBe('')
  })
})

describe('CardCountBadge', () => {
  it('应显示卡牌数量', () => {
    render(<CardCountBadge count={3} />)
    expect(screen.getByText('已获3张卡牌')).toBeInTheDocument()
  })

  it('count 为 0 不应渲染', () => {
    const { container } = render(<CardCountBadge count={0} />)
    expect(container.innerHTML).toBe('')
  })

  it('count 未传不应渲染', () => {
    const { container } = render(<CardCountBadge />)
    expect(container.innerHTML).toBe('')
  })
})

describe('NpcAvatar', () => {
  it('应根据 avatar 键显示对应 emoji', () => {
    render(<NpcAvatar avatar="laofuzi" name="老夫子" />)
    expect(screen.getByText('🧓')).toBeInTheDocument()
  })

  it('未知 avatar 应显示 avatar 字符串本身', () => {
    render(<NpcAvatar avatar="unknown" name="测试" />)
    expect(screen.getByText('unknown')).toBeInTheDocument()
  })

  it('空 avatar 应显示默认 emoji', () => {
    render(<NpcAvatar avatar="" name="测试" />)
    expect(screen.getByText('🧙')).toBeInTheDocument()
  })
})

const mockAlgorithmInfo = {
  algorithm_types: ['数组与双指针', '链表', '哈希表', '线性DP', '背包问题'],
  topic_importance: {
    '数组与双指针': 'core',
    '链表': 'core',
    '哈希表': 'core',
    '线性DP': 'core',
    '背包问题': 'important',
  },
  topic_prerequisites: {
    '背包问题': ['线性DP'],
  },
  topic_progress: {
    '数组与双指针': { card_count: 2, avg_durability: 80, learned: true },
    '链表': { card_count: 0, avg_durability: 0, learned: false },
    '哈希表': { card_count: 0, avg_durability: 0, learned: false },
    '线性DP': { card_count: 1, avg_durability: 50, learned: true },
    '背包问题': { card_count: 0, avg_durability: 0, learned: false },
  },
}

const mockNpcs = [
  { id: 1, name: '基础数据结构', title: '基础数据结构', specialties: ['数组与双指针', '链表', '哈希表'], avatar: '📚' },
  { id: 2, name: '动态规划', title: '动态规划', specialties: ['线性DP', '背包问题'], avatar: '💡' },
]

const mockLearningPath = [
  { order: 1, npc_name: '基础数据结构', algorithm_type: 'basic_data_structure', stage: '基础入门', goal: '掌握基础数据结构' },
  { order: 2, npc_name: '动态规划', algorithm_type: 'dynamic_programming', stage: '进阶学习', goal: '掌握动态规划' },
]

describe('AlgorithmMap', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useHallStore.setState({
      npcs: [],
      algorithmInfo: null,
      learningPath: [],
    })
  })

  it('加载中应显示加载提示', () => {
    render(
      React.createElement(MemoryRouter, null,
        React.createElement(AlgorithmMap)
      )
    )
    expect(screen.getByText('正在加载算法地图...')).toBeInTheDocument()
  })

  it('应渲染SVG地图', () => {
    useHallStore.setState({
      npcs: mockNpcs,
      algorithmInfo: mockAlgorithmInfo,
      learningPath: [],
    })
    const { container } = render(
      React.createElement(MemoryRouter, null,
        React.createElement(AlgorithmMap)
      )
    )
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})