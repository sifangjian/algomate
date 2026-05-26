import { useState, useCallback, memo } from 'react'
import ExamplesList from './ExamplesList'
import styles from './DimensionSection.module.css'

function parseJSON(value) {
  if (!value) return null
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function isEmpty(val) {
  if (val == null) return true
  if (typeof val === 'string') return val.trim() === ''
  if (Array.isArray(val)) return val.length === 0
  if (typeof val === 'object') return Object.values(val).every(v => isEmpty(v))
  return false
}

const TierSection = memo(function TierSection({ title, icon, color, children }) {
  const [open, setOpen] = useState(true)
  return (
    <div className={styles.tierSection} style={{ borderLeftColor: color }}>
      <button className={styles.tierHeader} onClick={() => setOpen(prev => !prev)}>
        <span className={styles.tierIcon}>{icon}</span>
        <span className={styles.tierTitle}>{title}</span>
        <span className={`${styles.toggle} ${open ? styles.toggleOpen : ''}`}>▼</span>
      </button>
      {open && <div className={styles.tierBody}>{children}</div>}
    </div>
  )
})

const FieldItem = memo(function FieldItem({ label, icon, value }) {
  const [open, setOpen] = useState(false)
  if (isEmpty(value)) return null

  return (
    <div className={styles.dimensionItem}>
      <button className={styles.dimensionHeader} onClick={() => setOpen(prev => !prev)}>
        <span className={styles.dimensionIcon}>{icon}</span>
        <span className={styles.dimensionLabel}>{label}</span>
        <span className={`${styles.dimensionToggle} ${open ? styles.toggleOpen : ''}`}>▼</span>
      </button>
      {open && (
        <div className={styles.dimensionContent}>
          <div className={styles.textContent}>{value}</div>
        </div>
      )}
    </div>
  )
})

export default function DimensionSection({ card }) {
  if (!card) return null

  const basic = parseJSON(card.basic_content) || {}
  const practical = parseJSON(card.practical_content) || {}
  const advanced = parseJSON(card.advanced_content) || {}

  const basicEmpty = isEmpty(basic.concept_definition) && isEmpty(basic.features) && isEmpty(basic.confusing_concepts)
  const practicalEmpty = isEmpty(practical.examples) && isEmpty(practical.applicable_scenarios) && isEmpty(practical.precautions)
  const advancedEmpty = isEmpty(advanced.common_mistakes) && isEmpty(advanced.extensions) && isEmpty(advanced.advanced_solutions)

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>📐 知识维度</h3>

      {!basicEmpty && (
        <TierSection title="基础" icon="📘" color="#6366f1">
          <FieldItem label="概念定义" icon="💡" value={basic.concept_definition} />
          <FieldItem label="特点" icon="🔑" value={basic.features} />
          <FieldItem label="易混淆概念" icon="🔀" value={basic.confusing_concepts} />
        </TierSection>
      )}

      {!practicalEmpty && (
        <TierSection title="实战" icon="⚔️" color="#10b981">
          {practical.examples && practical.examples.length > 0 && (
            <div className={styles.dimensionItem}>
              <div className={styles.dimensionContent}>
                <ExamplesList examples={practical.examples} />
              </div>
            </div>
          )}
          <FieldItem label="适用场景" icon="📋" value={practical.applicable_scenarios} />
          <FieldItem label="注意事项" icon="⚠️" value={practical.precautions} />
        </TierSection>
      )}

      {!advancedEmpty && (
        <TierSection title="进阶" icon="🚀" color="#8b5cf6">
          <FieldItem label="易错点" icon="❌" value={advanced.common_mistakes} />
          <FieldItem label="拓展方向" icon="🔄" value={advanced.extensions} />
          <FieldItem label="高级解法" icon="⚡" value={advanced.advanced_solutions} />
        </TierSection>
      )}

      {card.my_notes && (
        <FieldItem label="个人笔记" icon="📝" value={card.my_notes} />
      )}
    </div>
  )
}
