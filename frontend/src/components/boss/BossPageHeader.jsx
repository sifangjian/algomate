import styles from './BossPageHeader.module.css'

export default function BossPageHeader({ cardCount }) {
  return (
    <div className={styles.header}>
      <h1 className={styles.title}>Boss挑战</h1>
      {cardCount > 0 && (
        <span className={styles.badge}>🎴 {cardCount} 张卡牌</span>
      )}
    </div>
  )
}
