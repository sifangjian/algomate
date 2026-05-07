import Button from '../ui/Button/Button'
import styles from './NoCardDisabledState.module.css'

export default function NoCardDisabledState({ onGoPractice }) {
  return (
    <div className={styles.container}>
      <span className={styles.icon}>🎴</span>
      <p className={styles.text}>需要至少1张卡牌才能挑战Boss</p>
      <Button variant="primary" onClick={onGoPractice}>
        前往修习
      </Button>
    </div>
  )
}
