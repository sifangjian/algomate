import Modal from '../ui/Modal/Modal'
import Button from '../ui/Button/Button'
import styles from './RecoveryDialog.module.css'

export default function RecoveryDialog({ isOpen, onRecover, onDiscard }) {
  return (
    <Modal open={isOpen} onClose={onDiscard} title="恢复战斗" size="sm">
      <p className={styles.message}>检测到未完成的Boss挑战，是否恢复？</p>
      <div className={styles.actions}>
        <Button variant="ghost" onClick={onDiscard}>
          放弃恢复
        </Button>
        <Button variant="primary" onClick={onRecover}>
          恢复战斗
        </Button>
      </div>
    </Modal>
  )
}
