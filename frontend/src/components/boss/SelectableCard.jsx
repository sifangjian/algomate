import styles from './SelectableCard.module.css'

function getDurabilityColor(durability, maxDurability) {
  const percent = (durability / (maxDurability || 100)) * 100
  if (percent > 60) return 'linear-gradient(90deg, var(--color-success), #34d399)'
  if (percent >= 30) return 'linear-gradient(90deg, var(--color-warning), #fbbf24)'
  return 'linear-gradient(90deg, var(--color-danger), #f87171)'
}

export default function SelectableCard({ card, isWeakness, selected, onSelect, loading }) {
  const maxDur = card.max_durability || 100
  const durPercent = Math.min(100, Math.max(0, (card.durability / maxDur) * 100))

  return (
    <div
      className={`${styles.card} ${isWeakness ? styles.weakness : ''} ${selected ? styles.selected : ''} ${loading ? styles.disabled : ''}`}
      onClick={loading ? undefined : onSelect}
      role="button"
      tabIndex={loading ? -1 : 0}
      onKeyDown={(e) => {
        if (!loading && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      {isWeakness && <span className={styles.weaknessBadge}>弱点</span>}
      <div className={styles.cardHeader}>
        <span className={styles.cardName}>{card.name}</span>
      </div>
      <div className={styles.cardType}>{card.algorithm_type}</div>
      <div className={styles.durability}>
        <div className={styles.durBar}>
          <div
            className={styles.durFill}
            style={{
              width: `${durPercent}%`,
              background: getDurabilityColor(card.durability, maxDur),
            }}
          />
        </div>
        <span className={styles.durText}>
          耐久 {card.durability}/{maxDur}
        </span>
      </div>
    </div>
  )
}
