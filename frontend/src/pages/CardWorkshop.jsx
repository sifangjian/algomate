import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './CardWorkshop.module.css'

const ALGORITHM_CATEGORIES = [
    'Search', 'Sorting', 'Dynamic Programming', 'Graph',
    'Tree', 'Recursion', 'Array', 'String', 'Greedy', 'Math',
]

const REALM_DOMAINS = [
    '新手森林', '迷雾沼泽', '古树森林', '命运迷宫',
    '贪婪之塔', '智慧圣殿', '分裂山脉', '数学殿堂',
]

function CreateCardModal({ open, onClose, onCreated }) {
    const { addCard } = useCardStore()

    const [form, setForm] = useState({
        name: '',
        algorithm_category: '',
        difficulty: 3,
        noteContent: '',
    })
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)

    const [polishingField, setPolishingField] = useState(null)
    const [polishPreview, setPolishPreview] = useState(null)

    const resetForm = useCallback(() => {
        setForm({
            name: '',
            algorithm_category: '',
            difficulty: 3,
            noteContent: '',
        })
        setErrors({})
        setPolishingField(null)
        setPolishPreview(null)
        setIsSubmitting(false)
    }, [])

    const handleClose = useCallback(() => {
        resetForm()
        onClose()
    }, [onClose, resetForm])

    const handleFieldChange = useCallback((field, value) => {
        setForm((prev) => ({ ...prev, [field]: value }))
        setErrors((prev) => {
            if (prev[field]) {
                const next = { ...prev }
                delete next[field]
                return next
            }
            return prev
        })
    }, [])

    const handlePolish = useCallback(async (field) => {
        const content = form.noteContent

        if (!content.trim()) {
            showToast('请先输入内容再进行润色', 'warning')
            return
        }

        setPolishingField(field)
        setPolishPreview(null)

        try {
            const result = await cardService.polishCard({ content, type: field })
            setPolishPreview({ field, content: result.polished_content })
        } catch (err) {
            showToast(`AI润色失败: ${err.message}`, 'error')
            setPolishingField(null)
        }
    }, [form.noteContent])

    const handleAcceptPolish = useCallback(() => {
        if (!polishPreview) return

        setForm((prev) => ({ ...prev, noteContent: polishPreview.content }))

        setPolishPreview(null)
        setPolishingField(null)
    }, [polishPreview])

    const handleRejectPolish = useCallback(() => {
        setPolishPreview(null)
        setPolishingField(null)
    }, [])

    const validate = useCallback(() => {
        const newErrors = {}
        if (!form.name.trim()) newErrors.name = '卡牌名称不能为空'
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }, [form.name])

    const handleSubmit = useCallback(async () => {
        if (!validate()) return

        setIsSubmitting(true)
        try {
            const payload = {
                name: form.name.trim(),
                algorithm_category: form.algorithm_category.trim() || null,
                difficulty: form.difficulty,
                knowledge_content: form.noteContent.trim() || null,
            }

            const newCard = await cardService.createCard(payload)
            addCard(newCard)
            showToast(`卡牌「${newCard.name}」创建成功！`, 'success')
            onCreated?.(newCard)
            handleClose()
        } catch (err) {
            showToast(`创建失败: ${err.message}`, 'error')
        } finally {
            setIsSubmitting(false)
        }
    }, [form, validate, addCard, onCreated, handleClose])

    return (
        <Modal
            open={open}
            onClose={handleClose}
            title="✨ 创建新卡牌"
            size="lg"
        >
            <div className={styles.createForm}>
                <Input
                    label="卡牌名称"
                    placeholder="输入卡牌名称，如：二分查找"
                    value={form.name}
                    onChange={(e) => handleFieldChange('name', e.target.value)}
                    error={errors.name}
                    icon="🎴"
                    id="card-name"
                />

                <div className={styles.formField}>
                    <label className={styles.fieldLabel} htmlFor="card-category">
                        算法分类
                    </label>
                    <input
                        id="card-category"
                        className={styles.fieldInput}
                        placeholder="如：Dynamic Programming"
                        value={form.algorithm_category}
                        onChange={(e) => handleFieldChange('algorithm_category', e.target.value)}
                        list="category-list"
                    />
                    <datalist id="category-list">
                        {ALGORITHM_CATEGORIES.map((c) => (
                            <option key={c} value={c} />
                        ))}
                    </datalist>
                </div>

                <div className={styles.formField}>
                    <label className={styles.fieldLabel}>难度</label>
                    <div className={styles.starRating}>
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                type="button"
                                className={`${styles.starBtn} ${star <= form.difficulty ? styles.starActive : ''}`}
                                onClick={() => handleFieldChange('difficulty', star)}
                                aria-label={`${star}星`}
                            >
                                {star <= form.difficulty ? '★' : '☆'}
                            </button>
                        ))}
                        <span className={styles.starLabel}>{form.difficulty}/5</span>
                    </div>
                </div>

                <div className={styles.formField}>
                    <div className={styles.fieldHeader}>
                        <label className={styles.fieldLabel} htmlFor="card-note">心得内容</label>
                        <button
                            type="button"
                            className={styles.polishBtn}
                            onClick={() => handlePolish('note_content')}
                            disabled={!!polishingField || !form.noteContent.trim()}
                        >
                            {polishingField === 'note_content' ? '⏳ 润色中...' : '✨ AI润色'}
                        </button>
                    </div>
                    <textarea
                        id="card-note"
                        className={styles.fieldTextarea}
                        placeholder="输入心得内容（可选）..."
                        value={form.noteContent}
                        onChange={(e) => handleFieldChange('noteContent', e.target.value)}
                        rows={4}
                    />
                    {polishPreview && polishPreview.field === 'note_content' && (
                        <div className={styles.polishPreview}>
                            <div className={styles.polishPreviewHeader}>
                                <span>✨ AI润色结果</span>
                            </div>
                            <div className={styles.polishPreviewContent}>
                                {polishPreview.content}
                            </div>
                            <div className={styles.polishPreviewActions}>
                                <button
                                    type="button"
                                    className={styles.polishAcceptBtn}
                                    onClick={handleAcceptPolish}
                                >
                                    采纳
                                </button>
                                <button
                                    type="button"
                                    className={styles.polishRejectBtn}
                                    onClick={handleRejectPolish}
                                >
                                    放弃
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className={styles.createActions}>
                    <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
                        取消
                    </Button>
                    <Button
                        variant="accent"
                        onClick={handleSubmit}
                        loading={isSubmitting}
                        disabled={!!polishingField}
                    >
                        创建卡牌
                    </Button>
                </div>
            </div>
        </Modal>
    )
}

