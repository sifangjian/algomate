import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import styles from './TechniqueListPage.module.css'

export default function TechniqueListPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const topic = searchParams.get('topic') || ''
  const dueOnly = searchParams.get('due_only') === 'true'

  const [techniques, setTechniques] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const params = {}
        if (topic) params.algorithm_type = topic
        if (dueOnly) params.due_only = true
        const data = await cardService.getTechniques(params)
        if (!cancelled) setTechniques(data || [])
      } catch (err) {
        if (!cancelled) setError(err.message || '加载技巧列表失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [topic, dueOnly])

  const handleTechniqueClick = useCallback((id) => {
    navigate(`/card/technique/${id}`)
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
        <h2 className={styles.pageTitle}>{topic} — 技巧列表</h2>
        <span className={styles.count}>{techniques.length} 个技巧</span>
      </div>

      {techniques.length === 0 ? (
        <div className={styles.emptyState}>
          暂无技巧，去创建第一个技巧卡吧
        </div>
      ) : (
        <div className={styles.grid}>
          {techniques.map((tech) => (
            <div
              key={tech.id}
              className={styles.card}
              onClick={() => handleTechniqueClick(tech.id)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardName}>{tech.name}</span>
                {tech.review_status !== 'normal' && (
                  <span className={`${styles.badge} ${styles[`badge${tech.review_status}`]}`}>
                    {tech.review_status === 'due' ? '待复习' : '濒危'}
                  </span>
                )}
              </div>
              <div className={styles.cardMeta}>
                <span>{tech.category}</span>
                <span>熟练度: {'★'.repeat(tech.proficiency)}{'☆'.repeat(5 - tech.proficiency)}</span>
                <span>{tech.solution_count} 个解法</span>
              </div>
              {tech.use_cases && (
                <div className={styles.cardDesc}>{tech.use_cases}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}