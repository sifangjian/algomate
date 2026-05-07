import { DIFFICULTY_DISPLAY, ALGORITHM_TYPE_LABELS } from './constants'
import styles from './BossCard.module.css'

export default function BossCard({ boss, selected, onSelect }) {
  const diff = DIFFICULTY_DISPLAY[boss.difficulty] || DIFFICULTY_DISPLAY.medium

  return (
    <div
      className={`${styles.card} ${selected ? styles.selected : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      <div className={styles.header}>
        <span className={styles.emoji}>{diff.emoji}</span>
        <div className={styles.info}>
          <div className={styles.name}>{boss.name}</div>
          <div className={styles.meta}>
            <span className={styles.stars}>
              {'★'.repeat(diff.stars)}{'☆'.repeat(3 - diff.stars)}
            </span>
            <span className={styles.diffLabel}>{diff.label}</span>
          </div>
        </div>
      </div>
      <div className={styles.weakness}>
        弱点: {ALGORITHM_TYPE_LABELS[boss.weakness_type] || boss.weakness_type}
      </div>
    </div>
  )
}
