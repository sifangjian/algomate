import styles from './BossLayout.module.css'

export default function BossLayout({ left, right }) {
  return (
    <div className={styles.layout}>
      <div className={styles.leftPanel}>{left}</div>
      <div className={styles.rightPanel}>{right}</div>
    </div>
  )
}
