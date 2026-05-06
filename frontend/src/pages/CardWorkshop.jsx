import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import DurabilityChange from '../components/ui/DurabilityChange/DurabilityChange'
import EndangeredBanner from '../components/card/EndangeredBanner'
import PendingRetakeSection from '../components/card/PendingRetakeSection'
import DimensionSection from '../components/card/DimensionSection'
import VisualLinksSection from '../components/card/VisualLinksSection'
import CardEditForm from '../components/card/CardEditForm'
import RetakeButton from '../components/card/RetakeButton'
import styles from './CardWorkshop.module.css'

const ALGORITHM_CATEGORIES = [
    'Search', 'Sorting', 'Dynamic Programming', 'Graph',
    'Tree', 'Recursion', 'Array', 'String', 'Greedy', 'Math',
]

const STATUS_OPTIONS = [
    { value: '', label: '全部状态' },
    { value: 'normal', label: '正常' },
    { value: 'endangered', label: '濒危' },
    { value: 'pending_retake', label: '待重修' },
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
    const {
        cards, selectedCard, setSelectedCard, removeCard, addCard, updateCard,
        endangeredCount, pendingRetakeCount, loading, filters,
        setFilters, fetchCards, fetchCardDetail,
    } = useCardStore()

    const [searchKeyword, setSearchKeyword] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [sortBy, setSortBy] = useState('name')
    const [selectedRealm, setSelectedRealm] = useState('')
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [cardToDelete, setCardToDelete] = useState(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const [createModalOpen, setCreateModalOpen] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [sealedSectionOpen, setSealedSectionOpen] = useState(true)
    const [unsealConfirmOpen, setUnsealConfirmOpen] = useState(false)
    const [cardToUnseal, setCardToUnseal] = useState(null)
    const [isUnsealing, setIsUnsealing] = useState(false)
    const [editPolishingField, setEditPolishingField] = useState(null)
    const [editPolishPreview, setEditPolishPreview] = useState(null)
    const [durabilityAnimations, setDurabilityAnimations] = useState({})
    const [detailLoading, setDetailLoading] = useState(false)

    const lastClickTimeRef = useRef(0)
    const searchTimerRef = useRef(null)
    const DEBOUNCE_DELAY = 300

    useEffect(() => {
        if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
        searchTimerRef.current = setTimeout(() => {
            setDebouncedSearch(searchKeyword)
        }, DEBOUNCE_DELAY)
        return () => {
            if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
        }
    }, [searchKeyword])

    useEffect(() => {
        setFilters({ keyword: debouncedSearch.trim() })
    }, [debouncedSearch, setFilters])

    useEffect(() => {
        fetchCards()
    }, [filters.algorithm_type, filters.status, filters.keyword, fetchCards])

    useEffect(() => {
        if (!selectedCard) {
            setIsEditing(false)
        }
    }, [selectedCard])

    const endangeredCards = useMemo(
        () => cards.filter((c) => c.status === 'endangered'),
        [cards]
    )

    const pendingRetakeCards = useMemo(
        () => cards.filter((c) => c.status === 'pending_retake'),
        [cards]
    )

    const sealedCards = useMemo(
        () => cards.filter((c) => c.is_sealed),
        [cards]
    )

    const normalCards = useMemo(
        () => cards.filter((c) => !c.is_sealed && c.status !== 'pending_retake'),
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

    const handleStatusFilterChange = useCallback((e) => {
        setFilters({ status: e.target.value })
    }, [setFilters])

    const handleAlgorithmTypeFilterChange = useCallback((e) => {
        setFilters({ algorithm_type: e.target.value })
    }, [setFilters])

    const handleCardClick = useCallback(
        async (card) => {
            setSelectedCard(card)
            setDetailLoading(true)
            try {
                await fetchCardDetail(card.id)
            } catch {
            } finally {
                setDetailLoading(false)
            }
        },
        [setSelectedCard, fetchCardDetail]
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

    const handleEdit = useCallback(() => {
        setIsEditing(true)
    }, [])

    const handleCancelEdit = useCallback(() => {
        setIsEditing(false)
    }, [])

    const handleEditSave = useCallback(() => {
        setIsEditing(false)
    }, [])

    const handleUnsealRequest = useCallback((card) => {
        setCardToUnseal(card)
        setUnsealConfirmOpen(true)
    }, [])

    const handleUnsealConfirm = useCallback(async () => {
        if (!cardToUnseal) return
        setIsUnsealing(true)
        try {
            const updated = await cardService.unsealCard(cardToUnseal.id)
            updateCard(cardToUnseal.id, updated)
            setDurabilityAnimations(prev => ({ ...prev, [cardToUnseal.id]: { value: 30, key: Date.now() } }))
            showToast(`卡牌「${updated.name}」已解封，耐久度恢复至30`, 'success')
        } catch (err) {
            showToast(`解封失败: ${err.message}`, 'error')
        } finally {
            setIsUnsealing(false)
            setUnsealConfirmOpen(false)
            setCardToUnseal(null)
        }
    }, [cardToUnseal, updateCard])

    const getStatusLabel = useCallback((status) => {
        switch (status) {
            case 'endangered': return '濒危'
            case 'pending_retake': return '待重修'
            default: return '正常'
        }
    }, [])

    const getStatusClass = useCallback((status) => {
        switch (status) {
            case 'endangered': return styles.statusEndangered
            case 'pending_retake': return styles.statusPendingRetake
            default: return styles.statusNormal
        }
    }, [])

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

            <EndangeredBanner
                count={endangeredCount}
                endangeredCards={endangeredCards}
                onCardClick={handleReview}
            />

            <div className={styles.toolbar}>
                <Input
                    placeholder="搜索卡牌..."
                    value={searchKeyword}
                    onChange={handleSearchChange}
                    icon="🔍"
                    className={styles.searchInput}
                />
                <select
                    className={styles.filterSelect}
                    value={filters.algorithm_type}
                    onChange={handleAlgorithmTypeFilterChange}
                    aria-label="算法类型筛选"
                >
                    <option value="">全部类型</option>
                    {ALGORITHM_CATEGORIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                    ))}
                </select>
                <select
                    className={styles.filterSelect}
                    value={filters.status}
                    onChange={handleStatusFilterChange}
                    aria-label="状态筛选"
                >
                    {STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
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
                {loading ? (
                    <div className={styles.emptyState}>
                        <span className={styles.emptyIcon}>⏳</span>
                        <p>加载中...</p>
                    </div>
                ) : normalCards.length === 0 && sealedCards.length === 0 && pendingRetakeCards.length === 0 ? (
                    !debouncedSearch && !filters.status && !filters.algorithm_type ? (
                        <div className={styles.emptyGuide}>
                            <span className={styles.emptyGuideIcon}>🏔️</span>
                            <p className={styles.emptyGuideTitle}>还没有卡牌</p>
                            <p className={styles.emptyGuideDesc}>前往秘境修习，获取你的第一张卡牌</p>
                            <button className={styles.emptyGuideBtn} onClick={() => navigate('/')}>
                                前往秘境 →
                            </button>
                        </div>
                    ) : (
                        <div className={styles.emptyState}>
                            <span className={styles.emptyIcon}>🎴</span>
                            <p>没有找到匹配的卡牌</p>
                        </div>
                    )
                ) : (
                    normalCards.map((card) => (
                        <GameCard
                            key={card.id}
                            className={styles.cardItem}
                            hoverable
                            onClick={() => handleCardClick(card)}
                            glow={card.status === 'endangered'}
                        >
                            <div className={styles.cardHeader}>
                                <span className={styles.cardIcon}>{getAlgorithmIcon(card.algorithm_type || card.algorithmCategory)}</span>
                                <div className={styles.cardTitleArea}>
                                    <h3 className={styles.cardName}>{card.name}</h3>
                                    <span className={styles.cardCategory}>{card.algorithm_type || card.algorithmCategory}</span>
                                </div>
                                <span className={`${styles.statusTag} ${getStatusClass(card.status)}`}>
                                    {getStatusLabel(card.status)}
                                </span>
                            </div>

                            <div className={styles.durabilitySection} style={{ position: 'relative' }}>
                                {durabilityAnimations[card.id] && (
                                    <DurabilityChange
                                        key={durabilityAnimations[card.id].key}
                                        value={durabilityAnimations[card.id].value}
                                        onDone={() => setDurabilityAnimations(prev => {
                                            const next = { ...prev }
                                            delete next[card.id]
                                            return next
                                        })}
                                    />
                                )}
                                <div className={styles.durBar}>
                                    <div
                                        className={styles.durFill}
                                        style={{
                                            width: `${(card.durability / card.max_durability || card.durability / card.maxDurability) * 100}%`,
                                            background:
                                                card.durability >= 60
                                                    ? 'var(--color-success)'
                                                    : card.durability >= 30
                                                        ? 'var(--color-warning)'
                                                        : 'var(--color-danger)',
                                            ...(card.status === 'endangered' && { animation: 'pulse-glow 2s infinite' }),
                                        }}
                                    />
                                </div>
                                <span className={styles.durText}>
                                    耐久 {card.durability}/{card.max_durability || card.maxDurability}
                                </span>
                            </div>

                            <div className={styles.cardMeta}>
                                <span>修炼 {card.review_count || card.reviewCount || 0}次</span>
                            </div>

                            {card.status === 'pending_retake' && (
                                <RetakeButton card={card} />
                            )}
                        </GameCard>
                    ))
                )}
            </div>

            <PendingRetakeSection
                cards={pendingRetakeCards}
                onCardClick={handleCardClick}
            />

            {sealedCards.length > 0 && (
                <div className={styles.sealedSection}>
                    <button
                        className={styles.sealedHeader}
                        onClick={() => setSealedSectionOpen(!sealedSectionOpen)}
                    >
                        <span className={styles.sealedTitle}>🔒 封印卡牌 ({sealedCards.length})</span>
                        <span className={`${styles.sealedToggle} ${sealedSectionOpen ? styles.sealedToggleOpen : ''}`}>
                            ▼
                        </span>
                    </button>
                    {sealedSectionOpen && (
                        <div className={styles.sealedGrid}>
                            {sealedCards.map((card) => (
                                <div key={card.id} className={styles.sealedCard}>
                                    <div className={styles.sealedCardHeader}>
                                        <span className={styles.sealedCardIcon}>🔒</span>
                                        <div className={styles.sealedCardInfo}>
                                            <h4 className={styles.sealedCardName}>{card.name}</h4>
                                            {(card.algorithm_type || card.algorithmCategory) && (
                                                <span className={styles.sealedCardCategory}>{card.algorithm_type || card.algorithmCategory}</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className={styles.sealedCardMeta}>
                                        <span>耐久 {card.durability}/{card.max_durability || card.maxDurability}</span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleUnsealRequest(card)}
                                        className={styles.unsealBtn}
                                    >
                                        🔓 解封
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <Modal
                open={!!selectedCard}
                onClose={() => { setSelectedCard(null); setIsEditing(false) }}
                title={selectedCard?.name || ''}
                size="lg"
            >
                {selectedCard && (
                    <div className={styles.modalContent}>
                        <div className={styles.heroSection}>
                            <span className={`${styles.heroIcon} ${getStatusClass(selectedCard.status)}`}>
                                {getAlgorithmIcon(selectedCard.algorithm_type || selectedCard.algorithmCategory)}
                            </span>
                            <h2 className={styles.heroName}>{selectedCard.name}</h2>
                            <div className={styles.heroBadges}>
                                {(selectedCard.algorithm_type || selectedCard.algorithmCategory) && (
                                    <span className={styles.heroCategoryBadge}>{selectedCard.algorithm_type || selectedCard.algorithmCategory}</span>
                                )}
                                <span className={`${styles.heroStatus} ${getStatusClass(selectedCard.status)}`}>
                                    {getStatusLabel(selectedCard.status)}
                                </span>
                            </div>
                            <div className={styles.heroDivider} />
                        </div>

                        <div className={styles.statsGrid}>
                            <div className={styles.statCell} style={{ position: 'relative' }}>
                                <span className={styles.statIcon}>🛡️</span>
                                <span className={styles.statValue}>
                                    {Math.round((selectedCard.durability / (selectedCard.max_durability || selectedCard.maxDurability)) * 100)}%
                                </span>
                                <span className={styles.statDesc}>
                                    {selectedCard.durability >= 60 ? '状态良好' : selectedCard.durability >= 30 ? '需要关注' : '濒危警告'}
                                </span>
                                {durabilityAnimations[selectedCard.id] && (
                                    <DurabilityChange
                                        key={durabilityAnimations[selectedCard.id].key}
                                        value={durabilityAnimations[selectedCard.id].value}
                                        onDone={() => setDurabilityAnimations(prev => {
                                            const next = { ...prev }
                                            delete next[selectedCard.id]
                                            return next
                                        })}
                                    />
                                )}
                                <div className={styles.durProgressBar}>
                                    <div
                                        className={styles.durProgressFill}
                                        style={{
                                            width: `${(selectedCard.durability / (selectedCard.max_durability || selectedCard.maxDurability)) * 100}%`,
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

                            {selectedCard.review_level != null && (
                                <div className={styles.statCell}>
                                    <span className={styles.statIcon}>⚔️</span>
                                    <span className={styles.statValue}>Lv.{selectedCard.review_level}</span>
                                    <span className={styles.statDesc}>
                                        {selectedCard.review_level <= 1 ? '初窥门径'
                                            : selectedCard.review_level <= 3 ? '初学乍练'
                                            : selectedCard.review_level <= 5 ? '小有所成'
                                            : selectedCard.review_level <= 7 ? '融会贯通'
                                            : '登峰造极'}
                                    </span>
                                </div>
                            )}

                            <div className={styles.statCell}>
                                <span className={styles.statIcon}>📖</span>
                                <span className={styles.statValue}>{selectedCard.review_count || selectedCard.reviewCount || 0}</span>
                                <span className={styles.statDesc}>次修炼</span>
                            </div>
                        </div>

                        {!isEditing && (
                            <div className={styles.infoRow}>
                                <span className={styles.infoItem}>📅 {new Date(selectedCard.created_at || selectedCard.createdAt).toLocaleDateString()}</span>
                                <span className={styles.infoDot}>·</span>
                                <span className={styles.infoItem}>
                                    🕐 {selectedCard.last_reviewed || selectedCard.lastReviewed ? new Date(selectedCard.last_reviewed || selectedCard.lastReviewed).toLocaleDateString() : '从未修炼'}
                                </span>
                                {(selectedCard.algorithm_type || selectedCard.algorithmType) && (
                                    <>
                                        <span className={styles.infoDot}>·</span>
                                        <span className={styles.infoItem}>
                                            <span className={styles.runeTagInline}>{selectedCard.algorithm_type || selectedCard.algorithmType}</span>
                                        </span>
                                    </>
                                )}
                            </div>
                        )}

                        {isEditing ? (
                            <CardEditForm
                                card={selectedCard}
                                onSave={handleEditSave}
                                onCancel={handleCancelEdit}
                            />
                        ) : (
                            <>
                                <DimensionSection card={selectedCard} />
                                <VisualLinksSection visualLinks={selectedCard.visual_links} />
                            </>
                        )}

                        <div className={styles.modalActions}>
                            {isEditing ? null : (
                                <>
                                    <Button variant="primary" onClick={() => handleReview(selectedCard)} className={styles.reviewBtn}>
                                        📖 修炼此卡牌
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        onClick={handleEdit}
                                        className={styles.editBtn}
                                    >
                                        ✏️ 编辑
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        onClick={() => handleDeleteRequest(selectedCard)}
                                        className={styles.deleteBtn}
                                    >
                                        🗑️ 删除卡牌
                                    </Button>
                                </>
                            )}
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

            <ConfirmDialog
                open={unsealConfirmOpen}
                onClose={() => setUnsealConfirmOpen(false)}
                onConfirm={handleUnsealConfirm}
                title="确认解封"
                message={`确定要解封「${cardToUnseal?.name}」吗？\n解封后耐久度将恢复至30，卡牌重新参与遗忘曲线计算。`}
                confirmText="确认解封"
                cancelText="取消"
                loading={isUnsealing}
            />

            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={() => { setCreateModalOpen(false); fetchCards() }}
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
