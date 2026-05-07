import Button from '../ui/Button/Button'
import styles from './GuideButtons.module.css'

export default function GuideButtons({ onContinue, onGoPractice }) {
  return (
    <div className={styles.buttons}>
      <Button variant="secondary" onClick={onContinue}>
        继续挑战
      </Button>
      <Button variant="ghost" onClick={onGoPractice}>
        去修炼
      </Button>
    </div>
  )
}
