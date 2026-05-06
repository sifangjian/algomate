import { useState, useCallback, memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import RetakeButton from './RetakeButton'
import styles from './PendingRetakeSection.module.css'

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

function PendingRetakeSection({ onCardClick }) {
  const [isOpen, setIsOpen] = useState(true)
  const { pendingRetakeCount, cards } = useCardStore()

  const pendingRetakeCards = cards.filter((c) => c.status === 'pending_retake')

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  if (!pendingRetakeCount || pendingRetakeCount <= 0) return null

  return (
    <div className={styles.section}>
      <button className={styles.header} onClick={handleToggle}>
        <span className={styles.title}>
          🔒 待重修卡牌 ({pendingRetakeCount})
        </span>
        <span className={styles.tag}>待重修</span>
        <span className={`${styles.toggle} ${isOpen ? styles.toggleOpen : ''}`}>
          ▼
        </span>
      </button>
      {isOpen && (
        <div className={styles.cardGrid}>
          {pendingRetakeCards.map((card) => (
            <div key={card.id} className={styles.cardItem}>
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon}>
                  {ALGORITHM_ICONS[card.algorithm_type] || '📜'}
                </span>
                <div className={styles.cardInfo}>
                  <h4 className={styles.cardName}>{card.name}</h4>
                  {card.algorithm_type && (
                    <span className={styles.cardCategory}>
                      {card.algorithm_type}
                    </span>
                  )}
                </div>
              </div>
              <div className={styles.cardMeta}>
                <span>耐久 {card.durability}/{card.max_durability || 100}</span>
              </div>
              <RetakeButton card={card} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default memo(PendingRetakeSection)
