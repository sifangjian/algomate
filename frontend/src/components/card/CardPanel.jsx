import { useState, useCallback } from 'react'
import { cardService } from '../../services/cardService'
import CreateCardModal from './CreateCardModal'
import { showToast } from '../ui/Toast/index'
import CodeBlock from '../ui/CodeBlock'
import MarkdownRenderer from '../ui/MarkdownRenderer'
import styles from './CardPanel.module.css'

const DIFFICULTY_LABELS = { easy: '简单', medium: '中等', hard: '困难' }
const DIFFICULTY_CLASSES = { easy: styles.badgeEasy, medium: styles.badgeMedium, hard: styles.badgeHard }

const REVIEW_STATUS_LABELS = { normal: '正常', due: '到期', critical: '紧急' }
const REVIEW_STATUS_CLASSES = { normal: styles.badgeNormal, due: styles.badgeDue, critical: styles.badgeCritical }

function ProblemCard({ data, onNavigate, onRefresh }) {
  const [collapsedSolutions, setCollapsedSolutions] = useState(new Set())
  const [compareSelection, setCompareSelection] = useState([])
  const [solutionModal, setSolutionModal] = useState({ open: false })
  const [deleteSolutionId, setDeleteSolutionId] = useState(null)
  const [deleteSolutionName, setDeleteSolutionName] = useState('')

  const toggleSolution = useCallback((solId) => {
    setCollapsedSolutions(prev => {
      const next = new Set(prev)
      if (next.has(solId)) next.delete(solId)
      else next.add(solId)
      return next
    })
  }, [])

  const toggleCompareSelection = useCallback((solId) => {
    setCompareSelection(prev => {
      if (prev.includes(solId)) {
        return prev.filter(id => id !== solId)
      }
      if (prev.length >= 2) return [prev[1], solId]
      return [...prev, solId]
    })
  }, [])

  const handleAddSolution = useCallback(() => {
    setSolutionModal({ open: true, editData: null })
  }, [])

  const handleEditSolution = useCallback((sol) => {
    setSolutionModal({ open: true, editData: sol })
  }, [])

  const handleSolutionModalClose = useCallback(() => {
    setSolutionModal({ open: false })
  }, [])

  const handleSolutionSaved = useCallback(async () => {
    setSolutionModal({ open: false })
    onRefresh?.()
  }, [onRefresh])

  const handleDeleteSolution = useCallback(async () => {
    if (!deleteSolutionId) return
    try {
      await cardService.deleteSolution(deleteSolutionId)
      setDeleteSolutionId(null)
      setDeleteSolutionName('')
      onRefresh?.()
      showToast('解法已删除', 'success')
    } catch (err) {
      showToast(`删除失败: ${err.message}`, 'error')
    }
  }, [deleteSolutionId, onRefresh])

  return (
    <>
      <h1 className={styles.cardTitle}>{data.title}</h1>

      <div className={styles.cardMeta}>
        {data.difficulty && (
          <span className={`${styles.badge} ${DIFFICULTY_CLASSES[data.difficulty] || ''}`}>
            {DIFFICULTY_LABELS[data.difficulty] || data.difficulty}
          </span>
        )}
        {data.my_status && (
          <span className={styles.statusText}>{data.my_status}</span>
        )}
        {data.leetcode_link && (
          <a
            href={data.leetcode_link}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.externalLink}
          >
            🔗 LeetCode
          </a>
        )}
      </div>

      {data.notes && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>注意事项</h3>
          <MarkdownRenderer content={data.notes} className={styles.textContent} />
        </div>
      )}

      {data.video_demo_link && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>视频演示</h3>
          <a href={data.video_demo_link} target="_blank" rel="noopener noreferrer" className={styles.externalLink}>
            🔗 观看视频演示
          </a>
        </div>
      )}

      {data.related_problem_ids?.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>相关题目</h3>
          <div className={styles.techniquesRow}>
            {data.related_problem_ids.map((pid) => (
              <button
                key={pid}
                className={styles.techniqueLink}
                onClick={() => onNavigate('problem', pid)}
              >
                #{pid}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={styles.section}>
          <h3 className={styles.sectionTitle}>
            解法 ({data.solutions?.length || 0})
            <button className={styles.addSolutionBtn} onClick={handleAddSolution}>
              + 添加解法
            </button>
            {compareSelection.length === 2 && (
              <button className={styles.compareBtn} onClick={() => setCompareSelection([])}>
                取消对比
              </button>
            )}
          </h3>
          {data.solutions?.length > 0 ? (
          <div className={styles.solutionsList}>
            {data.solutions.map((sol) => (
              <div key={sol.id} className={styles.solutionCard}>
                <div
                  className={styles.solutionHeader}
                  onClick={() => toggleSolution(sol.id)}
                >
                  <div className={styles.solutionHeaderLeft}>
                    <span className={styles.solutionLinkName}>{sol.name}</span>
                    {sol.time_complexity && (
                      <span className={styles.solutionLinkComplexity}>{sol.time_complexity}</span>
                    )}
                    {sol.space_complexity && (
                      <span className={styles.solutionLinkComplexity} style={{ background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary-light)' }}>
                        {sol.space_complexity}
                      </span>
                    )}
                  </div>
                  <div className={styles.solutionActions}>
                    <button
                      className={styles.solutionActionBtn}
                      onClick={(e) => { e.stopPropagation(); handleEditSolution(sol); }}
                      title="编辑解法"
                    >
                      ✏️
                    </button>
                    <button
                      className={styles.solutionActionBtn}
                      onClick={(e) => { e.stopPropagation(); setDeleteSolutionId(sol.id); setDeleteSolutionName(sol.name); }}
                      title="删除解法"
                    >
                      🗑️
                    </button>
                    <button
                      className={`${styles.compareSelectBtn} ${compareSelection.includes(sol.id) ? styles.compareSelectBtnActive : ''}`}
                      onClick={(e) => { e.stopPropagation(); toggleCompareSelection(sol.id); }}
                    >
                      {compareSelection.includes(sol.id) ? '✓ 已选' : '对比'}
                    </button>
                  </div>
                  <span className={styles.collapseIcon}>
                    {collapsedSolutions.has(sol.id) ? '▶' : '▼'}
                  </span>
                </div>

                {!collapsedSolutions.has(sol.id) && (
                  <div className={styles.solutionBody}>
                    {sol.breakthrough && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>突破口</span>
                        <MarkdownRenderer content={sol.breakthrough} className={styles.textContent} />
                      </div>
                    )}
                    {sol.approach && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>思路</span>
                        <MarkdownRenderer content={sol.approach} className={styles.textContent} />
                      </div>
                    )}
                    {sol.code && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>代码</span>
                        <CodeBlock code={sol.code} />
                      </div>
                    )}
                    {sol.pitfalls?.length > 0 && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>易错点</span>
                        <ul className={styles.pitfallList}>
                          {sol.pitfalls.map((pitfall, i) => (
                            <li key={i} className={styles.pitfallItem}>{pitfall}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {sol.techniques?.length > 0 && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>关联技巧</span>
                        <div className={styles.techniquesRow}>
                          {sol.techniques.map((tech) => (
                            <button
                              key={tech.id}
                              className={styles.techniqueLink}
                              onClick={(e) => { e.stopPropagation(); onNavigate('technique', tech.id); }}
                            >
                              {tech.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {!sol.breakthrough && !sol.approach && !sol.code && (!sol.pitfalls || sol.pitfalls.length === 0) && (!sol.techniques || sol.techniques.length === 0) && (
                      <div className={styles.solutionField}>
                        <span className={styles.solutionFieldLabel}>暂无详情</span>
                        <div className={styles.textContent} style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>可编辑解法卡片添加突破口、思路、代码等内容</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {compareSelection.length === 2 && (
        <div className={styles.comparePanel}>
          <h3 className={styles.sectionTitle}>解法对比</h3>
          <div className={styles.compareColumns}>
            {compareSelection.map((solId) => {
              const sol = data.solutions.find(s => s.id === solId)
              if (!sol) return null
              return (
                <div key={sol.id} className={styles.compareColumn}>
                  <div className={styles.compareColumnHeader}>{sol.name}</div>
                  {sol.time_complexity && <div className={styles.compareField}><span className={styles.solutionFieldLabel}>时间:</span> {sol.time_complexity}</div>}
                  {sol.space_complexity && <div className={styles.compareField}><span className={styles.solutionFieldLabel}>空间:</span> {sol.space_complexity}</div>}
                  {sol.breakthrough && <div className={styles.compareField}><span className={styles.solutionFieldLabel}>突破口:</span> <MarkdownRenderer content={sol.breakthrough} className={styles.textContent} /></div>}
                  {sol.approach && <div className={styles.compareField}><span className={styles.solutionFieldLabel}>思路:</span> <MarkdownRenderer content={sol.approach} className={styles.textContent} /></div>}
                  {sol.code && <div className={styles.compareField}><span className={styles.solutionFieldLabel}>代码:</span> <CodeBlock code={sol.code} /></div>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 解法编辑/创建模态框 */}
      <CreateCardModal
        open={solutionModal.open}
        onClose={handleSolutionModalClose}
        onCreated={handleSolutionSaved}
        forceType="solution"
        editType={solutionModal.editData ? 'solution' : null}
        editData={solutionModal.editData}
        problemId={data.id}
      />

      {/* 删除解法确认 */}
      {deleteSolutionId && (
        <div className={styles.solutionDeleteOverlay}>
          <div className={styles.solutionDeleteDialog}>
            <h3>确认删除</h3>
            <p>确定要删除解法「{deleteSolutionName}」吗？此操作不可撤销。</p>
            <div className={styles.solutionDeleteDialogButtons}>
              <button className={styles.solutionDeleteCancelBtn} onClick={() => { setDeleteSolutionId(null); setDeleteSolutionName(''); }}>
                取消
              </button>
              <button className={styles.solutionDeleteConfirmBtn} onClick={handleDeleteSolution}>
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function SolutionCard({ data, onNavigate }) {
  return (
    <>
      <h1 className={styles.cardTitle}>{data.name}</h1>

      <div className={styles.cardMeta}>
        {data.problem_title && (
          <button
            className={styles.linkItem}
            style={{ width: 'auto', padding: '4px 12px', fontSize: '0.82rem' }}
            onClick={() => onNavigate('problem', data.problem_id)}
          >
            ← {data.problem_title}
          </button>
        )}
      </div>

      {(data.time_complexity || data.space_complexity) && (
        <div className={styles.cardMeta}>
          {data.time_complexity && (
            <span className={styles.badge} style={{ background: 'rgba(16,185,129,0.1)', color: 'var(--color-success)', border: '1px solid rgba(16,185,129,0.25)' }}>
              时间: {data.time_complexity}
            </span>
          )}
          {data.space_complexity && (
            <span className={styles.badge} style={{ background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary-light)', border: '1px solid rgba(99,102,241,0.25)' }}>
              空间: {data.space_complexity}
            </span>
          )}
        </div>
      )}

      {data.breakthrough && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>突破口</h3>
          <MarkdownRenderer content={data.breakthrough} className={styles.textContent} />
        </div>
      )}

      {data.approach && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>思路</h3>
          <MarkdownRenderer content={data.approach} className={styles.textContent} />
        </div>
      )}

      {data.code && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>代码</h3>
          <CodeBlock code={data.code} />
        </div>
      )}

      {data.pitfalls?.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>易错点</h3>
          <ul className={styles.pitfallList}>
            {data.pitfalls.map((pitfall, i) => (
              <li key={i} className={styles.pitfallItem}>{pitfall}</li>
            ))}
          </ul>
        </div>
      )}

      {data.techniques?.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>关联技巧</h3>
          <div className={styles.techniquesRow}>
            {data.techniques.map((tech) => (
              <button
                key={tech.id}
                className={styles.techniqueLink}
                onClick={() => onNavigate('technique', tech.id)}
              >
                {tech.name}
                {tech.category && <span style={{ opacity: 0.7, fontSize: '0.75rem' }}>({tech.category})</span>}
              </button>
            ))}
          </div>
        </div>
      )}

      {data.related_solution_ids?.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>相关解法</h3>
          <div className={styles.techniquesRow}>
            {data.related_solution_ids.map((sid) => (
              <button
                key={sid}
                className={styles.techniqueLink}
                onClick={() => onNavigate('solution', sid)}
              >
                #{sid}
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function TechniqueCard({ data, onNavigate }) {
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewResult, setReviewResult] = useState(null)

  const handleSelfReview = useCallback(async (rating) => {
    setReviewLoading(true)
    setReviewResult(null)
    try {
      const result = await cardService.selfReviewTechnique(data.id, rating)
      setReviewResult(result)
      showToast('自评成功', 'success')
    } catch (err) {
      showToast(`自评失败: ${err.message}`, 'error')
    } finally {
      setReviewLoading(false)
    }
  }, [data.id])

  const renderStars = (proficiency) => {
    const stars = []
    for (let i = 0; i < 5; i++) {
      stars.push(
        <span key={i} className={i < proficiency ? styles.starFilled : styles.starEmpty}>
          ★
        </span>
      )
    }
    return stars
  }

  return (
    <>
      <h1 className={styles.cardTitle}>{data.name}</h1>

      <div className={styles.cardMeta}>
        {data.category && (
          <span className={styles.badge} style={{ background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary-light)', border: '1px solid rgba(99,102,241,0.25)' }}>
            {data.category}
          </span>
        )}
        {data.proficiency != null && (
          <span className={styles.starsRow}>{renderStars(data.proficiency)}</span>
        )}
        {data.next_review_date ? (
          <span className={`${styles.badge} ${REVIEW_STATUS_CLASSES[data.review_status] || ''}`}>
            下次复习: {new Date(data.next_review_date).toLocaleDateString()}
          </span>
        ) : (
          <span className={styles.badge} style={{ background: 'rgba(99,102,241,0.08)', color: 'var(--color-text-muted)', border: '1px solid var(--border-color)' }}>
            尚未复习
          </span>
        )}
      </div>

      {data.use_cases && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>使用场景</h3>
          <MarkdownRenderer content={data.use_cases} className={styles.textContent} />
        </div>
      )}

      {data.code_template && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>代码模板</h3>
          <CodeBlock code={data.code_template} />
        </div>
      )}

      {data.memory_anchors && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>记忆锚点</h3>
          <MarkdownRenderer content={data.memory_anchors} className={styles.textContent} />
        </div>
      )}

      {data.notes && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>注意事项</h3>
          <MarkdownRenderer content={data.notes} className={styles.textContent} />
        </div>
      )}

      {data.video_demo_link && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>视频演示</h3>
          <a href={data.video_demo_link} target="_blank" rel="noopener noreferrer" className={styles.externalLink}>
            🔗 观看视频演示
          </a>
        </div>
      )}

      {/* 关联题目 */}
      {(() => {
        const allProblems = (data.solutions || [])
          .filter(sol => sol.problem_id && sol.problem_title)
          .filter((sol, i, arr) => arr.findIndex(s => s.problem_id === sol.problem_id) === i)
        if (allProblems.length === 0) return null
        return (
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>关联题目</h3>
            <div className={styles.solutionsList}>
              {allProblems.map((sol) => (
                <button
                  key={sol.problem_id}
                  className={styles.solutionLink}
                  onClick={() => onNavigate('problem', sol.problem_id)}
                >
                  <span className={styles.solutionLinkName}>{sol.problem_title}</span>
                  {sol.leetcode_link && (
                    <a
                      href={sol.leetcode_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.externalLink}
                      onClick={(e) => e.stopPropagation()}
                      style={{ fontSize: '0.75rem' }}
                    >
                      🔗 LeetCode
                    </a>
                  )}
                </button>
              ))}
            </div>
          </div>
        )
      })()}

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>自评</h3>
        {!reviewResult ? (
          <div className={styles.selfRatingOptions}>
            <button
              className={styles.ratingBtn}
              onClick={() => handleSelfReview('forgot')}
              disabled={reviewLoading}
            >
              😵 完全忘了 (forgot)
            </button>
            <button
              className={styles.ratingBtn}
              onClick={() => handleSelfReview('struggled')}
              disabled={reviewLoading}
            >
              🤔 有思路但写不出 (struggled)
            </button>
            <button
              className={styles.ratingBtn}
              onClick={() => handleSelfReview('passed')}
              disabled={reviewLoading}
            >
              👍 写出来了但不是最优 (passed)
            </button>
            <button
              className={styles.ratingBtn}
              onClick={() => handleSelfReview('mastered')}
              disabled={reviewLoading}
            >
              🎉 最优解 (mastered)
            </button>
            {reviewLoading && <div className={styles.loadingState}>提交中...</div>}
          </div>
        ) : (
          <div className={styles.reviewResult}>
            <div>自评完成！</div>
            {reviewResult.new_durability != null && (
              <div>新耐久度: {reviewResult.new_durability}</div>
            )}
            {reviewResult.next_review && (
              <div>下次复习: {new Date(reviewResult.next_review).toLocaleDateString()}</div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

export default function CardPanel({ type, data, onNavigate, onRefresh }) {
  if (!data) {
    return (
      <div className={styles.cardPanel}>
        <div className={styles.loadingState}>暂无数据</div>
      </div>
    )
  }

  return (
    <div className={styles.cardPanel}>
      {type === 'problem' && <ProblemCard data={data} onNavigate={onNavigate} onRefresh={onRefresh} />}
      {type === 'solution' && <SolutionCard data={data} onNavigate={onNavigate} />}
      {type === 'technique' && <TechniqueCard data={data} onNavigate={onNavigate} />}
    </div>
  )
}