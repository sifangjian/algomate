import styles from './HallHeader.module.css'

export default function HallHeader({ onCreateCard }) {
  return (
    <div className={styles.hallHeader}>
      <div className={styles.titleRow}>
        <button className={styles.createBtn} onClick={onCreateCard}>➕ 新建</button>
      </div>
    </div>
  )
}
