import styles from './TaskCard.module.css'

const TASK_TYPE_CONFIG = {
  critical_review: { label: '濒危', className: styles.reasonCritical },
  forgetting_curve_review: { label: '遗忘曲线', className: styles.reasonForgetting },
  leetcode_challenge: { label: 'LeetCode', className: styles.reasonLeetcode },
}

function getAlgorithmIcon(category) {
  const map = {
    Search: '🔍', Sorting: '📊', 'Dynamic Programming': '🎯',
    Graph: '🕸️', Tree: '🌲', Recursion: '🔄', Array: '📋',
    String: '📝', Greedy: '💰', Math: '🔢',
  }
  return map[category] || '📜'
}

function getDurabilityClass(durability, maxDurability) {
  const pct = maxDurability > 0 ? (durability / maxDurability) * 100 : 0
  if (pct < 30) return styles.fillCritical
  if (pct < 60) return styles.fillWarning
  return styles.fillNormal
}

export default function TaskCard({ task, isCompleted, onReview, onQuiz, onLeetCode }) {
  const typeConfig = TASK_TYPE_CONFIG[task.task_type] || TASK_TYPE_CONFIG.leetcode_challenge
  const durability = task.card_durability ?? 0
  const maxDurability = task.max_durability || 100
  const durPct = maxDurability > 0 ? Math.min(100, Math.max(0, (durability / maxDurability) * 100)) : 0

  return (
    <div className={`${styles.taskCard} ${isCompleted ? styles.completed : ''}`}>
      <div className={styles.taskHeader}>
        <div className={styles.taskNameArea}>
          <span className={styles.taskIcon}>{getAlgorithmIcon(task.algorithm_type)}</span>
          <span className={styles.taskName}>{task.card_name}</span>
        </div>
        <span className={`${styles.reason} ${typeConfig.className}`}>
          {typeConfig.label}
        </span>
      </div>

      <div className={styles.durabilityRow}>
        <div className={styles.durabilityBar}>
          <div
            className={`${styles.durabilityFill} ${getDurabilityClass(durability, maxDurability)}`}
            style={{ width: `${durPct}%` }}
          />
        </div>
        <span className={styles.durabilityText}>{durability}/{maxDurability}</span>
      </div>

      {!isCompleted ? (
        <div className={styles.actionButtons}>
          {(task.review_types || ['content_review', 'quick_quiz', 'leetcode_challenge']).map((rt) => {
            if (rt === 'content_review') {
              return <button key={rt} className={styles.actionBtn} onClick={onReview}>📖 知识回顾</button>
            }
            if (rt === 'quick_quiz') {
              return <button key={rt} className={styles.actionBtn} onClick={onQuiz}>✏️ 快速问答</button>
            }
            if (rt === 'leetcode_challenge') {
              return <button key={rt} className={styles.actionBtn} onClick={onLeetCode}>💻 LeetCode</button>
            }
            return null
          })}
        </div>
      ) : (
        <div className={styles.completedBadge}>✅ 今日已修炼</div>
      )}
    </div>
  )
}
