import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../services/cardService'
import { useUserStore } from '../stores/userStore'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import PostReviewGuide from '../components/guide/PostReviewGuide'
import ReviewStatsBar from '../components/dailyReview/ReviewStatsBar'
import TaskCard from '../components/dailyReview/TaskCard'
import KnowledgeReview from '../components/dailyReview/KnowledgeReview'
import QuickQuiz from '../components/dailyReview/QuickQuiz'
import LeetCodeChallenge from '../components/dailyReview/LeetCodeChallenge'
import styles from './DailyReview.module.css'

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

export default function DailyReview() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [completedTaskIds, setCompletedTaskIds] = useState(new Set())
  const [reviewMode, setReviewMode] = useState(null)
  const [selectedTask, setSelectedTask] = useState(null)
  const [reviewStats, setReviewStats] = useState(null)
  const [endangeredCount, setEndangeredCount] = useState(0)
  const [hasCards, setHasCards] = useState(true)
  const [guide, setGuide] = useState(null)
  const updateUserStats = useUserStore(s => s.updateStats)

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      const data = await cardService.getTodayReviewTasks()
      const resp = data?.data || data
      setTasks(resp?.tasks || [])
      setEndangeredCount(resp?.endangered_count || 0)
      setHasCards(resp?.has_cards !== false)
    } catch {
      // toast handled in sub-components
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTasks()
    cardService.getReviewStats().then(data => {
      setReviewStats(data)
      const stats = data?.data || data
      if (stats) {
        updateUserStats({
          totalCards: stats.total_cards ?? stats.total_review_count ?? 0,
          streakDays: stats.weekly_review_days ?? 0,
          totalReviews: stats.total_review_count ?? 0,
        })
      }
    }).catch(() => {})
  }, [fetchTasks])

  const sortedTasks = (() => {
    return [...tasks].sort((a, b) => {
      const pa = PRIORITY_ORDER[a.priority] ?? 3
      const pb = PRIORITY_ORDER[b.priority] ?? 3
      return pa - pb
    })
  })()

  const handleReview = useCallback((task) => {
    setSelectedTask(task)
    setReviewMode('review')
  }, [])

  const handleQuiz = useCallback((task) => {
    setSelectedTask(task)
    setReviewMode('quiz')
  }, [])

  const handleLeetCode = useCallback((task) => {
    setSelectedTask(task)
    setReviewMode('leetcode')
  }, [])

  const handleComplete = useCallback(async (reviewType) => {
    if (!selectedTask) return
    try {
      const data = await cardService.completeReviewV1(selectedTask.card_id, reviewType)
      const resp = data?.data || data
      setCompletedTaskIds(prev => new Set([...prev, selectedTask.card_id]))
      if (resp?.guide) setGuide(resp.guide)
      setReviewMode(null)
      setSelectedTask(null)
    } catch {
      // handled in sub-components
    }
  }, [selectedTask])

  const handleBack = useCallback(() => {
    setReviewMode(null)
    setSelectedTask(null)
    setGuide(null)
  }, [])

  if (loading) return <LoadingScreen />

  return (
    <div className={`${styles.container} page-container`}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>📋 每日修炼</h1>
        <p className={styles.pageSubtitle}>巩固算法知识，保持卡牌耐久</p>
      </div>

      <ReviewStatsBar
        completedCount={completedTaskIds.size}
        totalCount={tasks.length}
        weeklyDays={reviewStats?.weekly_review_days}
        totalReviews={reviewStats?.total_review_count}
        endangeredCount={endangeredCount}
      />

      {reviewMode === 'review' && selectedTask && (
        <KnowledgeReview
          task={selectedTask}
          onComplete={() => handleComplete('content_review')}
          onBack={handleBack}
        />
      )}

      {reviewMode === 'quiz' && selectedTask && (
        <QuickQuiz
          task={selectedTask}
          onComplete={() => handleComplete('quick_quiz')}
          onBack={handleBack}
        />
      )}

      {reviewMode === 'leetcode' && selectedTask && (
        <LeetCodeChallenge
          task={selectedTask}
          onComplete={() => handleComplete('leetcode_challenge')}
          onBack={handleBack}
        />
      )}

      {!reviewMode && (
        <>
          {tasks.length === 0 ? (
            <div className={styles.emptyState}>
              <span className={styles.emptyIcon}>📋</span>
              {!hasCards ? (
                <p className={styles.emptyText}>修习更多算法技巧后，这里会出现每日修炼任务</p>
              ) : (
                <p className={styles.emptyText}>今日没有待修炼任务，继续保持！🎉</p>
              )}
            </div>
          ) : (
            <div className={styles.taskList}>
              {sortedTasks.map((task) => (
                <TaskCard
                  key={task.task_id}
                  task={task}
                  isCompleted={completedTaskIds.has(task.card_id)}
                  onReview={() => handleReview(task)}
                  onQuiz={() => handleQuiz(task)}
                  onLeetCode={() => handleLeetCode(task)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {guide && <PostReviewGuide guide={guide} scene="after_review" />}
    </div>
  )
}
