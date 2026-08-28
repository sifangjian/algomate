import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import styles from './SolutionListPage.module.css'

export default function SolutionListPage() {
  const navigate = useNavigate()
  const [solutions, setSolutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await cardService.getSolutions()
        if (!cancelled) setSolutions(data || [])
      } catch (err) {
        if (!cancelled) setError(err.message || '加载解法列表失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const handleSolutionClick = useCallback((id) => {
    navigate(`/card/solution/${id}`)
  }, [navigate])

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

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        <h2 className={styles.pageTitle}>解法列表</h2>
        <span className={styles.count}>{solutions.length} 个解法</span>
      </div>

      {solutions.length === 0 ? (
        <div className={styles.emptyState}>
          暂无解法，去创建第一个解法吧
        </div>
      ) : (
        <div className={styles.grid}>
          {solutions.map((solution) => (
            <div
              key={solution.id}
              className={styles.card}
              onClick={() => handleSolutionClick(solution.id)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardName}>{solution.name}</span>
                {solution.technique_count > 0 && (
                  <span className={styles.techniqueCount}>
                    {solution.technique_count} 个技巧
                  </span>
                )}
              </div>
              <div className={styles.cardMeta}>
                {solution.problem_title && (
                  <span className={styles.problemTitle} title={solution.problem_title}>
                    {solution.problem_title}
                  </span>
                )}
              </div>
              <div className={styles.cardFooter}>
                <span className={styles.complexity}>
                  {solution.time_complexity || '—'} / {solution.space_complexity || '—'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}