export default function CardWorkshop() {
    const navigate = useNavigate()
    const { cards, setCards, selectedCard, setSelectedCard, removeCard, addCard } = useCardStore()

    const [searchKeyword, setSearchKeyword] = useState('')
    const [sortBy, setSortBy] = useState('name')
    const [selectedRealm, setSelectedRealm] = useState('')
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [cardToDelete, setCardToDelete] = useState(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const [createModalOpen, setCreateModalOpen] = useState(false)

    const lastClickTimeRef = useRef(0)
    const DEBOUNCE_DELAY = 300

    useEffect(() => {
        cardService.getAll().then((data) => {
            if (Array.isArray(data) && data.length > 0) setCards(data)
        }).catch(() => { })
    }, [setCards])

    const filteredCards = useMemo(() => {
        let result = cards

        if (selectedRealm) {
            result = result.filter(
                (c) => c.domain === selectedRealm
            )
        }

        if (searchKeyword.trim()) {
            const kw = searchKeyword.toLowerCase()
            result = result.filter(
                (c) =>
                    c.name.toLowerCase().includes(kw) ||
                    c.algorithmCategory?.toLowerCase().includes(kw)
            )
        }

        result = [...result].sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name)
                case 'durability':
                    return a.durability - b.durability
                case 'reviewedDate':
                    return new Date(b.lastReviewed || 0) - new Date(a.lastReviewed || 0)
                default:
                    return 0
            }
        })

        return result
    }, [cards, searchKeyword, sortBy, selectedRealm])

    const dangerCount = useMemo(
        () => cards.filter((c) => c.durability < 30).length,
        [cards]
    )

    const handleSortChange = useCallback((e) => {
        const now = Date.now()
        if (now - lastClickTimeRef.current < DEBOUNCE_DELAY) {
            return
        }
        lastClickTimeRef.current = now
        setSortBy(e.target.value)
    }, [])

    const handleSearchChange = useCallback((e) => {
        setSearchKeyword(e.target.value)
    }, [])

    const handleCardClick = useCallback(
        (card) => setSelectedCard(card),
        [setSelectedCard]
    )

    const handleDeleteRequest = useCallback((card) => {
        setCardToDelete(card)
        setDeleteConfirmOpen(true)
    }, [])

    const handleDeleteConfirm = useCallback(async () => {
        if (!cardToDelete) return
        setIsDeleting(true)
        try {
            await cardService.deleteCard(cardToDelete.id)
            removeCard(cardToDelete.id)
            showToast(`卡牌「${cardToDelete.name}」已删除`, 'success')
        } catch (err) {
            showToast(`删除失败: ${err.message}`, 'error')
        } finally {
            setIsDeleting(false)
            setDeleteConfirmOpen(false)
            setCardToDelete(null)
            setSelectedCard(null)
        }
    }, [cardToDelete, removeCard, setSelectedCard])

    const handleReview = useCallback(
        (card) => {
            if (card.is_sealed || card.durability === 0) {
                showToast('该卡牌已封印，无法修炼', 'warning')
                return
            }
            navigate(`/boss/battle?cardId=${card.id}`)
        },
        [navigate]
    )

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>🎴 卡牌工坊</h1>
                    <p className={styles.pageSubtitle}>管理你的算法知识卡牌</p>
                </div>
                <Button
                    variant="accent"
                    size="sm"
                    icon="➕"
                    onClick={() => setCreateModalOpen(true)}
                >
                    创建新卡牌
                </Button>
            </div>

            {dangerCount > 0 && (
                <div className={styles.warningBanner} role="alert">
                    <span>⚠️</span>
                    <span>
                        有 <strong>{dangerCount}</strong> 张卡牌濒危（耐久度 &lt; 30%），请及时修炼！
                    </span>
                </div>
            )}

            <div className={styles.toolbar}>
                <Input
                    placeholder="搜索卡牌..."
                    value={searchKeyword}
                    onChange={handleSearchChange}
                    icon="🔍"
                    className={styles.searchInput}
                />
                <div className={styles.realmTabs}>
                    <button
                        className={`${styles.realmTab} ${!selectedRealm ? styles.activeTab : ''}`}
                        onClick={() => setSelectedRealm('')}
                    >
                        全部
                    </button>
                    {REALM_DOMAINS.map((realm) => (
                        <button
                            key={realm}
                            className={`${styles.realmTab} ${selectedRealm === realm ? styles.activeTab : ''}`}
                            onClick={() => setSelectedRealm(realm)}
                        >
                            {realm}
                        </button>
                    ))}
                </div>
                <select
                    className={styles.sortSelect}
                    value={sortBy}
                    onChange={handleSortChange}
                    aria-label="排序方式"
                >
                    <option value="name">按名称</option>
                    <option value="durability">按耐久度</option>
                    <option value="reviewedDate">按修炼时间</option>
                </select>
            </div>

            <div className={styles.cardGrid}>
                {filteredCards.length === 0 ? (
                    <div className={styles.emptyState}>
                        <span className={styles.emptyIcon}>🎴</span>
                        <p>没有找到匹配的卡牌</p>
                    </div>
                ) : (
                    filteredCards.map((card) => (
                        <GameCard
                            key={card.id}
                            className={styles.cardItem}
                            hoverable
                            onClick={() => handleCardClick(card)}
                            glow={card.status === 'danger'}
                        >
                            <div className={styles.cardHeader}>
                                <span className={styles.cardIcon}>{getAlgorithmIcon(card.algorithmCategory)}</span>
                                <div className={styles.cardTitleArea}>
                                    <h3 className={styles.cardName}>{card.name}</h3>
                                    <span className={styles.cardCategory}>{card.algorithmCategory}</span>
                                </div>
                                <span className={`${styles.statusDot} ${styles[card.status]}`} title={
                                    card.status === 'normal' ? '正常' :
                                        card.status === 'warning' ? '注意' : '濒危'
                                } />
                            </div>

                            <div className={styles.durabilitySection}>
                                <div className={styles.durBar}>
                                    <div
                                        className={styles.durFill}
                                        style={{
                                            width: `${(card.durability / card.maxDurability) * 100}%`,
                                            background:
                                                card.durability >= 60
                                                    ? 'var(--color-success)'
                                                    : card.durability >= 30
                                                        ? 'var(--color-warning)'
                                                        : 'var(--color-danger)',
                                            ...(card.status === 'danger' && { animation: 'pulse-glow 2s infinite' }),
                                        }}
                                    />
                                </div>
                                <span className={styles.durText}>
                                    耐久 {card.durability}/{card.maxDurability}
                                </span>
                            </div>

                            <div className={styles.cardMeta}>
                                <span>修炼 {card.reviewCount}次</span>
                                <span>心得 {card.noteCount}</span>
                            </div>
                        </GameCard>
                    ))
                )}
            </div>

            <Modal
                open={!!selectedCard}
                onClose={() => setSelectedCard(null)}
                title={selectedCard?.name || ''}
                size="lg"
            >
                {selectedCard && (
                    <div className={styles.modalContent}>
                        <div className={styles.heroSection}>
                            <span className={`${styles.heroIcon} ${styles[selectedCard.status]}`}>
                                {getAlgorithmIcon(selectedCard.algorithmCategory)}
                            </span>
                            <h2 className={styles.heroName}>{selectedCard.name}</h2>
                            <div className={styles.heroBadges}>
                                {selectedCard.algorithmCategory && (
                                    <span className={styles.heroCategoryBadge}>{selectedCard.algorithmCategory}</span>
                                )}
                                <span className={`${styles.heroStatus} ${styles[selectedCard.status]}`}>
                                    {selectedCard.status === 'normal' ? '正常' : selectedCard.status === 'warning' ? '注意' : '濒危'}
                                </span>
                            </div>
                            <div className={styles.heroDivider} />
                        </div>

                        <div className={styles.statsGrid}>
                            <div className={styles.statCell}>
                                <span className={styles.statIcon}>🛡️</span>
                                <span className={styles.statValue}>
                                    {Math.round((selectedCard.durability / selectedCard.maxDurability) * 100)}%
                                </span>
                                <span className={styles.statDesc}>
                                    {selectedCard.durability >= 60 ? '状态良好' : selectedCard.durability >= 30 ? '需要关注' : '濒危警告'}
                                </span>
                                <div className={styles.durProgressBar}>
                                    <div
                                        className={styles.durProgressFill}
                                        style={{
                                            width: `${(selectedCard.durability / selectedCard.maxDurability) * 100}%`,
                                            background: selectedCard.durability >= 60
                                                ? 'linear-gradient(90deg, #10b981, #34d399)'
                                                : selectedCard.durability >= 30
                                                    ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                                                    : 'linear-gradient(90deg, #ef4444, #f87171)',
                                        }}
                                    />
                                </div>
                            </div>

                            <div className={styles.statCell}>
                                <span className={styles.statIcon}>⭐</span>
                                <span className={styles.statValue}>{'★'.repeat(selectedCard.difficulty)}{'☆'.repeat(5 - selectedCard.difficulty)}</span>
                                <span className={styles.statDesc}>
                                    {['', '入门难度', '简单难度', '中等难度', '困难难度', '地狱难度'][selectedCard.difficulty] || ''}
                                </span>
                            </div>

                            {selectedCard.reviewLevel != null && (
                                <div className={styles.statCell}>
                                    <span className={styles.statIcon}>⚔️</span>
                                    <span className={styles.statValue}>Lv.{selectedCard.reviewLevel}</span>
                                    <span className={styles.statDesc}>
                                        {selectedCard.reviewLevel <= 1 ? '初窥门径'
                                            : selectedCard.reviewLevel <= 3 ? '初学乍练'
                                            : selectedCard.reviewLevel <= 5 ? '小有所成'
                                            : selectedCard.reviewLevel <= 7 ? '融会贯通'
                                            : '登峰造极'}
                                    </span>
                                </div>
                            )}

                            <div className={styles.statCell}>
                                <span className={styles.statIcon}>📖</span>
                                <span className={styles.statValue}>{selectedCard.reviewCount ?? 0}</span>
                                <span className={styles.statDesc}>次修炼</span>
                            </div>
                        </div>

                        <div className={styles.infoRow}>
                            <span className={styles.infoItem}>📅 {new Date(selectedCard.createdAt).toLocaleDateString()}</span>
                            <span className={styles.infoDot}>·</span>
                            <span className={styles.infoItem}>
                                🕐 {selectedCard.lastReviewed ? new Date(selectedCard.lastReviewed).toLocaleDateString() : '从未修炼'}
                            </span>
                            {selectedCard.nextReviewDate && (
                                <>
                                    <span className={styles.infoDot}>·</span>
                                    <span className={styles.infoItem}>⏳ {new Date(selectedCard.nextReviewDate).toLocaleDateString()}</span>
                                </>
                            )}
                            {selectedCard.algorithmType && (
                                <>
                                    <span className={styles.infoDot}>·</span>
                                    <span className={styles.infoItem}>
                                        <span className={styles.runeTagInline}>{selectedCard.algorithmType}</span>
                                    </span>
                                </>
                            )}
                        </div>

                        {selectedCard.keyPoints?.length > 0 && (
                            <div className={styles.runeTagSection}>
                                <span className={styles.runeTagTitle}>🔑 关键要点</span>
                                <div className={styles.runeTagList}>
                                    {selectedCard.keyPoints.map((kp, i) => (
                                        <span key={i} className={styles.runeTagItem}>{kp}</span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {selectedCard.knowledgeContent && (
                            <div className={styles.scrollSection}>
                                <div className={styles.scrollTitle}>📖 知识内容</div>
                                <div className={styles.scrollContent}>
                                    {selectedCard.knowledgeContent}
                                </div>
                            </div>
                        )}

                        {selectedCard.summary && (
                            <div className={styles.quoteCard}>
                                <span className={styles.quoteMark}>"</span>
                                <p className={styles.quoteText}>{selectedCard.summary}</p>
                                <span className={styles.quoteAttribution}>—— 算法心得</span>
                            </div>
                        )}

                        <div className={styles.modalActions}>
                            <Button variant="primary" onClick={() => handleReview(selectedCard)} className={styles.reviewBtn}>
                                📖 修炼此卡牌
                            </Button>
                            <Button
                                variant="ghost"
                                onClick={() => handleDeleteRequest(selectedCard)}
                                className={styles.deleteBtn}
                            >
                                🗑️ 删除卡牌
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>

            <ConfirmDialog
                open={deleteConfirmOpen}
                onClose={() => setDeleteConfirmOpen(false)}
                onConfirm={handleDeleteConfirm}
                title="确认删除"
                message={`确定要删除「${cardToDelete?.name}」卡牌吗？\n删除后关联的心得将保留，但无法再通过卡牌访问。`}
                confirmText="确认删除"
                cancelText="取消"
                variant="danger"
                loading={isDeleting}
            />

            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={() => setCreateModalOpen(false)}
            />
        </div>
    )
}

function getAlgorithmIcon(category) {
    const map = {
        Search: '🔍',
        Sorting: '📊',
        'Dynamic Programming': '🎯',
        Graph: '🕸️',
        Tree: '🌲',
        Recursion: '🔄',
        Array: '📋',
        String: '📝',
        Greedy: '💰',
        Math: '🔢',
    }
    return map[category] || '📜'
}
