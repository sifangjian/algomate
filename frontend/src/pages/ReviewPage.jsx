import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import styles from './ReviewPage.module.css'

const PRIORITY_LABELS = {
  critical: '濒危',
  high: '高',
  medium: '中',
  low: '低',
}

const SELF_RATINGS = [
  { value: 'forgot', label: '忘了', color: '#f44336' },
  { value: 'struggled', label: '困难', color: '#ff9800' },
  { value: 'passed', label: '通过', color: '#4caf50' },
  { value: 'mastered', label: '熟练', color: '#2196f3' },
]

export default function ReviewPage() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeReview, setActiveReview] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [completedTasks, setCompletedTasks] = useState(new Set())

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await cardService.getTodayReviewTasks()
        if (!cancelled) {
          const data = res?.data || res
          setTasks(data?.tasks || [])
          setSummary({
            total_count: data?.total_count || 0,
            due_count: data?.due_count || 0,
            endangered_count: data?.endangered_count || 0,
            has_cards: data?.has_cards ?? true,
          })
        }
      } catch (err) {
        if (!cancelled) setError(err.message || '加载修炼任务失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const handleStartReview = useCallback(async (task) => {
    setActiveReview(task.card_id)
    try {
      await cardService.startReview(task.card_id)
    } catch (err) {
      console.error('开始修炼失败:', err)
    }
  }, [])

  const handleCompleteReview = useCallback(async (cardId, rating) => {
    setSubmitting(true)
    try {
      // Use the first available review_type from the task or default to "content_review"
      const task = tasks.find((t) => t.card_id === cardId)
      const reviewType = task?.review_types?.[0] || 'content_review'
      await cardService.completeReviewV1(cardId, reviewType)
      setCompletedTasks((prev) => new Set([...prev, cardId]))
      setActiveReview(null)
    } catch (err) {
      console.error('完成修炼失败:', err)
    } finally {
      setSubmitting(false)
    }
  }, [tasks])

  const handleBack = useCallback(() => {
    navigate('/')
  }, [navigate])

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        </div>
        <div className={styles.loadingState}>加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        </div>
        <div className={styles.errorState}>
          <div className={styles.errorTitle}>加载失败</div>
          <div className={styles.errorMessage}>{error}</div>
          <button className={styles.backButton} onClick={handleBack}>返回首页</button>
        </div>
      </div>
    )
  }

  const remainingTasks = tasks.filter((t) => !completedTasks.has(t.card_id))

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        <h2 className={styles.pageTitle}>今日修炼</h2>
        {summary && (
          <span className={styles.count}>
            {summary.total_count} 个任务
            {summary.endangered_count > 0 && ` · ${summary.endangered_count} 个濒危`}
            {summary.due_count > 0 && ` · ${summary.due_count} 个待复习`}
          </span>
        )}
      </div>

      {remainingTasks.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>✓</div>
          <div className={styles.emptyTitle}>今日无待复习任务</div>
          <div className={styles.emptyDesc}>所有卡牌都已复习完毕，继续保持！</div>
        </div>
      ) : (
        <div className={styles.list}>
          {remainingTasks.map((task) => {
            const isActive = activeReview === task.card_id
            const isCompleted = completedTasks.has(task.card_id)

            return (
              <div
                key={task.task_id}
                className={`${styles.taskCard} ${isActive ? styles.taskCardActive : ''} ${isCompleted ? styles.taskCardCompleted : ''}`}
              >
                <div className={styles.taskHeader}>
                  <div className={styles.taskInfo}>
                    <span className={styles.taskName}>{task.card_name}</span>
                    {task.card_algorithm_type && (
                      <span className={styles.algorithmTag}>{task.card_algorithm_type}</span>
                    )}
                  </div>
                  <span className={`${styles.priorityBadge} ${styles[`priority${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}`]}`}>
                    {PRIORITY_LABELS[task.priority]}
                  </span>
                </div>

                <div className={styles.taskMeta}>
                  <span>耐久度: {task.card_durability}/{task.max_durability}</span>
                  {task.next_review_date && (
                    <span>下次复习: {task.next_review_date}</span>
                  )}
                  <span>等级: {task.review_level}</span>
                </div>

                {task.reason && (
                  <div className={styles.taskReason}>{task.reason}</div>
                )}

                {!isActive && !isCompleted && (
                  <button
                    className={styles.startBtn}
                    onClick={() => handleStartReview(task)}
                    disabled={activeReview !== null}
                  >
                    开始修炼
                  </button>
                )}

                {isActive && (
                  <div className={styles.ratingSection}>
                    <div className={styles.ratingLabel}>自评本次修炼效果：</div>
                    <div className={styles.ratingBtns}>
                      {SELF_RATINGS.map((rating) => (
                        <button
                          key={rating.value}
                          className={styles.ratingBtn}
                          style={{ borderColor: rating.color, color: rating.color }}
                          onClick={() => handleCompleteReview(task.card_id, rating.value)}
                          disabled={submitting}
                        >
                          {rating.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}