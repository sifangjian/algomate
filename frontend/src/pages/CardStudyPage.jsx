import { useState, useEffect, memo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import { cardService } from '../services/cardService'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import PrerequisiteSelector from '../components/hall/PrerequisiteSelector'
import styles from './CardStudyPage.module.css'

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

const SolutionItem = memo(function SolutionItem({ solution }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className={styles.solutionItem}>
      <button className={styles.solutionHeader} onClick={() => setExpanded(p => !p)}>
        <span className={styles.solutionName}>{solution.name || '解法'}</span>
        {solution.complexity && (
          <span className={styles.complexityTag}>{solution.complexity}</span>
        )}
        <span className={`${styles.toggle} ${expanded ? styles.toggleOpen : ''}`}>▸</span>
      </button>
      {expanded && (
        <div className={styles.solutionBody}>
          {solution.principle && (
            <MarkdownRenderer content={solution.principle} className={styles.mdContent} />
          )}
          {solution.code && (
            <pre className={styles.codeBlock}><code>{solution.code}</code></pre>
          )}
        </div>
      )}
    </div>
  )
})

const ExampleCard = memo(function ExampleCard({ example, index }) {
  const [expanded, setExpanded] = useState(true)
  return (
    <div className={styles.exampleCard}>
      <button className={styles.exampleHeader} onClick={() => setExpanded(p => !p)}>
        <span className={styles.exampleIndex}>#{index + 1}</span>
        <span className={styles.exampleTitle}>{example.title || `例题 ${index + 1}`}</span>
        <span className={`${styles.toggle} ${expanded ? styles.toggleOpen : ''}`}>▸</span>
      </button>
      {expanded && (
        <div className={styles.exampleBody}>
          {example.problem && (
            <MarkdownRenderer content={example.problem} className={styles.mdContent} />
          )}
          {example.solutions?.length > 0 && (
            <div className={styles.solutionsList}>
              {example.solutions.map((sol, i) => (
                <SolutionItem key={i} solution={sol} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
})

function FieldRow({ label, children }) {
  if (!children) return null
  return (
    <div className={styles.fieldRow}>
      <span className={styles.fieldLabel}>{label}</span>
      {children}
    </div>
  )
}

export default function CardStudyPage() {
  const { cardId } = useParams()
  const navigate = useNavigate()
  const { selectedCard, fetchCardById, clearSelectedCard } = useHallStore()
  const [loading, setLoading] = useState(true)
  const [cardPrerequisites, setCardPrerequisites] = useState([])

  useEffect(() => {
    if (cardId) {
      setLoading(true)
      fetchCardById(cardId).finally(() => setLoading(false))
    }
    return () => clearSelectedCard()
  }, [cardId, fetchCardById, clearSelectedCard])

  useEffect(() => {
    if (selectedCard?.id) {
      cardService.getLinks(selectedCard.id).then(links => {
        const prereqs = (Array.isArray(links) ? links : [])
          .filter(l => l.link_type === 'prerequisite' && l.direction === 'incoming')
          .map(l => ({ id: l.source_card_id, name: l.source_card_name }))
        setCardPrerequisites(prereqs)
      }).catch(() => {})
    }
  }, [selectedCard?.id])

  const handleBack = () => navigate('/')

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={handleBack}>← 返回</button>
          <h1 className={styles.title}>卡牌详情</h1>
        </div>
        <div className={styles.loadingHint}>加载中...</div>
      </div>
    )
  }

  if (!selectedCard) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={handleBack}>← 返回</button>
          <h1 className={styles.title}>卡牌详情</h1>
        </div>
        <div className={styles.emptyHint}>未找到卡牌数据</div>
      </div>
    )
  }

  const card = selectedCard
  const basic = parseJSON(card.basic_content) || {}
  const practical = parseJSON(card.practical_content) || {}
  const advanced = parseJSON(card.advanced_content) || {}

  const basicEmpty = isEmpty(basic.concept_definition) && isEmpty(basic.features) && isEmpty(basic.confusing_concepts)
  const practicalEmpty = isEmpty(practical.examples) && isEmpty(practical.applicable_scenarios) && isEmpty(practical.precautions)
  const advancedEmpty = isEmpty(advanced.common_mistakes) && isEmpty(advanced.extensions) && isEmpty(advanced.advanced_solutions) && isEmpty(card.my_notes)
  const allEmpty = basicEmpty && practicalEmpty && advancedEmpty

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={handleBack}>← 返回</button>
        <h1 className={styles.title}>{card.algorithm_type || card.name}</h1>
      </div>

      <div className={styles.content}>
        {allEmpty ? (
          <div className={styles.emptyHint}>暂无学习内容</div>
        ) : (
          <>
            {/* 基础维度 */}
            {!basicEmpty && (
              <section className={styles.dimension} style={{ borderLeftColor: '#6366f1' }}>
                <div className={styles.dimensionHeader}>
                  <span>📘 基础</span>
                </div>
                <div className={styles.dimensionBody}>
                  {basic.concept_definition && (
                    <FieldRow label="概念定义">
                      <MarkdownRenderer content={basic.concept_definition} className={styles.mdContent} />
                    </FieldRow>
                  )}
                  {basic.features && (
                    <FieldRow label="特点">
                      <MarkdownRenderer content={basic.features} className={styles.mdContent} />
                    </FieldRow>
                  )}
                  {basic.confusing_concepts && (
                    <FieldRow label="易混淆概念">
                      <div className={styles.highlightBlock}>
                        <MarkdownRenderer content={basic.confusing_concepts} className={styles.mdContent} />
                      </div>
                    </FieldRow>
                  )}
                </div>
              </section>
            )}

            {/* 实战维度 */}
            {!practicalEmpty && (
              <section className={styles.dimension} style={{ borderLeftColor: '#10b981' }}>
                <div className={styles.dimensionHeader}>
                  <span>⚔️ 实战</span>
                </div>
                <div className={styles.dimensionBody}>
                  {practical.examples?.length > 0 && (
                    <div className={styles.examplesList}>
                      {practical.examples.map((ex, i) => (
                        <ExampleCard key={i} example={ex} index={i} />
                      ))}
                    </div>
                  )}
                  {practical.applicable_scenarios && (
                    <FieldRow label="适用场景">
                      <MarkdownRenderer content={practical.applicable_scenarios} className={styles.mdContent} />
                    </FieldRow>
                  )}
                  {practical.precautions && (
                    <FieldRow label="注意事项">
                      <MarkdownRenderer content={practical.precautions} className={styles.mdContent} />
                    </FieldRow>
                  )}
                </div>
              </section>
            )}

            {/* 进阶维度 */}
            {!advancedEmpty && (
              <section className={styles.dimension} style={{ borderLeftColor: '#8b5cf6' }}>
                <div className={styles.dimensionHeader}>
                  <span>🚀 进阶</span>
                </div>
                <div className={styles.dimensionBody}>
                  {advanced.common_mistakes && (
                    <div className={styles.warningBlock}>
                      <span className={styles.warningLabel}>⚠️ 易错点</span>
                      <MarkdownRenderer content={advanced.common_mistakes} className={styles.mdContent} />
                    </div>
                  )}
                  {advanced.extensions && (
                    <FieldRow label="拓展方向">
                      <MarkdownRenderer content={advanced.extensions} className={styles.mdContent} />
                    </FieldRow>
                  )}
                  {advanced.advanced_solutions && (
                    <FieldRow label="高级解法">
                      <MarkdownRenderer content={advanced.advanced_solutions} className={styles.mdContent} />
                    </FieldRow>
                  )}
                  {card.my_notes && (
                    <FieldRow label="个人笔记">
                      <blockquote className={styles.noteBlock}>
                        <MarkdownRenderer content={card.my_notes} className={styles.mdContent} />
                      </blockquote>
                    </FieldRow>
                  )}
                </div>
              </section>
            )}
          </>
        )}
      </div>
      <PrerequisiteSelector cardId={card.id} currentPrerequisites={cardPrerequisites} />
    </div>
  )
}
