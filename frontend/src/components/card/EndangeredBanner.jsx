import { memo } from 'react'
import styles from './EndangeredBanner.module.css'

function EndangeredBanner({ count, endangeredCards, onCardClick }) {
  if (!count || count <= 0) return null

  return (
    <div className={styles.banner} role="alert">
      <div className={styles.bannerHeader}>
        <span className={styles.bannerIcon}>⚠️</span>
        <span className={styles.bannerText}>
          有 <strong className={styles.bannerCount}>{count}</strong> 张卡牌濒危，请及时修炼！
        </span>
        <span className={styles.endangeredTag}>濒危</span>
      </div>
      {endangeredCards && endangeredCards.length > 0 && (
        <div className={styles.cardList}>
          {endangeredCards.map((card) => (
            <button
              key={card.id}
              className={styles.cardItem}
              onClick={() => onCardClick?.(card)}
              title={`点击修炼「${card.name}」`}
            >
              <span className={styles.cardIcon}>{getAlgorithmIcon(card.algorithm_type || card.algorithmCategory)}</span>
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

export default memo(EndangeredBanner)
