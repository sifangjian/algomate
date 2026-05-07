import styles from './BossRightPanel.module.css'

export default function BossRightPanel({ children }) {
  return (
    <div className={styles.panel}>
      {children || (
        <div className={styles.placeholder}>
          <span className={styles.icon}>⚔️</span>
          <p>选择一个Boss开始挑战</p>
        </div>
      )}
    </div>
  )
}
