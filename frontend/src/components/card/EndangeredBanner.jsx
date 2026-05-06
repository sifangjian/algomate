import { memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import styles from './EndangeredBanner.module.css'

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

function EndangeredBanner({ onCardClick }) {
  const { endangeredCount, cards } = useCardStore()

  if (!endangeredCount || endangeredCount <= 0) return null

  const endangeredCards = cards.filter((c) => c.status === 'endangered')

  return (
    <div className={styles.banner} role="alert">
      <div className={styles.bannerHeader}>
        <span className={styles.bannerIcon}>⚠️</span>
        <span className={styles.bannerText}>
          有 <strong className={styles.bannerCount}>{endangeredCount}</strong> 张卡牌濒危，请及时修炼！
        </span>
        <span className={styles.endangeredTag}>濒危</span>
      </div>
      {endangeredCards.length > 0 && (
        <div className={styles.cardList}>
          {endangeredCards.map((card) => (
            <button
              key={card.id}
              className={styles.cardItem}
              onClick={() => onCardClick?.(card)}
              title={`点击修炼「${card.name}」`}
            >
              <span className={styles.cardIcon}>{ALGORITHM_ICONS[card.algorithm_type] || '📜'}</span>
              <span className={styles.cardName}>{card.name}</span>
              <span className={styles.cardPulse} />
              <span className={styles.cardAction}>去修炼 →</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default memo(EndangeredBanner)
