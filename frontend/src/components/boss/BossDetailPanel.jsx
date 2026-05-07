import { DIFFICULTY_DISPLAY, ALGORITHM_TYPE_LABELS } from './constants'
import styles from './BossDetailPanel.module.css'

export default function BossDetailPanel({ boss }) {
  if (!boss) return null
  const diff = DIFFICULTY_DISPLAY[boss.difficulty] || DIFFICULTY_DISPLAY.medium

  return (
    <div className={styles.detail}>
      <div className={styles.header}>
        <span className={styles.emoji}>{diff.emoji}</span>
        <div className={styles.info}>
          <h2 className={styles.name}>{boss.name}</h2>
          <div className={styles.meta}>
            <span className={styles.diffBadge}>{diff.label}</span>
            <span className={styles.stars}>
              {'★'.repeat(diff.stars)}{'☆'.repeat(3 - diff.stars)}
            </span>
          </div>
        </div>
      </div>
      <div className={styles.weaknessRow}>
        <span className={styles.weaknessLabel}>弱点属性</span>
        <span className={styles.weaknessValue}>
          {ALGORITHM_TYPE_LABELS[boss.weakness_type] || boss.weakness_type}
        </span>
      </div>
      {boss.description && (
        <p className={styles.description}>{boss.description}</p>
      )}
    </div>
  )
}
