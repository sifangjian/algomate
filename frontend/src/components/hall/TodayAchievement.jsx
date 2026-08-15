import { useState, useEffect } from 'react'
import { useHallStore } from '../../stores/hallStore'
import styles from './TodayAchievement.module.css'

function getMotivationalMessage(totalNew, streakDays) {
  if (totalNew === 0 && streakDays === 0) {
    return '今天还没有记录，开始你的算法之旅吧！'
  }
  if (totalNew >= 5) return '今日收获满满，太强了！'
  if (totalNew >= 3) return '不错的进度，继续保持！'
  if (totalNew >= 1) return '今天也有进步，积累就是力量！'
  if (streakDays > 0) return '今天虽然没有新增，但你的连续学习记录还在！'
  return '每天进步一点点，坚持带来大改变！'
}

export default function TodayAchievement() {
  const { todayStats, fetchTodayStats } = useHallStore()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    fetchTodayStats()
  }, [fetchTodayStats])

  useEffect(() => {
    if (todayStats) {
      const timer = setTimeout(() => setVisible(true), 100)
      return () => clearTimeout(timer)
    }
  }, [todayStats])

  if (!todayStats) return null

  const { new_problems, new_solutions, new_techniques, reviews_completed, total_new, streak_days } = todayStats
  const hasActivity = total_new > 0 || reviews_completed > 0
  const message = getMotivationalMessage(total_new, streak_days)

  return (
    <div className={`${styles.container} ${visible ? styles.visible : ''} ${hasActivity ? styles.hasActivity : styles.noActivity}`}>
      <div className={styles.mainRow}>
        <div className={styles.streakSection}>
          <span className={styles.fireIcon}>{streak_days > 0 ? '🔥' : '🕯️'}</span>
          <div className={styles.streakText}>
            <span className={styles.streakCount}>{streak_days}</span>
            <span className={styles.streakLabel}>天连续学习</span>
          </div>
        </div>

        <div className={styles.divider} />

        <div className={styles.statsRow}>
          <div className={styles.statItem}>
            <span className={styles.statIcon}>📝</span>
            <span className={styles.statValue}>{new_problems}</span>
            <span className={styles.statLabel}>新题目</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statIcon}>💡</span>
            <span className={styles.statValue}>{new_solutions}</span>
            <span className={styles.statLabel}>新解法</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statIcon}>🎯</span>
            <span className={styles.statValue}>{new_techniques}</span>
            <span className={styles.statLabel}>新技巧</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statIcon}>✅</span>
            <span className={styles.statValue}>{reviews_completed}</span>
            <span className={styles.statLabel}>已完成复习</span>
          </div>
        </div>
      </div>

      <div className={styles.messageRow}>
        <span className={styles.messageIcon}>💪</span>
        <span className={styles.messageText}>{message}</span>
      </div>
    </div>
  )
}