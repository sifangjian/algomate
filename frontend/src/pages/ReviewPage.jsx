import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import { showToast } from '../components/ui/Toast/index'
import styles from './ReviewPage.module.css'

const PRIORITY_LABELS = {
  critical: '紧急',
  high: '高',
  medium: '中',
  low: '低',
}

const PRIORITY_CLASSES = {
  critical: styles.priorityCritical,
  high: styles.priorityHigh,
  medium: styles.priorityMedium,
  low: styles.priorityLow,
}

export default function ReviewPage() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState([])
  const [summary, setSummary] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [completingIds, setCompletingIds] = useState(new Set())

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await cardService.getTodayReviewTasks()
      const data = result?.data || result
      setTasks(data.tasks || [])
      setSummary({
        total: data.total_count || 0,
        endangered: data.endangered_count || 0,
        due: data.due_count || 0,
        hasCards: data.has_cards ?? true,
      })
    } catch (err) {
      setError(err.message || '加载修炼任务失败')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const handleComplete = useCallback(async (task) => {
    setCompletingIds(prev => new Set(prev).add(task.card_id))
    try {
      const reviewType = task.review_types?.[0] || 'content_review'
      await cardService.completeReviewV1(task.card_id, reviewType)
      showToast(`「${task.card_name}」修炼完成`, 'success')
      // 移除已完成的任务
      setTasks(prev => prev.filter(t => t.card_id !== task.card_id))
    } catch (err) {
      showToast(`修炼失败: ${err.message}`, 'error')
    } finally {
      setCompletingIds(prev => {
        const next = new Set(prev)
        next.delete(task.card_id)
        return next
      })
    }
  }, [])

  const handleCardClick = useCallback((cardId) => {
    navigate(`/study/${cardId}`)
  }, [navigate])

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>⚔️ 今日修炼</h1>
        </div>
        <LoadingScreen />
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>⚔️ 今日修炼</h1>
        </div>
        <div className={styles.emptyState}>
          <p className={styles.errorText}>{error}</p>
          <button className={styles.retryBtn} onClick={fetchTasks}>重新加载</button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>⚔️ 今日修炼</h1>
      </div>

      {summary.hasCards && (
        <div className={styles.summary}>
          <span className={styles.summaryItem}>
            待修炼: <strong>{summary.total}</strong>
          </span>
          {summary.endangered > 0 && (
            <span className={`${styles.summaryItem} ${styles.summaryCritical}`}>
              濒危: <strong>{summary.endangered}</strong>
            </span>
          )}
          {summary.due > 0 && (
            <span className={styles.summaryItem}>
              到期: <strong>{summary.due}</strong>
            </span>
          )}
        </div>
      )}

      <div className={styles.taskList}>
        {tasks.length === 0 ? (
          <div className={styles.emptyState}>
            <p className={styles.emptyText}>
              {summary.hasCards ? '今日没有待修炼的卡牌 🎉' : '暂无卡牌，先去图鉴创建卡牌吧'}
            </p>
            {!summary.hasCards && (
              <button className={styles.goBtn} onClick={() => navigate('/')}>
                前往图鉴
              </button>
            )}
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.task_id || task.card_id}
              className={styles.taskCard}
              onClick={() => handleCardClick(task.card_id)}
            >
              <div className={styles.taskHeader}>
                <span className={`${styles.priority} ${PRIORITY_CLASSES[task.priority] || ''}`}>
                  {PRIORITY_LABELS[task.priority] || task.priority}
                </span>
                <span className={styles.taskType}>
                  {task.task_type === 'critical_review' ? '濒危修复' : '曲线复习'}
                </span>
              </div>
              <h3 className={styles.taskName}>{task.card_name}</h3>
              <div className={styles.taskMeta}>
                {task.card_algorithm_type && (
                  <span className={styles.tag}>{task.card_algorithm_type}</span>
                )}
                {task.review_level != null && (
                  <span className={styles.tag}>Lv.{task.review_level}</span>
                )}
                {task.card_durability != null && (
                  <span className={styles.tag} style={{
                    color: task.card_durability > 60 ? '#34d399' : task.card_durability >= 30 ? '#fbbf24' : '#f87171'
                  }}>
                    耐久 {Math.round(task.card_durability)}%
                  </span>
                )}
              </div>
              {task.reason && (
                <p className={styles.reason}>{task.reason}</p>
              )}
              <button
                className={styles.completeBtn}
                onClick={(e) => {
                  e.stopPropagation()
                  handleComplete(task)
                }}
                disabled={completingIds.has(task.card_id)}
              >
                {completingIds.has(task.card_id) ? '修炼中...' : '开始修炼'}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}