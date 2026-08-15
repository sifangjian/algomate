import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../../stores/hallStore'
import { ALGORITHM_ICONS } from '../../constants/algorithmConstants'
import { Icon } from '../ui/Icons'
import styles from './TopicGrid.module.css'

function findIcon(topicName) {
  for (const [key, icon] of Object.entries(ALGORITHM_ICONS)) {
    if (topicName.includes(key)) {
      return icon
    }
  }
  return 'book'
}

export default function TopicGrid() {
  const navigate = useNavigate()
  const { overview, overviewLoading, fetchTopicOverview } = useHallStore()

  useEffect(() => {
    fetchTopicOverview()
  }, [fetchTopicOverview])

  const handleTopicClick = useCallback((topicKey) => {
    navigate(`/topic/${encodeURIComponent(topicKey)}`)
  }, [navigate])

  const handleBannerClick = useCallback((e, filter) => {
    e.stopPropagation()
    navigate(`/techniques?${filter}`)
  }, [navigate])

  if (overviewLoading) {
    return <div className={styles.loadingState}>加载中...</div>
  }

  if (!overview || !overview.topics?.length) {
    return <div className={styles.loadingState}>暂无数据</div>
  }

  const { topics, total_due, total_critical } = overview

  const sortedTopics = [...topics].sort((a, b) => {
    const aHasDue = a.due_technique_count > 0 || a.critical_technique_count > 0
    const bHasDue = b.due_technique_count > 0 || b.critical_technique_count > 0
    if (aHasDue && !bHasDue) return -1
    if (!aHasDue && bHasDue) return 1
    return b.technique_count - a.technique_count
  })

  return (
    <div className={styles.topicGrid}>
      {total_due > 0 && (
        <div className={`${styles.reviewBanner} ${styles.due}`}>
          <span>今日有 {total_due} 个技巧待复习</span>
          <span className={styles.bannerLink} onClick={(e) => handleBannerClick(e, 'due_only=true')}>查看待复习技巧 →</span>
        </div>
      )}
      {total_critical > 0 && (
        <div className={`${styles.reviewBanner} ${styles.critical}`}>
          <span>今日有 {total_critical} 个濒危技巧</span>
          <span className={styles.bannerLink} onClick={(e) => handleBannerClick(e, 'due_only=true')}>查看待复习技巧 →</span>
        </div>
      )}

      <div className={styles.grid}>
        {sortedTopics.map((topic) => {
          const icon = findIcon(topic.name)
          const hasDue = topic.due_technique_count > 0
          const hasCritical = topic.critical_technique_count > 0

          return (
            <div
              key={topic.key}
              className={styles.topicCard}
              onClick={() => handleTopicClick(topic.key)}
            >
              <div className={styles.topicIcon}>
                <Icon name={icon} size={24} color="var(--accent)" />
              </div>
              <div className={styles.topicName}>{topic.name}</div>
              <div className={styles.topicStats}>
                <span>题目 {topic.problem_count}</span>
                <span>解法 {topic.solution_count}</span>
                <span>技巧 {topic.technique_count}</span>
              </div>
              <div className={styles.badges}>
                {hasDue && (
                  <span className={`${styles.badge} ${styles.badgeDue}`}>
                    待复习 {topic.due_technique_count}
                  </span>
                )}
                {hasCritical && (
                  <span className={`${styles.badge} ${styles.badgeCritical}`}>
                    濒危 {topic.critical_technique_count}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}