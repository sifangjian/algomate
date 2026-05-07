import { useGuideStore } from '../../stores/guideStore'
import { useGuideNavigation } from '../../hooks/useGuideNavigation'
import Button from '../ui/Button/Button'
import styles from './GuideCard.module.css'

export default function GuideCard({ guide, scene }) {
  const { skipGuide, shouldShowGuide } = useGuideStore()
  const { navigateToAction } = useGuideNavigation()

  if (!guide || !shouldShowGuide(scene)) {
    return null
  }

  const availableActions = guide.available_actions?.filter(
    (action) => action.available !== false
  ) || []

  if (availableActions.length === 0) {
    return null
  }

  return (
    <div className={styles.guidePanel}>
      <p className={styles.guideMessage}>{guide.message}</p>
      <div className={styles.guideActions}>
        {availableActions.map((action) => (
          <Button
            key={action.action}
            variant="secondary"
            onClick={() => navigateToAction(action)}
          >
            {action.label}
          </Button>
        ))}
      </div>
      <button className={styles.skipButton} onClick={() => skipGuide(scene)}>
        跳过
      </button>
    </div>
  )
}
