import { useState } from 'react'
import styles from './LearningPathCard.module.css'

export default function LearningPathCard({ steps }) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className={styles.learningPathCard}>
      <div
        className={styles.pathHeader}
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setIsExpanded(!isExpanded)
          }
        }}
      >
        <span className={styles.pathIcon}>🗺️</span>
        <span className={styles.pathTitle}>推荐学习路径</span>
        <span className={styles.pathToggle}>{isExpanded ? '▲' : '▼'}</span>
      </div>
      {isExpanded && (
        <div className={styles.pathContent}>
          {steps.map(step => (
            <div key={step.order} className={styles.pathStep}>
              <div className={styles.stepOrder}>{step.order}</div>
              <div className={styles.stepInfo}>
                <span className={styles.stepStage}>{step.stage}</span>
                <span className={styles.stepNpc}>{step.npc_name}</span>
                <p className={styles.stepGoal}>{step.goal}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
