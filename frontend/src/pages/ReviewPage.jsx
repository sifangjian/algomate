import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { cardService } from '../services/cardService'
import VariantPracticeModal from '../components/card/VariantPracticeModal'
import PanelSection from '../components/workbench/PanelSection'
import styles from './ReviewPage.module.css'

const PRIORITY_LABELS = {
  critical: '濒危',
  high: '高',
  medium: '中',
  low: '低',
}

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

// 技巧卡：轻量自检（回忆/核对）
const SELF_RATINGS = [
  { value: 'forgot', label: '忘了', color: '#f44336' },
  { value: 'struggled', label: '困难', color: '#ff9800' },
  { value: 'passed', label: '通过', color: '#4caf50' },
  { value: 'mastered', label: '熟练', color: '#2196f3' },
]

// 题卡：重做原题（程序性提取练习），用户自标记 AC / 卡住
const REDONE_RATINGS = [
  { value: 'redone_ac', label: '已 AC', color: '#4caf50' },
  { value: 'redone_stuck', label: '卡住了', color: '#f44336' },
]

export default function ReviewPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const filter = searchParams.get('filter') || 'all' // all | critical | done
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeReview, setActiveReview] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [completedTasks, setCompletedTasks] = useState(new Set())
  const [variantModal, setVariantModal] = useState(null) // { problemId, problemTitle }

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

  const setFilter = useCallback((f) => {
    if (f === 'all') setSearchParams({})
    else setSearchParams({ filter: f })
  }, [setSearchParams])

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
      await cardService.completeReview(cardId, rating)
      setCompletedTasks((prev) => new Set([...prev, cardId]))
      setActiveReview(null)
    } catch (err) {
      console.error('完成修炼失败:', err)
    } finally {
      setSubmitting(false)
    }
  }, [])

  const handleBack = useCallback(() => {
    navigate('/')
  }, [navigate])

  const pending = tasks.filter((t) => !completedTasks.has(t.card_id))
  let visibleTasks = pending
  if (filter === 'critical') {
    visibleTasks = pending.filter((t) => t.priority === 'critical' || (t.card_durability ?? 100) < 30)
  } else if (filter === 'done') {
    visibleTasks = tasks.filter((t) => completedTasks.has(t.card_id))
  }
  visibleTasks = [...visibleTasks].sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9))

  const filterTabs = [
    { key: 'all', label: `待复习 (${pending.length})` },
    { key: 'critical', label: `濒危 (${pending.filter((t) => t.priority === 'critical' || (t.card_durability ?? 100) < 30).length})` },
    { key: 'done', label: `已完成 (${completedTasks.size})` },
  ]

  return (
    <div className={styles.page}>
      <PanelSection number="00" title="today.review — 今日修炼" path="/review">
        <div className={styles.toolbar}>
          <button className={styles.backButton} onClick={handleBack}>← 返回</button>
          <div className={styles.filterTabs}>
            {filterTabs.map((tab) => (
              <button
                key={tab.key}
                className={`${styles.filterTab} ${filter === tab.key ? styles.filterTabActive : ''}`}
                onClick={() => setFilter(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className={styles.stateBox}>加载中...</div>
        ) : error ? (
          <div className={styles.stateBox}>
            <div className={styles.errorTitle}>加载失败</div>
            <div className={styles.errorMessage}>{error}</div>
            <button className={styles.backButton} onClick={handleBack}>返回首页</button>
          </div>
        ) : visibleTasks.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>✓</div>
            <div className={styles.emptyTitle}>
              {filter === 'done' ? '暂无已完成任务' : filter === 'critical' ? '暂无濒危任务' : '今日无待复习任务'}
            </div>
            <div className={styles.emptyDesc}>所有卡牌都已复习完毕，继续保持！</div>
          </div>
        ) : (
          <div className={styles.grid}>
            {visibleTasks.map((task) => {
              const isActive = activeReview === task.card_id
              const isCompleted = completedTasks.has(task.card_id)
              const isProblem = task.card_type === 'problem'

              return (
                <div
                  key={task.task_id}
                  className={`${styles.taskCard} ${styles[`prio_${task.priority}`]} ${isActive ? styles.taskCardActive : ''} ${isCompleted ? styles.taskCardCompleted : ''}`}
                >
                  <div className={styles.cardTop}>
                    <div className={styles.cardInfo}>
                      <span className={styles.cardName}>{task.card_name}</span>
                      {isProblem ? (
                        <span className={`${styles.tag} ${styles.tagProblem}`}>重做原题</span>
                      ) : (
                        task.card_algorithm_type && (
                          <span className={styles.tag}>{task.card_algorithm_type}</span>
                        )
                      )}
                    </div>
                    <span className={`${styles.priorityBadge} ${styles[`badge_${task.priority}`]}`}>
                      {PRIORITY_LABELS[task.priority]}
                    </span>
                  </div>

                  <div className={styles.cardMeta}>
                    <span>耐久度 {task.card_durability}/{task.max_durability}</span>
                    <span>·</span>
                    <span>等级 {task.review_level}</span>
                    {task.next_review_date && (
                      <>
                        <span>·</span>
                        <span>下次 {task.next_review_date}</span>
                      </>
                    )}
                  </div>

                  {task.reason && <div className={styles.cardReason}>{task.reason}</div>}

                  {isProblem && (
                    <div className={styles.problemActions}>
                      {task.leetcode_link && (
                        <a className={styles.redoBtn} href={task.leetcode_link} target="_blank" rel="noopener noreferrer">
                          去 LeetCode 重做 ↗
                        </a>
                      )}
                      {task.has_variants && (
                        <button
                          className={styles.variantBtn}
                          onClick={() => setVariantModal({ problemId: task.problem_id, problemTitle: task.card_name })}
                          disabled={isActive}
                        >
                          变体练习 ({task.variants?.length || 0})
                        </button>
                      )}
                    </div>
                  )}

                  {!isActive && !isCompleted && (
                    <button className={styles.startBtn} onClick={() => handleStartReview(task)} disabled={activeReview !== null}>
                      {isProblem ? '开始重做' : '开始修炼'}
                    </button>
                  )}

                  {isActive && (
                    <div className={styles.ratingSection}>
                      <div className={styles.ratingLabel}>
                        {isProblem ? '重做原题后自评：' : '自评本次修炼效果：'}
                      </div>
                      <div className={styles.ratingBtns}>
                        {(isProblem ? REDONE_RATINGS : SELF_RATINGS).map((rating) => (
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

                  {isCompleted && <div className={styles.doneMark}>✓ 已完成</div>}
                </div>
              )
            })}
          </div>
        )}
      </PanelSection>

      {variantModal && (
        <VariantPracticeModal
          open={!!variantModal}
          problemId={variantModal.problemId}
          problemTitle={variantModal.problemTitle}
          onClose={() => setVariantModal(null)}
          onSaved={() => {
            setVariantModal(null)
          }}
        />
      )}
    </div>
  )
}
