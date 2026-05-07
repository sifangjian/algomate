import Button from '../ui/Button/Button'
import styles from './PostBossGuide.module.css'

export default function PostBossGuide({ guide, onAction }) {
  if (!guide) return null

  return (
    <div className={styles.container}>
      <p className={styles.message}>{guide.message}</p>
      <div className={styles.actions}>
        {guide.available_actions.map((action) => (
          <Button
            key={action.action}
            variant={action.available !== false ? 'secondary' : 'ghost'}
            onClick={() => action.available !== false && onAction?.(action)}
            disabled={action.available === false}
          >
            {action.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
