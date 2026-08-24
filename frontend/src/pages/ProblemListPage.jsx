import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import styles from './ProblemListPage.module.css'

const DIFFICULTIES = ['all', 'easy', 'medium', 'hard']

const DIFFICULTY_LABELS = {
  all: '全部',
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

const STATUS_LABELS = {
  untried: '未尝试',
  accepted: '已通过',
  optimal: '最优解',
}

export default function ProblemListPage() {
  const navigate = useNavigate()
  const [problems, setProblems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const params = {}
        if (filter !== 'all') params.difficulty = filter
        const data = await cardService.getProblems(params)
        if (!cancelled) setProblems(data || [])
      } catch (err) {
        if (!cancelled) setError(err.message || '加载题目列表失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [filter])

  const handleProblemClick = useCallback((id) => {
    navigate(`/card/problem/${id}`)
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
        <h2 className={styles.pageTitle}>题目列表</h2>
        <span className={styles.count}>{problems.length} 道题目</span>
      </div>

      <div className={styles.filters}>
        {DIFFICULTIES.map((d) => (
          <button
            key={d}
            className={`${styles.filterBtn} ${filter === d ? styles.filterBtnActive : ''}`}
            onClick={() => setFilter(d)}
          >
            {DIFFICULTY_LABELS[d]}
          </button>
        ))}
      </div>

      {problems.length === 0 ? (
        <div className={styles.emptyState}>
          暂无题目，去创建第一道题目吧
        </div>
      ) : (
        <div className={styles.grid}>
          {problems.map((problem) => (
            <div
              key={problem.id}
              className={styles.card}
              onClick={() => handleProblemClick(problem.id)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardName}>{problem.title}</span>
                <span className={`${styles.difficultyBadge} ${styles[`difficulty${problem.difficulty.charAt(0).toUpperCase() + problem.difficulty.slice(1)}`]}`}>
                  {DIFFICULTY_LABELS[problem.difficulty]}
                </span>
              </div>
              <div className={styles.cardMeta}>
                <span className={`${styles.statusTag} ${styles[`status${problem.my_status.charAt(0).toUpperCase() + problem.my_status.slice(1)}`]}`}>
                  {STATUS_LABELS[problem.my_status]}
                </span>
                <span>{problem.solution_count} 个解法</span>
              </div>
              {problem.tags && problem.tags.length > 0 && (
                <div className={styles.tags}>
                  {problem.tags.map((tag, i) => (
                    <span key={i} className={styles.tag}>{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}