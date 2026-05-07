import styles from './NoWeaknessHint.module.css'

export default function NoWeaknessHint() {
  return (
    <div className={styles.hint}>
      <span className={styles.icon}>⚠️</span>
      <p className={styles.text}>你没有此Boss弱点类型的卡牌，使用其他卡牌挑战将更困难</p>
    </div>
  )
}
