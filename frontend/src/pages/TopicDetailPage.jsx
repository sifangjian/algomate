import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import { ALGORITHM_ICONS } from '../constants/algorithmConstants'
import styles from './TopicDetailPage.module.css'

function findIcon(topicName) {
  for (const [key, icon] of Object.entries(ALGORITHM_ICONS)) {
    if (topicName.includes(key)) {
      return icon
    }
  }
  return '📚'
}

const DIFFICULTY_CLASSES = {
  easy: styles.badgeEasy,
  medium: styles.badgeMedium,
  hard: styles.badgeHard,
}

export default function TopicDetailPage() {
  const { algorithmType } = useParams()
  const navigate = useNavigate()
  const decodedType = decodeURIComponent(algorithmType)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all / problem / technique / due

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const result = await cardService.getTopicDetail(decodedType)
        if (!cancelled) setData(result)
      } catch (err) {
        if (!cancelled) setError(err.message || '加载失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [decodedType])

  const handleCardClick = useCallback((cardType, id) => {
    navigate(`/card/${cardType}/${id}`)
  }, [navigate])

  const handleBack = useCallback(() => {
    navigate('/')
  }, [navigate])

  const getFilteredCards = () => {
    if (!data) return { problems: [], solutions: [], techniques: [] }
    let problems = data.problems || []
    let solutions = data.solutions || []
    let techniques = data.techniques || []

    if (filter === 'due') {
      techniques = techniques.filter(t => t.review_status !== 'normal')
    }

    return { problems, solutions, techniques }
  }

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

  const { problems, solutions, techniques } = getFilteredCards()
  const totalCards = problems.length + solutions.length + techniques.length

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <button className={styles.backButton} onClick={handleBack}>← 返回</button>
        <div className={styles.topicHeader}>
          <span className={styles.topicIcon}>{findIcon(decodedType)}</span>
          <h2 className={styles.pageTitle}>{decodedType}</h2>
        </div>
        <span className={styles.count}>{totalCards} 张卡片</span>
      </div>

      <div className={styles.filterRow}>
        {[
          { key: 'all', label: '全部' },
          { key: 'problem', label: `题目 (${problems.length})` },
          { key: 'solution', label: `解法 (${solutions.length})` },
          { key: 'technique', label: `技巧 (${techniques.length})` },
          { key: 'due', label: '待复习' },
        ].map((f) => (
          <button
            key={f.key}
            className={filter === f.key ? styles.filterActive : styles.filterBtn}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filter === 'all' || filter === 'problem' ? (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            <span className={styles.sectionIcon}>📝</span> 题目 ({problems.length})
          </h3>
          <div className={styles.cardGrid}>
            {problems.length === 0 ? (
              <div className={styles.emptyHint}>暂无题目</div>
            ) : (
              problems.map((p) => (
                <div
                  key={`problem-${p.id}`}
                  className={`${styles.card} ${styles.cardProblem}`}
                  onClick={() => handleCardClick('problem', p.id)}
                >
                  <div className={styles.cardHeader}>
                    <span className={styles.cardName}>{p.name}</span>
                    {p.difficulty && (
                      <span className={`${styles.badge} ${DIFFICULTY_CLASSES[p.difficulty] || ''}`}>
                        {p.difficulty}
                      </span>
                    )}
                  </div>
                  <div className={styles.cardMeta}>
                    <span>📖 {p.solution_count} 个解法</span>
                  </div>
                  {p.tags?.length > 0 && (
                    <div className={styles.tagsRow}>
                      {p.tags.map((tag, i) => (
                        <span key={i} className={styles.tag}>{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>
      ) : null}

      {filter === 'all' || filter === 'solution' ? (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            <span className={styles.sectionIcon}>💡</span> 解法 ({solutions.length})
          </h3>
          <div className={styles.cardGrid}>
            {solutions.length === 0 ? (
              <div className={styles.emptyHint}>暂无解法</div>
            ) : (
              solutions.map((s) => (
                <div
                  key={`solution-${s.id}`}
                  className={`${styles.card} ${styles.cardSolution}`}
                  onClick={() => handleCardClick('solution', s.id)}
                >
                  <div className={styles.cardHeader}>
                    <span className={styles.cardName}>{s.name}</span>
                  </div>
                  <div className={styles.cardMeta}>
                    {s.problem_title && <span>📖 {s.problem_title}</span>}
                    {s.solution_count > 0 && <span>🔗 {s.solution_count} 个技巧</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      ) : null}

      {filter === 'all' || filter === 'technique' || filter === 'due' ? (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>
            <span className={styles.sectionIcon}>⭐</span> 技巧 ({techniques.length})
          </h3>
          <div className={styles.cardGrid}>
            {techniques.length === 0 ? (
              <div className={styles.emptyHint}>暂无技巧</div>
            ) : (
              techniques.map((t) => (
                <div
                  key={`technique-${t.id}`}
                  className={`${styles.card} ${styles.cardTechnique} ${
                    t.review_status === 'critical' ? styles.cardCritical :
                    t.review_status === 'due' ? styles.cardDue : ''
                  }`}
                  onClick={() => handleCardClick('technique', t.id)}
                >
                  <div className={styles.cardHeader}>
                    <span className={styles.cardName}>{t.name}</span>
                    {t.review_status !== 'normal' && (
                      <span className={`${styles.badge} ${
                        t.review_status === 'critical' ? styles.badgeCritical : styles.badgeDue
                      }`}>
                        {t.review_status === 'critical' ? '濒危' : '待复习'}
                      </span>
                    )}
                  </div>
                  <div className={styles.cardMeta}>
                    {t.proficiency > 0 && (
                      <span>熟练度: {'★'.repeat(t.proficiency)}{'☆'.repeat(5 - t.proficiency)}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      ) : null}
    </div>
  )
}