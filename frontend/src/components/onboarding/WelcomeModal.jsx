import { useState } from 'react'
import Modal from '../ui/Modal/Modal'
import { ConfirmDialog } from '../ui/Modal/Modal'
import Button from '../ui/Button/Button'
import OnboardingStepIndicator from './OnboardingStepIndicator'
import styles from './WelcomeModal.module.css'

export default function WelcomeModal({ onStart, onSkip }) {
  const [showSkipConfirm, setShowSkipConfirm] = useState(false)

  return (
    <>
      <Modal open={true} onClose={() => setShowSkipConfirm(true)} ariaLabel="欢迎引导" closeOnOverlay={false}>
        <div className={styles.welcomeModal}>
          <div className={styles.welcomeIcon}>🏰</div>
          <h1 className={styles.welcomeTitle}>欢迎来到算法大陆</h1>
          <div className={styles.welcomeStory}>
            <p>在这片神秘的大陆上，算法是修仙者最强大的力量。</p>
            <p>跟随导师修习，收集卡牌，挑战 Boss，</p>
            <p>成为算法大陆的至强者！</p>
          </div>
          <OnboardingStepIndicator current={1} total={5} />
          <div className={styles.welcomeActions}>
            <Button variant="primary" onClick={onStart} fullWidth aria-label="开始冒险，进入新手引导">
              开始冒险
            </Button>
            <Button variant="ghost" onClick={() => setShowSkipConfirm(true)} aria-label="跳过新手引导">
              跳过引导
            </Button>
          </div>
        </div>
      </Modal>
      {showSkipConfirm && (
        <ConfirmDialog
          open={true}
          onClose={() => setShowSkipConfirm(false)}
          onConfirm={onSkip}
          onCancel={() => setShowSkipConfirm(false)}
          title="是否跳过引导？"
          message="跳过后将不再显示新手引导，你可以自由探索算法大陆。"
        />
      )}
    </>
  )
}
