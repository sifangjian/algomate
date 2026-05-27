import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../../services/cardService'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import styles from './LeetCodeChallenge.module.css'

function getDifficultyClass(difficulty) {
  const d = (difficulty || '').toLowerCase()
  if (d === 'easy') return styles.difficultyEasy
  if (d === 'hard') return styles.difficultyHard
  return styles.difficultyMedium
}

export default function LeetCodeChallenge({ task, onComplete, onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [evaluating, setEvaluating] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    cardService.getLeetCodeRecommendation(task.card_id)
      .then(res => {
        const resp = res?.data || res
        setData(resp?.data || resp)
      })
      .catch(() => {
        setError(true)
        showToast('获取LeetCode推荐失败', 'error')
      })
      .finally(() => setLoading(false))
  }, [task.card_id])

  const handleOpenLeetCode = useCallback(() => {
    if (data?.url) {
      window.open(data.url, '_blank')
    }
  }, [data])

  const handleSelfEval = useCallback(async (result) => {
    if (result === 'solved') {
      setEvaluating(true)
      try {
        await cardService.completeReviewV1(task.card_id, 'leetcode_challenge')
        showToast('LeetCode挑战完成！', 'success')
        onComplete()
      } catch {
        showToast('完成修炼失败', 'error')
      } finally {
        setEvaluating(false)
      }
    } else {
      onBack()
    }
  }, [task.card_id, onComplete, onBack])

  if (loading) {
    return <div className={styles.loading}>正在推荐LeetCode题目...</div>
  }

  if (error || !data) {
    return (
      <div className={styles.container}>
        <button className={styles.backBtn} onClick={onBack}>← 返回任务列表</button>
        <div className={styles.errorPanel}>
          <p>获取LeetCode推荐失败，请稍后重试</p>
          <Button variant="ghost" onClick={onBack}>返回</Button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>💻 LeetCode 挑战 - {task.card_name}</h2>
        <button className={styles.backBtn} onClick={onBack}>← 返回</button>
      </div>

      <div className={styles.problemCard}>
        <div className={styles.problemHeader}>
          <h3 className={styles.problemTitle}>{data.title || '推荐题目'}</h3>
          {data.difficulty && (
            <span className={`${styles.difficultyBadge} ${getDifficultyClass(data.difficulty)}`}>
              {data.difficulty}
            </span>
          )}
        </div>

        {data.description && (
          <p className={styles.problemDesc}>{data.description}</p>
        )}

        {data.url && (
          <button className={styles.openBtn} onClick={handleOpenLeetCode}>
            🔗 前往 LeetCode 解题
          </button>
        )}
      </div>

      <div className={styles.selfEval}>
        <p className={styles.selfEvalTitle}>完成后的自我评估：</p>
        <div className={styles.selfEvalBtns}>
          <button
            className={`${styles.evalBtn} ${styles.evalSolved}`}
            onClick={() => handleSelfEval('solved')}
            disabled={evaluating}
          >
            ✅ 已解决
          </button>
          <button
            className={`${styles.evalBtn} ${styles.evalUnsolved}`}
            onClick={() => handleSelfEval('unsolved')}
          >
            ❌ 未解决
          </button>
          <button
            className={`${styles.evalBtn} ${styles.evalSkip}`}
            onClick={() => handleSelfEval('skip')}
          >
            ⏭️ 跳过
          </button>
        </div>
      </div>
    </div>
  )
}
