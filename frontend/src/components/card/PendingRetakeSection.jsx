import { useState, useCallback, memo } from 'react'
import RetakeButton from './RetakeButton'
import styles from './PendingRetakeSection.module.css'

function PendingRetakeSection({ cards, onCardClick }) {
  const [isOpen, setIsOpen] = useState(true)

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  if (!cards || cards.length === 0) return null

  return (
    <div className={styles.section}>
      <button className={styles.header} onClick={handleToggle}>
        <span className={styles.title}>
          🔒 待重修卡牌 ({cards.length})
        </span>
        <span className={`${styles.tag}`}>待重修</span>
        <span className={`${styles.toggle} ${isOpen ? styles.toggleOpen : ''}`}>
          ▼
        </span>
      </button>
      {isOpen && (
        <div className={styles.cardGrid}>
          {cards.map((card) => (
            <div key={card.id} className={styles.cardItem}>
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon}>
                  {getAlgorithmIcon(card.algorithm_type || card.algorithmCategory)}
                </span>
                <div className={styles.cardInfo}>
                  <h4 className={styles.cardName}>{card.name}</h4>
                  {(card.algorithm_type || card.algorithmCategory) && (
                    <span className={styles.cardCategory}>
                      {card.algorithm_type || card.algorithmCategory}
                    </span>
                  )}
                </div>
              </div>
              <div className={styles.cardMeta}>
                <span>耐久 {card.durability}/{card.max_durability || card.maxDurability}</span>
              </div>
              <RetakeButton card={card} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function getAlgorithmIcon(category) {
  const map = {
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
  return map[category] || '📜'
}

export default memo(PendingRetakeSection)
