import styles from './ReviewStatsBar.module.css'

export default function ReviewStatsBar({ completedCount, totalCount, weeklyDays, totalReviews, endangeredCount }) {
  if (totalCount === 0 && !totalReviews) return null

  return (
    <div className={styles.statsBar}>
      {totalCount > 0 && (
        <>
          <span className={styles.statsItem}>
            今日 <span className={styles.statsHighlight}>{completedCount}/{totalCount}</span>
          </span>
          <span className={styles.statsDot}>|</span>
        </>
      )}
      {weeklyDays != null && (
        <>
          <span className={styles.statsItem}>
            连续 <span className={styles.statsHighlight}>{weeklyDays}</span> 天
          </span>
          <span className={styles.statsDot}>|</span>
        </>
      )}
      {totalReviews != null && (
        <>
          <span className={styles.statsItem}>
            累计 <span className={styles.statsHighlight}>{totalReviews}</span> 次
          </span>
        </>
      )}
      {endangeredCount > 0 && (
        <span className={styles.endangeredBadge}>
          {endangeredCount} 张濒危
        </span>
      )}
    </div>
  )
}
