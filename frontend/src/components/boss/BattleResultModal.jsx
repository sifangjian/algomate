import Modal from '../ui/Modal/Modal'
import ResultAnimation from './ResultAnimation'
import DurabilityChangeDisplay from './DurabilityChangeDisplay'
import AnswerFeedback from './AnswerFeedback'
import GuideButtons from './GuideButtons'
import styles from './BattleResultModal.module.css'

export default function BattleResultModal({ result, isOpen, onClose, onContinue, onGoPractice }) {
  if (!result) return null
  const isVictory = result.is_correct

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title={isVictory ? '挑战成功' : '挑战失败'}
      size="md"
    >
      <div className={styles.content}>
        <ResultAnimation isVictory={isVictory} />
        {isVictory ? (
          <div className={styles.victoryContent}>
            {result.reward && (
              <div className={styles.stats}>
                {result.reward.exp != null && result.reward.exp > 0 && (
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>经验奖励</span>
                    <span className={`${styles.statValue} ${styles.positive}`}>
                      +{result.reward.exp} XP
                    </span>
                  </div>
                )}
                {result.reward.durability_change != null && result.reward.durability_change !== 0 && (
                  <DurabilityChangeDisplay change={result.reward.durability_change} />
                )}
                {result.reward.durability_change === 0 && (
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>卡牌耐久</span>
                    <span className={styles.statValue}>0</span>
                  </div>
                )}
              </div>
            )}
            {result.new_card_dropped && result.dropped_card && (
              <div className={styles.droppedCard}>
                <div className={styles.droppedTitle}>🎁 掉落新卡牌!</div>
                <div className={styles.droppedName}>{result.dropped_card.name}</div>
              </div>
            )}
          </div>
        ) : (
          <AnswerFeedback result={result} />
        )}
        <GuideButtons onContinue={onContinue} onGoPractice={onGoPractice} />
      </div>
    </Modal>
  )
}
