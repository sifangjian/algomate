import styles from './ResultAnimation.module.css'

export default function ResultAnimation({ isVictory }) {
  return (
    <div className={`${styles.animation} ${isVictory ? styles.victory : styles.defeat}`}>
      <span className={styles.icon}>{isVictory ? '🏆' : '💀'}</span>
      <span className={styles.text}>{isVictory ? '挑战成功!' : '挑战失败'}</span>
    </div>
  )
}
