import { useState } from 'react'
import { useCardStore } from '../../stores/cardStore'
import RetakeButton from './RetakeButton'
import styles from './PendingRetakeSection.module.css'

export default function PendingRetakeSection({ onCardClick }) {
  const store = useCardStore()
  const pendingRetakeCount = store?.pendingRetakeCount
  const cards = store?.cards
  const [collapsed, setCollapsed] = useState(false)

  if (!pendingRetakeCount || pendingRetakeCount === 0) {
    return null
  }

  const pendingCards = (cards || []).filter(c => c.status === 'pending_retake')

  return (
    <div className={styles.pendingRetakeSection}>
      <button
        className={styles.header}
        onClick={() => setCollapsed(!collapsed)}
      >
        <span className={styles.title}>待重修卡牌 ({pendingRetakeCount})</span>
      </button>
      {!collapsed && (
        <div className={styles.cardList}>
          {pendingCards.map((card) => (
            <div key={card.id} className={styles.cardItem}>
              <div className={styles.cardInfo} onClick={() => onCardClick?.(card)}>
                <span className={styles.cardName}>{card.name}</span>
                <span className={styles.retakeTag}>待重修</span>
                {card.durability !== undefined && (
                  <span className={styles.durability}>耐久度: {card.durability}/{card.max_durability || 5}</span>
                )}
              </div>
              <RetakeButton card={card} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
