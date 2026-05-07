import { useGuideStore } from '../../stores/guideStore'
import { useGuideNavigation } from '../../hooks/useGuideNavigation'
import Button from '../ui/Button/Button'
import styles from './PostDialogueGuide.module.css'

const SCENE = 'after_dialogue'

export default function PostDialogueGuide() {
  const { currentGuide, visible, skipGuide, shouldShowGuide } = useGuideStore()
  const { navigateToAction } = useGuideNavigation()

  if (!visible || !currentGuide || !shouldShowGuide(SCENE)) {
    return null
  }

  const availableActions = currentGuide.available_actions?.filter(
    (action) => action.available !== false
  ) || []

  if (availableActions.length === 0) {
    return null
  }

  return (
    <div className={styles.container}>
      <p className={styles.message}>{currentGuide.message}</p>
      <div className={styles.buttons}>
        {availableActions.map((action) => (
          <Button
            key={action.action}
            variant={action.action === 'go_boss' ? 'secondary' : 'ghost'}
            onClick={() => navigateToAction(action)}
          >
            {action.label}
          </Button>
        ))}
        <Button variant="ghost" onClick={() => skipGuide(SCENE)}>
          跳过
        </Button>
      </div>
    </div>
  )
}
