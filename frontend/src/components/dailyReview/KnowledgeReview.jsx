import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../../services/cardService'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import ExamplesList from '../card/ExamplesList'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './KnowledgeReview.module.css'

function parseJSON(value) {
  if (!value) return null
  if (typeof value === 'object') return value
  try { return JSON.parse(value) } catch { return null }
}

function isEmpty(val) {
  if (val == null) return true
  if (typeof val === 'string') return val.trim() === ''
  if (Array.isArray(val)) return val.length === 0
  if (typeof val === 'object') return Object.values(val).every(v => isEmpty(v))
  return false
}

function ContentBlock({ icon, label, content }) {
  if (isEmpty(content)) return null
  return (
    <div className={styles.contentBlock}>
      <div className={styles.contentLabel}>
        <span className={styles.contentIcon}>{icon}</span>
        {label}
      </div>
      <div className={styles.contentBody}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(content)}</ReactMarkdown>
      </div>
    </div>
  )
}

export default function KnowledgeReview({ task, onComplete, onBack }) {
  const [card, setCard] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    cardService.getById(task.card_id)
      .then(data => setCard(data?.data || data))
      .catch(() => showToast('加载知识回顾失败', 'error'))
      .finally(() => setLoading(false))
  }, [task.card_id])

  if (loading) {
    return <div className={styles.loading}>加载中...</div>
  }

  if (!card) {
    return (
      <div className={styles.container}>
        <button className={styles.backBtn} onClick={onBack}>← 返回任务列表</button>
        <div className={styles.empty}>该卡牌暂无知识内容</div>
      </div>
    )
  }

  const basic = parseJSON(card.basic_content) || {}
  const practical = parseJSON(card.practical_content) || {}
  const advanced = parseJSON(card.advanced_content) || {}
  const hasBasic = !isEmpty(basic.concept_definition) || !isEmpty(basic.features) || !isEmpty(basic.confusing_concepts)
  const hasPractical = !isEmpty(practical.examples) || !isEmpty(practical.applicable_scenarios) || !isEmpty(practical.precautions)
  const hasAdvanced = !isEmpty(advanced.common_mistakes) || !isEmpty(advanced.extensions) || !isEmpty(advanced.advanced_solutions)
  const hasNotes = !isEmpty(card.my_notes)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.cardIcon}>{card.algorithm_type === 'Dynamic Programming' ? '🎯' : card.algorithm_type === 'Graph' ? '🕸️' : card.algorithm_type === 'Sorting' ? '📊' : card.algorithm_type === 'Tree' ? '🌲' : '📜'}</span>
          <h2 className={styles.title}>{task.card_name}</h2>
        </div>
        <button className={styles.backBtn} onClick={onBack}>← 返回</button>
      </div>

      {/* 基础层 */}
      {hasBasic && (
        <div className={`${styles.tier} ${styles.tierBasic}`}>
          <div className={styles.tierHeader}>
            <span className={styles.tierIcon}>📘</span>
            <span>基础知识</span>
          </div>
          <div className={styles.tierBody}>
            <ContentBlock icon="💡" label="概念定义" content={basic.concept_definition} />
            <ContentBlock icon="🔑" label="核心特点" content={basic.features} />
            <ContentBlock icon="🔀" label="易混淆概念" content={basic.confusing_concepts} />
          </div>
        </div>
      )}

      {/* 实战层 */}
      {hasPractical && (
        <div className={`${styles.tier} ${styles.tierPractical}`}>
          <div className={styles.tierHeader}>
            <span className={styles.tierIcon}>⚔️</span>
            <span>实战应用</span>
          </div>
          <div className={styles.tierBody}>
            {!isEmpty(practical.examples) && practical.examples.length > 0 && (
              <div className={styles.contentBlock}>
                <div className={styles.contentLabel}>
                  <span className={styles.contentIcon}>📝</span>
                  例题
                </div>
                <ExamplesList examples={practical.examples} />
              </div>
            )}
            <ContentBlock icon="📋" label="适用场景" content={practical.applicable_scenarios} />
            <ContentBlock icon="⚠️" label="注意事项" content={practical.precautions} />
          </div>
        </div>
      )}

      {/* 进阶层 */}
      {hasAdvanced && (
        <div className={`${styles.tier} ${styles.tierAdvanced}`}>
          <div className={styles.tierHeader}>
            <span className={styles.tierIcon}>🚀</span>
            <span>进阶拓展</span>
          </div>
          <div className={styles.tierBody}>
            <ContentBlock icon="❌" label="常见错误" content={advanced.common_mistakes} />
            <ContentBlock icon="🔄" label="拓展方向" content={advanced.extensions} />
            <ContentBlock icon="⚡" label="高级解法" content={advanced.advanced_solutions} />
          </div>
        </div>
      )}

      {/* 个人笔记 */}
      {hasNotes && (
        <div className={`${styles.tier} ${styles.tierNotes}`}>
          <div className={styles.tierHeader}>
            <span className={styles.tierIcon}>📝</span>
            <span>我的心得</span>
          </div>
          <div className={styles.tierBody}>
            <div className={styles.contentBody}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{card.my_notes}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      <div className={styles.footer}>
        <Button variant="accent" onClick={onComplete}>✅ 完成回顾</Button>
      </div>
    </div>
  )
}
