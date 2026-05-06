import { useRef } from 'react'
import Input from '../ui/Input/Input'
import AlgorithmTypeTags from './AlgorithmTypeTags'
import styles from './HallHeader.module.css'

const ALGORITHM_TYPES = [
  { value: '', label: '全部' },
  { value: 'basic_data_structure', label: '基础数据结构' },
  { value: 'stack_queue_search', label: '栈队列与搜索' },
  { value: 'search_traversal', label: '搜索与遍历' },
  { value: 'tree', label: '树结构' },
  { value: 'graph', label: '图结构' },
  { value: 'backtracking', label: '回溯算法' },
  { value: 'greedy', label: '贪心算法' },
  { value: 'dynamic_programming', label: '动态规划' },
]

export default function HallHeader({ filters, onFilterChange, onReset }) {
  const debounceRef = useRef(null)

  const handleSearch = (e) => {
    const val = e.target.value
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onFilterChange({ keyword: val })
    }, 300)
  }

  return (
    <div className={styles.hallHeader}>
      <h1 className={styles.pageTitle}>导师大厅</h1>
      <div className={styles.searchRow}>
        <Input
          placeholder="搜索导师名称或专长..."
          defaultValue={filters.keyword}
          onChange={handleSearch}
          maxLength={50}
          icon="🔍"
        />
      </div>
      <AlgorithmTypeTags
        types={ALGORITHM_TYPES}
        selected={filters.algorithm_type}
        onSelect={(type) => onFilterChange({ algorithm_type: type })}
      />
    </div>
  )
}
