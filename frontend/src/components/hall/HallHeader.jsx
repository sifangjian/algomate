import styles from './HallHeader.module.css'

export default function HallHeader({ onCreateCard }) {
  return (
    <div className={styles.hallHeader}>
      <div className={styles.titleRow}>
        <h1 className={styles.pageTitle}>算法地图</h1>
        <button className={styles.createBtn} onClick={onCreateCard}>➕ 创建新卡牌</button>
      </div>
    </div>
  )
}
