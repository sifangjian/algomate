import { useState, useEffect } from 'react'
import { cardService } from '../../services/cardService'
import VariantPracticeModal from '../card/VariantPracticeModal'
import PanelSection from './PanelSection'
import styles from './TodayReview.module.css'

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

export default function TodayReview() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [variantModal, setVariantModal] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const res = await cardService.getTodayReviewTasks()
        if (!cancelled) {
          const data = res?.data || res
          setTasks(data?.tasks || [])
        }
      } catch (err) {
        if (!cancelled) console.error('加载修炼任务失败:', err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const visibleTasks = [...tasks].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
  )

  return (
    <PanelSection number="02" title="today.review — 今日修炼">
      {loading ? (
        <div className={styles.stateBox}>加载中...</div>
      ) : visibleTasks.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>✓</div>
          <div className={styles.emptyTitle}>今日无待复习任务</div>
          <div className={styles.emptyDesc}>所有卡牌都已复习完毕，继续保持！</div>
        </div>
      ) : (
        <div className={styles.grid}>
          {visibleTasks.map((task) => {
            const isProblem = task.card_type === 'problem'
            const isCritical =
              task.priority === 'critical' || (task.card_durability ?? 100) < 30

            return (
              <div
                key={task.task_id}
                className={`${styles.taskCard} ${styles[`prio_${task.priority}`]}${
                  isCritical ? ` ${styles.endangered}` : ''
                }`}
              >
                {isCritical && <div className={styles.endangeredBadge}>濒危</div>}
                <div className={styles.cardTop}>
                  <div className={styles.cardInfo}>
                    <span className={styles.cardName}>{task.card_name}</span>
                    {task.card_algorithm_type && (
                      <span className={styles.cardTypeTag}>{task.card_algorithm_type}</span>
                    )}
                  </div>
                </div>

                <div className={styles.cardMeta}>
                  <span>耐久度 {task.card_durability}/{task.max_durability}</span>
                  {task.next_review_date && (
                    <>
                      <span>·</span>
                      <span>下次 {task.next_review_date}</span>
                    </>
                  )}
                </div>

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
                      >
                        变体练习 ({task.variants?.length || 0})
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {variantModal && (
        <VariantPracticeModal
          open={!!variantModal}
          problemId={variantModal.problemId}
          problemTitle={variantModal.problemTitle}
          onClose={() => setVariantModal(null)}
          onSaved={() => setVariantModal(null)}
        />
      )}
    </PanelSection>
  )
}
