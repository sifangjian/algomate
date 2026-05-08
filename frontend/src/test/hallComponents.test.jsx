import React from 'react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AlgorithmTypeTags from '../components/hall/AlgorithmTypeTags'
import SpecialtyTags from '../components/hall/SpecialtyTags'
import CardCountBadge from '../components/hall/CardCountBadge'
import RecommendTip from '../components/hall/RecommendTip'
import NpcAvatar from '../components/hall/NpcAvatar'
import NpcGrid from '../components/hall/NpcGrid'
import LearningPathCard from '../components/hall/LearningPathCard'

describe('AlgorithmTypeTags', () => {
  const types = [
    { value: '', label: '全部' },
    { value: 'basic_data_structure', label: '基础数据结构' },
    { value: 'tree', label: '树结构' },
  ]

  it('应渲染所有类型标签', () => {
    render(<AlgorithmTypeTags types={types} selected="" onSelect={vi.fn()} />)
    expect(screen.getByText('全部')).toBeInTheDocument()
    expect(screen.getByText('基础数据结构')).toBeInTheDocument()
    expect(screen.getByText('树结构')).toBeInTheDocument()
  })

  it('应高亮选中的标签', () => {
    render(<AlgorithmTypeTags types={types} selected="tree" onSelect={vi.fn()} />)
    const treeTag = screen.getByText('树结构')
    expect(treeTag).toHaveAttribute('aria-checked', 'true')
  })

  it('点击标签应调用 onSelect', async () => {
    const onSelect = vi.fn()
    render(<AlgorithmTypeTags types={types} selected="" onSelect={onSelect} />)
    await userEvent.click(screen.getByText('树结构'))
    expect(onSelect).toHaveBeenCalledWith('tree')
  })

  it('点击"全部"应传入空字符串', async () => {
    const onSelect = vi.fn()
    render(<AlgorithmTypeTags types={types} selected="tree" onSelect={onSelect} />)
    await userEvent.click(screen.getByText('全部'))
    expect(onSelect).toHaveBeenCalledWith('')
  })
})

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

describe('RecommendTip', () => {
  it('应显示推荐提示文本', () => {
    render(<RecommendTip />)
    expect(screen.getByText('推荐新手从这里开始')).toBeInTheDocument()
  })

  it('应包含星标图标', () => {
    render(<RecommendTip />)
    expect(screen.getByText('⭐')).toBeInTheDocument()
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

describe('NpcGrid', () => {
  it('应渲染所有 NPC 卡片', () => {
    const npcs = [
      { id: 1, name: '老夫子', title: '基础数据结构导师', algorithm_type: 'basic_data_structure', specialties: ['数组'], avatar: 'laofuzi', card_count: 0 },
      { id: 2, name: '栈语者', title: '栈队列与搜索导师', algorithm_type: 'stack_queue_search', specialties: ['栈'], avatar: 'zhanzhe', card_count: 2 },
    ]
    render(<NpcGrid npcs={npcs} isNewUser={false} />)
    expect(screen.getByText('老夫子')).toBeInTheDocument()
    expect(screen.getByText('栈语者')).toBeInTheDocument()
  })

  it('空列表应显示空状态', () => {
    render(<NpcGrid npcs={[]} isNewUser={false} />)
    expect(screen.getByText('未找到匹配的导师')).toBeInTheDocument()
  })

  it('有卡牌的 NPC 应显示卡牌数量', () => {
    const npcs = [
      { id: 1, name: '老夫子', title: '基础数据结构导师', algorithm_type: 'basic_data_structure', specialties: ['数组'], avatar: 'laofuzi', card_count: 3 },
    ]
    render(<NpcGrid npcs={npcs} isNewUser={false} />)
    expect(screen.getByText('已获3张卡牌')).toBeInTheDocument()
  })

  it('新用户时老夫子应显示推荐提示', () => {
    const npcs = [
      { id: 1, name: '老夫子', title: '基础数据结构导师', algorithm_type: 'basic_data_structure', specialties: ['数组'], avatar: 'laofuzi', card_count: 0 },
    ]
    render(<NpcGrid npcs={npcs} isNewUser={true} />)
    expect(screen.getByText('推荐新手从这里开始')).toBeInTheDocument()
  })
})

describe('LearningPathCard', () => {
  const steps = [
    { order: 1, npc_name: '老夫子', algorithm_type: 'basic_data_structure', stage: '基础入门', goal: '掌握基础数据结构' },
    { order: 2, npc_name: '栈语者', algorithm_type: 'stack_queue_search', stage: '搜索基础', goal: '掌握栈队列与搜索' },
  ]

  it('应显示推荐学习路径标题', () => {
    render(<LearningPathCard steps={steps} />)
    expect(screen.getByText('推荐学习路径')).toBeInTheDocument()
  })

  it('默认折叠状态不应显示步骤详情', () => {
    render(<LearningPathCard steps={steps} />)
    expect(screen.queryByText('基础入门')).not.toBeInTheDocument()
  })

  it('点击展开后应显示步骤详情', async () => {
    render(<LearningPathCard steps={steps} />)
    await userEvent.click(screen.getByText('推荐学习路径'))
    expect(screen.getByText('基础入门')).toBeInTheDocument()
    expect(screen.getByText('掌握基础数据结构')).toBeInTheDocument()
    expect(screen.getByText('搜索基础')).toBeInTheDocument()
  })

  it('再次点击应折叠', async () => {
    render(<LearningPathCard steps={steps} />)
    const header = screen.getByText('推荐学习路径')
    await userEvent.click(header)
    expect(screen.getByText('基础入门')).toBeInTheDocument()
    await userEvent.click(header)
    expect(screen.queryByText('基础入门')).not.toBeInTheDocument()
  })
})
