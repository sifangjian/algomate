import { useState, useCallback, memo } from 'react'
import styles from './DimensionSection.module.css'

const DIMENSION_META = {
  core_concept: { icon: '💡', label: '核心概念', defaultOpen: true },
  key_points: { icon: '🔑', label: '关键要点', defaultOpen: true },
  code_template: { icon: '💻', label: '代码模板', defaultOpen: false },
  time_complexity: { icon: '⏱️', label: '时间复杂度', defaultOpen: false },
  space_complexity: { icon: '📦', label: '空间复杂度', defaultOpen: false },
  typical_problems: { icon: '🎯', label: '典型题目', defaultOpen: false },
  common_mistakes: { icon: '⚠️', label: '常见错误', defaultOpen: false },
  optimization: { icon: '🚀', label: '优化思路', defaultOpen: false },
  extensions: { icon: '🔗', label: '扩展知识', defaultOpen: false },
  summary: { icon: '📝', label: '总结', defaultOpen: false },
}

function parseContent(key, value) {
  if (value == null) return null
  if (key === 'typical_problems') {
    if (Array.isArray(value)) return value
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed : [String(value)]
    } catch {
      return [String(value)]
    }
  }
  if (key === 'key_points') {
    if (Array.isArray(value)) return value
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed : [String(value)]
    } catch {
      return String(value).split('\n').filter(Boolean)
    }
  }
  return String(value)
}

const DimensionItem = memo(function DimensionItem({ dimensionKey, value, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)
  const meta = DIMENSION_META[dimensionKey]
  const content = parseContent(dimensionKey, value)

  const handleToggle = useCallback(() => {
    setOpen((prev) => !prev)
  }, [])

  if (content == null || (Array.isArray(content) && content.length === 0) || content === '') {
    return null
  }

  return (
    <div className={styles.dimensionItem}>
      <button
        className={styles.dimensionHeader}
        onClick={handleToggle}
        aria-expanded={open}
      >
        <span className={styles.dimensionIcon}>{meta.icon}</span>
        <span className={styles.dimensionLabel}>{meta.label}</span>
        <span className={`${styles.dimensionToggle} ${open ? styles.toggleOpen : ''}`}>
          ▼
        </span>
      </button>
      {open && (
        <div className={styles.dimensionContent}>
          {dimensionKey === 'code_template' ? (
            <pre className={styles.codeBlock}>{content}</pre>
          ) : dimensionKey === 'typical_problems' || dimensionKey === 'key_points' ? (
            <ul className={styles.listContent}>
              {Array.isArray(content)
                ? content.map((item, i) => (
                    <li key={i} className={styles.listItem}>
                      {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                    </li>
                  ))
                : <li className={styles.listItem}>{content}</li>
              }
            </ul>
          ) : (
            <div className={styles.textContent}>{content}</div>
          )}
        </div>
      )}
    </div>
  )
})

const DIMENSION_KEYS = Object.keys(DIMENSION_META)

export default function DimensionSection({ card }) {
  if (!card) return null

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>📐 知识维度</h3>
      <div className={styles.dimensionList}>
        {DIMENSION_KEYS.map((key) => (
          <DimensionItem
            key={key}
            dimensionKey={key}
            value={card[key]}
            defaultOpen={DIMENSION_META[key].defaultOpen}
          />
        ))}
      </div>
    </div>
  )
}
