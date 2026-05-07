import { useNavigate } from 'react-router-dom'
import Button from '../ui/Button/Button'
import { useGuideStore } from '../../stores/guideStore'
import styles from './PostReviewGuide.module.css'

const ACTION_ICONS = {
  continue_review: '🧘',
  go_boss: '⚔️',
}

export default function PostReviewGuide({ guide, scene }) {
  const navigate = useNavigate()
  const { shouldShowGuide, skipGuide } = useGuideStore()

  if (!guide || !shouldShowGuide(scene)) {
    return null
  }

  const availableActions = guide.available_actions.filter((action) => action.available)

  const handleAction = (action) => {
    navigate(action.target_path)
  }

  const handleSkip = () => {
    skipGuide(scene)
  }

  return (
    <div className={styles.guidePanel}>
      <p className={styles.guideMessage}>{guide.message}</p>
      <div className={styles.guideActions}>
        {availableActions.map((action) => (
          <Button
            key={action.action}
            variant={action.action === 'continue_review' ? 'accent' : 'secondary'}
            onClick={() => handleAction(action)}
          >
            {ACTION_ICONS[action.action] || '→'} {action.label}
          </Button>
        ))}
      </div>
      <button className={styles.skipButton} onClick={handleSkip}>
        跳过
      </button>
    </div>
  )
}
