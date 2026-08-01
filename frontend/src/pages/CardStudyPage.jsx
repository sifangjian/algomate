import { useState, useEffect, useCallback, memo } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import MarkdownRenderer from '../components/ui/MarkdownRenderer'
import CodeBlock from '../components/ui/CodeBlock'

import CardEditForm from '../components/card/CardEditForm'
import { showToast } from '../components/ui/Toast/index'
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

// 卡牌名称缓存，用于 [[双链]] 链接跳转
let cardNameCache = null
let cardNameCachePromise = null

function getCardByName(name) {
    if (cardNameCache) {
        return Promise.resolve(cardNameCache[name])
    }
    if (cardNameCachePromise) return cardNameCachePromise.then(() => cardNameCache[name])

    cardNameCachePromise = cardService.getAll({ keyword: '', limit: 200 }).then(result => {
        const cache = {}
        const cards = result.cards || []
        cards.forEach(c => { cache[c.name] = c.id })
        cardNameCache = cache
        return cache[name]
    }).catch(() => {
        cardNameCache = {}
        return null
    })
    return cardNameCachePromise
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

// 可点击的卡牌链接组件
function CardLink({ text }) {
    const navigate = useNavigate()
    const [cardId, setCardId] = useState(null)
    const [loading, setLoading] = useState(true)

    // 解析 [[名称]] 格式
    const match = text.match(/^\[\[(.+?)\]\]/)
    const cardName = match ? match[1] : text
    // 只有当文本包含 — 分隔符时才提取 note
    const hasNoteSeparator = text.match(/^\[\[.+?\]\]\s*[—\-–]\s*/)
    const note = hasNoteSeparator ? text.replace(/^\[\[.+?\]\]\s*[—\-–]\s*/, '').trim() : ''

    useEffect(() => {
        getCardByName(cardName).then(id => {
            setCardId(id)
            setLoading(false)
        })
    }, [cardName])

    const handleClick = (e) => {
        e.preventDefault()
        if (cardId) {
            navigate(`/study/${cardId}`)
        }
    }

    return (
        <span>
            {loading ? (
                <span style={{ color: '#888' }}>{cardName}</span>
            ) : cardId ? (
                <a
                    href={`/study/${cardId}`}
                    onClick={handleClick}
                    style={{
                        color: '#60a5fa', cursor: 'pointer', textDecoration: 'none',
                        fontWeight: 500, borderBottom: '1px dashed rgba(96,165,250,0.3)'
                    }}
                    onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                    onMouseLeave={e => e.target.style.textDecoration = 'none'}
                >
                    {cardName}
                </a>
            ) : (
                <span style={{ color: '#888' }}>{cardName}</span>
            )}
            {note && <span style={{ color: '#999', marginLeft: 4 }}>— {note}</span>}
        </span>
    )
}

export default function CardStudyPage() {
    const { cardId } = useParams()
    const navigate = useNavigate()
    const location = useLocation()
    const { selectedCard, fetchCardById, clearSelectedCard, setSelectedCard: setHallSelectedCard } = useHallStore()
    const { deleteCard, updateCard } = useCardStore()
    const [loading, setLoading] = useState(true)
    const [isEditing, setIsEditing] = useState(false)
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    useEffect(() => {
        if (cardId) {
            setLoading(true)
            fetchCardById(cardId).finally(() => {
                setLoading(false)
                // 检查是否从创建卡牌跳转过来，自动进入编辑模式
                if (location.state?.autoEdit) {
                    setIsEditing(true)
                }
            })
        }
        return () => clearSelectedCard()
    }, [cardId, fetchCardById, clearSelectedCard, location.state?.autoEdit])

    const handleBack = () => navigate('/')

    const handleEdit = useCallback(() => {
        setIsEditing(true)
    }, [])

    const handleEditCancel = useCallback(() => {
        setIsEditing(false)
    }, [])

    const handleDeleteRequest = useCallback(() => {
        setDeleteConfirmOpen(true)
    }, [])

    const handleDeleteCancel = useCallback(() => {
        setDeleteConfirmOpen(false)
    }, [])

    const handleDeleteConfirm = useCallback(async () => {
        if (!selectedCard) return
        setIsDeleting(true)
        try {
            await deleteCard(selectedCard.id)
            showToast(`卡牌「${selectedCard.name}」已删除`, 'success')
            navigate('/')
        } catch (err) {
            showToast(`删除失败: ${err.message}`, 'error')
        } finally {
            setIsDeleting(false)
            setDeleteConfirmOpen(false)
        }
    }, [selectedCard, deleteCard, navigate])

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
    const newContent = parseJSON(card.content) || {}
    const isNewCard = card.card_type === 'tip' || card.card_type === 'problem'

    return (
        <div className={styles.page}>
            <div className={styles.header}>
                <button className={styles.backBtn} onClick={handleBack}>← 返回</button>
                <h1 className={styles.title}>{card.name}</h1>
                {!isEditing && (
                    <div className={styles.headerActions}>
                        <button className={styles.editBtn} onClick={handleEdit}>✏️ 编辑</button>
                        <button className={styles.deleteBtn} onClick={handleDeleteRequest}>🗑️ 删除</button>
                    </div>
                )}
            </div>

            {isEditing ? (
                <div className={styles.content}>
                    <CardEditForm card={card} onSave={(updatedCard) => {
                        if (updatedCard) {
                            setHallSelectedCard(updatedCard)
                        }
                        setIsEditing(false)
                    }} onCancel={handleEditCancel} />
                </div>
            ) : (
                <>
                    <div className={styles.content}>
                        {/* 新版技巧卡 */}
                        {isNewCard && card.card_type === 'tip' && !isEmpty(newContent) && (
                            <section className={styles.dimension} style={{ borderLeftColor: '#6366f1' }}>
                                <div className={styles.dimensionBody}>
                                    {newContent.one_line_definition && (
                                        <FieldRow label="一句话定义">
                                            <div className={styles.highlightBlock}>{newContent.one_line_definition}</div>
                                        </FieldRow>
                                    )}
                                    {newContent.trigger_condition && (
                                        <FieldRow label="触发条件">
                                            <div className={styles.triggerCondition}>
                                                <strong>{newContent.trigger_condition}</strong>
                                            </div>
                                        </FieldRow>
                                    )}
                                    {newContent.core_ideas?.length > 0 && (
                                        <FieldRow label="核心思路">
                                            <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                                {newContent.core_ideas.map((idea, i) => (
                                                    <li key={i}>{idea}</li>
                                                ))}
                                            </ul>
                                        </FieldRow>
                                    )}
                                    {newContent.complexity && (
                                        <FieldRow label="复杂度">
                                            <span className={styles.complexityTag}>{newContent.complexity}</span>
                                        </FieldRow>
                                    )}
                                    {newContent.related_problems?.length > 0 && (
                                        <FieldRow label="关联题目">
                                            <ul style={{ margin: 0, paddingLeft: '20px', listStyle: 'none' }}>
                                                {newContent.related_problems.map((p, i) => (
                                                    <li key={i} style={{ marginBottom: 4 }}>
                                                        <CardLink text={p} />
                                                    </li>
                                                ))}
                                            </ul>
                                        </FieldRow>
                                    )}
                                    {(newContent.related_tips?.length > 0 || newContent.similar_tips?.length > 0) && (
                                        <FieldRow label="关联技巧">
                                            <ul style={{ margin: 0, paddingLeft: '20px', listStyle: 'none' }}>
                                                {(newContent.related_tips || newContent.similar_tips || []).map((t, i) => (
                                                    <li key={i} style={{ marginBottom: 4 }}>
                                                        <CardLink text={t} />
                                                    </li>
                                                ))}
                                            </ul>
                                        </FieldRow>
                                    )}
                                    {newContent.pitfall_guide?.length > 0 && (
                                        <FieldRow label="避坑指南">
                                            <div className={styles.warningBlock}>
                                                {newContent.pitfall_guide.map((p, i) => (
                                                    <div key={i}>{p}</div>
                                                ))}
                                            </div>
                                        </FieldRow>
                                    )}
                                </div>
                            </section>
                        )}

                        {/* 新版题目卡 */}
                        {isNewCard && card.card_type === 'problem' && !isEmpty(newContent) && (
                            <section className={styles.dimension} style={{ borderLeftColor: '#10b981' }}>
                                <div className={styles.dimensionBody}>
                                    {newContent.one_line_problem && (
                                        <FieldRow label="一句话题干">
                                            <div className={styles.highlightBlock}>{newContent.one_line_problem}</div>
                                        </FieldRow>
                                    )}
                                    {newContent.core_skills?.length > 0 && (
                                        <FieldRow label="核心考点">
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                                {newContent.core_skills.map((s, i) => (
                                                    <CardLink key={i} text={s} />
                                                ))}
                                            </div>
                                        </FieldRow>
                                    )}
                                    {newContent.solution_approach?.length > 0 && (
                                        <FieldRow label="解法思路">
                                            <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                                {newContent.solution_approach.map((s, i) => (
                                                    <li key={i}>{s}</li>
                                                ))}
                                            </ul>
                                        </FieldRow>
                                    )}
                                    {newContent.core_code_snippet && (
                                        <FieldRow label="核心代码片段">
                                            <CodeBlock code={newContent.core_code_snippet} />
                                        </FieldRow>
                                    )}
                                    {newContent.complexity && (
                                        <FieldRow label="复杂度">
                                            <span className={styles.complexityTag}>{newContent.complexity}</span>
                                        </FieldRow>
                                    )}

                                </div>
                            </section>
                        )}
                    </div>
                </>
            )}
            {deleteConfirmOpen && (
                <div className={styles.confirmOverlay}>
                    <div className={styles.confirmDialog}>
                        <h3>确认删除</h3>
                        <p>确定要删除「{card.name}」卡牌吗？此操作不可撤销。</p>
                        <div className={styles.confirmActions}>
                            <button className={styles.cancelBtn} onClick={handleDeleteCancel}>取消</button>
                            <button className={styles.dangerBtn} onClick={handleDeleteConfirm} disabled={isDeleting}>
                                {isDeleting ? '删除中...' : '确认删除'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
