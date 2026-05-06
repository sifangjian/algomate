import styles from './GameCard.module.css'

const ALGORITHM_ICONS = {
  Search: '🔍',
  Sorting: '📊',
  'Dynamic Programming': '🎯',
  Graph: '🕸️',
  Tree: '🌲',
  Recursion: '🔄',
  Array: '📋',
  String: '📝',
  Greedy: '💰',
  Math: '🔢',
}

function getDurabilityColor(durability) {
  if (durability > 60) return 'var(--color-success)'
  if (durability >= 30) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

export default function GameCard({ card, onClick, className = '' }) {
  if (!card) return null

  const isEndangered = card.status === 'endangered'
  const isPendingRetake = card.status === 'pending_retake'
  const maxDur = card.max_durability || 100
  const durPercent = Math.min(100, Math.max(0, (card.durability / maxDur) * 100))

  return (
    <div
      className={`
        ${styles.card}
        ${onClick ? styles.hoverable : ''}
        ${isEndangered ? styles.glow : ''}
        ${isPendingRetake ? styles.locked : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          onClick()
        }
      }}
    >
      <div className={styles.cardHeader}>
        <span className={styles.cardIcon}>
          {ALGORITHM_ICONS[card.algorithm_type] || '📜'}
        </span>
        <div className={styles.cardTitleArea}>
          <h3 className={styles.cardName}>{card.name}</h3>
          {card.algorithm_type && (
            <span className={styles.cardCategory}>{card.algorithm_type}</span>
          )}
        </div>
        <div className={styles.badges}>
          {isEndangered && (
            <span className={styles.endangeredBadge}>濒危</span>
          )}
          {card.pending_retake && (
            <span className={styles.retakeBadge}>待重修</span>
          )}
        </div>
      </div>

      <div className={styles.durabilitySection}>
        <div className={styles.durBar}>
          <div
            className={styles.durFill}
            style={{
              width: `${durPercent}%`,
              background: getDurabilityColor(card.durability),
              ...(isEndangered && { animation: 'pulse-glow 2s infinite' }),
            }}
          />
        </div>
        <span className={styles.durText}>
          耐久 {card.durability}/{maxDur}
        </span>
      </div>

      <div className={styles.cardMeta}>
        <span>修炼 {card.review_count || 0}次</span>
      </div>
    </div>
  )
}
