import styles from './RecommendTip.module.css'

export default function RecommendTip() {
  return (
    <div className={styles.recommendTip}>
      <span className={styles.recommendIcon}>⭐</span>
      <span className={styles.recommendText}>推荐从这里开始</span>
    </div>
  )
}
