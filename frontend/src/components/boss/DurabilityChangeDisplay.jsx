import styles from './DurabilityChangeDisplay.module.css'

export default function DurabilityChangeDisplay({ change }) {
  if (change == null) return null
  const isPositive = change > 0

  return (
    <div className={styles.container}>
      <span className={styles.label}>卡牌耐久</span>
      <span className={`${styles.value} ${isPositive ? styles.positive : styles.negative}`}>
        {isPositive ? '+' : ''}{change}
      </span>
    </div>
  )
}
