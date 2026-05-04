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
    const { cards, setCards, selectedCard, setSelectedCard, removeCard, addCard, updateCard } = useCardStore()

    const [searchKeyword, setSearchKeyword] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [sortBy, setSortBy] = useState('name')
    const [selectedRealm, setSelectedRealm] = useState('')
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [cardToDelete, setCardToDelete] = useState(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const [createModalOpen, setCreateModalOpen] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [editForm, setEditForm] = useState({})
    const [isSaving, setIsSaving] = useState(false)
    const [sealedSectionOpen, setSealedSectionOpen] = useState(true)
    const [unsealConfirmOpen, setUnsealConfirmOpen] = useState(false)
    const [cardToUnseal, setCardToUnseal] = useState(null)
    const [isUnsealing, setIsUnsealing] = useState(false)
    const [editPolishingField, setEditPolishingField] = useState(null)
    const [editPolishPreview, setEditPolishPreview] = useState(null)
    const [durabilityAnimations, setDurabilityAnimations] = useState({})

    const lastClickTimeRef = useRef(0)
    const searchTimerRef = useRef(null)
    const DEBOUNCE_DELAY = 300

    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
        searchTimerRef.current = setTimeout(() => {
            setDebouncedSearch(searchKeyword)
        }, DEBOUNCE_DELAY)
        return () => {
            if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
        }
    }, [searchKeyword])

    const fetchCards = useCallback(async () => {
        setIsLoading(true)
        try {
            const params = {}
            if (selectedRealm) params.realm = selectedRealm
            if (debouncedSearch.trim()) params.search = debouncedSearch.trim()
            if (sortBy) {
                if (sortBy === 'reviewedDate') {
                    params.sort = 'last_reviewed'
                    params.order = 'desc'
                } else if (sortBy === 'durability') {
                    params.sort = 'durability'
                    params.order = 'asc'
                } else {
                    params.sort = 'name'
                    params.order = 'asc'
                }
            }
            const data = await cardService.getAll(params)
            if (Array.isArray(data)) setCards(data)
        } catch {
        } finally {
            setIsLoading(false)
        }
    }, [selectedRealm, debouncedSearch, sortBy, setCards])

    useEffect(() => {
        fetchCards()
    }, [fetchCards])

    useEffect(() => {
        if (!selectedCard) {
            setIsEditing(false)
            setEditForm({})
        }
    }, [selectedCard])


    const dangerCards = useMemo(
        () => cards.filter((c) => c.durability < 30 && !c.is_sealed),
        [cards]
    )

    const dangerCount = dangerCards.length

    const sealedCards = useMemo(
        () => cards.filter((c) => c.is_sealed),
        [cards]
    )

    const normalCards = useMemo(
        () => cards.filter((c) => !c.is_sealed),
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

    const handleEdit = useCallback(() => {
        if (!selectedCard) return
        setEditForm({
            name: selectedCard.name || '',
            algorithm_type: selectedCard.algorithmType || selectedCard.algorithm_type || '',
            knowledge_content: selectedCard.knowledgeContent || selectedCard.knowledge_content || '',
            summary: selectedCard.summary || '',
            key_points: Array.isArray(selectedCard.keyPoints || selectedCard.key_points) ? [...(selectedCard.keyPoints || selectedCard.key_points)] : [],
        })
        setIsEditing(true)
    }, [selectedCard])

    const handleCancelEdit = useCallback(() => {
        setIsEditing(false)
        setEditForm({})
    }, [])

    const handleSaveEdit = useCallback(async () => {
        if (!selectedCard) return
        setIsSaving(true)
        try {
            const payload = {
                name: editForm.name.trim(),
                algorithm_type: editForm.algorithm_type.trim() || null,
                knowledge_content: editForm.knowledge_content.trim() || null,
                summary: editForm.summary.trim() || null,
                key_points: JSON.stringify(editForm.key_points.filter(kp => kp.trim())),
            }
            const updated = await cardService.updateCard(selectedCard.id, payload)
            updateCard(selectedCard.id, updated)
            setSelectedCard(updated)
            setIsEditing(false)
            setEditForm({})
            showToast(`卡牌「${updated.name}」已更新`, 'success')
        } catch (err) {
            showToast(`保存失败: ${err.message}`, 'error')
        } finally {
            setIsSaving(false)
        }
    }, [selectedCard, editForm, updateCard, setSelectedCard])

    const handleEditFieldChange = useCallback((field, value) => {
        setEditForm(prev => ({ ...prev, [field]: value }))
    }, [])

    const handleAddKeyPoint = useCallback(() => {
        setEditForm(prev => ({
            ...prev,
            key_points: [...prev.key_points, ''],
        }))
    }, [])

    const handleRemoveKeyPoint = useCallback((index) => {
        setEditForm(prev => ({
            ...prev,
            key_points: prev.key_points.filter((_, i) => i !== index),
        }))
    }, [])

    const handleKeyPointChange = useCallback((index, value) => {
        setEditForm(prev => ({
            ...prev,
            key_points: prev.key_points.map((kp, i) => i === index ? value : kp),
        }))
    }, [])

    const handleEditPolish = useCallback(async (field) => {
        let content = ''
        if (field === 'summary') {
            content = editForm.summary || ''
        } else if (field === 'key_points') {
            content = editForm.key_points.filter(kp => kp.trim()).join('\n')
        } else {
            content = editForm.knowledge_content || ''
        }

        if (!content.trim()) {
            showToast('请先输入内容再进行润色', 'warning')
            return
        }

        setEditPolishingField(field)
        setEditPolishPreview(null)

        try {
            const result = await cardService.polishCard({ content, type: field })
            setEditPolishPreview({ field, content: result.polished_content })
        } catch (err) {
            showToast(`AI润色失败: ${err.message}`, 'error')
            setEditPolishingField(null)
        }
    }, [editForm])

    const handleEditPolishAccept = useCallback(() => {
        if (!editPolishPreview) return

        const { field, content } = editPolishPreview
        if (field === 'summary') {
            setEditForm(prev => ({ ...prev, summary: content }))
        } else if (field === 'key_points') {
            const points = content.split('\n').filter(line => line.trim())
            setEditForm(prev => ({ ...prev, key_points: points }))
        } else {
            setEditForm(prev => ({ ...prev, knowledge_content: content }))
        }

        setEditPolishPreview(null)
        setEditPolishingField(null)
    }, [editPolishPreview])

    const handleEditPolishReject = useCallback(() => {
        setEditPolishPreview(null)
        setEditPolishingField(null)
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
                    <div className={styles.warningBannerHeader}>
                        <span>⚠️</span>
                        <span>
                            有 <strong>{dangerCount}</strong> 张卡牌濒危（耐久度 &lt; 30%），请及时修炼！
                        </span>
                    </div>
                    <div className={styles.dangerCardList}>
                        {dangerCards.map((card) => (
                            <button
                                key={card.id}
                                className={styles.dangerCardItem}
                                onClick={() => handleReview(card)}
                                title={`点击修炼「${card.name}」`}
                            >
                                <span className={styles.dangerCardIcon}>{getAlgorithmIcon(card.algorithmCategory)}</span>
                                <span className={styles.dangerCardName}>{card.name}</span>
                                <span className={styles.dangerCardDur}>🛡️{card.durability}</span>
                                <span className={styles.dangerCardAction}>去修炼 →</span>
                            </button>
                        ))}
                    </div>
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
                {isLoading ? (
                    <div className={styles.emptyState}>
                        <span className={styles.emptyIcon}>⏳</span>
                        <p>加载中...</p>
                    </div>
                ) : normalCards.length === 0 && sealedCards.length === 0 ? (
                    <div className={styles.emptyState}>
                        <span className={styles.emptyIcon}>🎴</span>
                        <p>没有找到匹配的卡牌</p>
                    </div>
                ) : (
                    normalCards.map((card) => (
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
                                            {card.algorithmCategory && (
                                                <span className={styles.sealedCardCategory}>{card.algorithmCategory}</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className={styles.sealedCardMeta}>
                                        <span>耐久 {card.durability}/{card.maxDurability}</span>
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
                            {isEditing ? (
                                <Input
                                    value={editForm.name}
                                    onChange={(e) => handleEditFieldChange('name', e.target.value)}
                                    placeholder="卡牌名称"
                                    className={styles.editNameInput}
                                />
                            ) : (
                                <h2 className={styles.heroName}>{selectedCard.name}</h2>
                            )}
                            <div className={styles.heroBadges}>
                                {isEditing ? (
                                    <div className={styles.formField}>
                                        <input
                                            className={styles.fieldInput}
                                            placeholder="算法类型，如：二分查找"
                                            value={editForm.algorithm_type}
                                            onChange={(e) => handleEditFieldChange('algorithm_type', e.target.value)}
                                            list="edit-algorithm-type-list"
                                        />
                                        <datalist id="edit-algorithm-type-list">
                                            {ALGORITHM_CATEGORIES.map((c) => (
                                                <option key={c} value={c} />
                                            ))}
                                        </datalist>
                                    </div>
                                ) : (
                                    <>
                                        {selectedCard.algorithmCategory && (
                                            <span className={styles.heroCategoryBadge}>{selectedCard.algorithmCategory}</span>
                                        )}
                                        <span className={`${styles.heroStatus} ${styles[selectedCard.status]}`}>
                                            {selectedCard.status === 'normal' ? '正常' : selectedCard.status === 'warning' ? '注意' : '濒危'}
                                        </span>
                                    </>
                                )}
                            </div>
                            <div className={styles.heroDivider} />
                        </div>

                        <div className={styles.statsGrid}>
                            <div className={styles.statCell} style={{ position: 'relative' }}>
                                <span className={styles.statIcon}>🛡️</span>
                                <span className={styles.statValue}>
                                    {Math.round((selectedCard.durability / selectedCard.maxDurability) * 100)}%
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

                        {!isEditing && (
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
                        )}

                        {isEditing ? (
                            <>
                                <div className={styles.runeTagSection}>
                                    <div className={styles.fieldHeader}>
                                        <span className={styles.runeTagTitle}>🔑 关键要点</span>
                                        <div className={styles.fieldHeaderActions}>
                                            <button
                                                type="button"
                                                className={styles.polishBtn}
                                                onClick={() => handleEditPolish('key_points')}
                                                disabled={!!editPolishingField || editForm.key_points.every(kp => !kp.trim())}
                                            >
                                                {editPolishingField === 'key_points' ? '⏳ 润色中...' : '✨ AI润色'}
                                            </button>
                                            <button
                                                type="button"
                                                className={styles.addKeyPointBtn}
                                                onClick={handleAddKeyPoint}
                                            >
                                                + 添加
                                            </button>
                                        </div>
                                    </div>
                                    <div className={styles.keyPointsEditList}>
                                        {editForm.key_points.map((kp, i) => (
                                            <div key={i} className={styles.keyPointEditItem}>
                                                <input
                                                    className={styles.fieldInput}
                                                    value={kp}
                                                    onChange={(e) => handleKeyPointChange(i, e.target.value)}
                                                    placeholder="输入关键要点..."
                                                />
                                                <button
                                                    type="button"
                                                    className={styles.removeKeyPointBtn}
                                                    onClick={() => handleRemoveKeyPoint(i)}
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                    {editPolishPreview && editPolishPreview.field === 'key_points' && (
                                        <div className={styles.polishPreview}>
                                            <div className={styles.polishPreviewHeader}>
                                                <span>✨ AI润色结果</span>
                                            </div>
                                            <div className={styles.polishPreviewContent}>
                                                {editPolishPreview.content}
                                            </div>
                                            <div className={styles.polishPreviewActions}>
                                                <button
                                                    type="button"
                                                    className={styles.polishAcceptBtn}
                                                    onClick={handleEditPolishAccept}
                                                >
                                                    采纳
                                                </button>
                                                <button
                                                    type="button"
                                                    className={styles.polishRejectBtn}
                                                    onClick={handleEditPolishReject}
                                                >
                                                    放弃
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className={styles.formField}>
                                    <div className={styles.fieldHeader}>
                                        <label className={styles.fieldLabel}>📖 知识内容</label>
                                        <button
                                            type="button"
                                            className={styles.polishBtn}
                                            onClick={() => handleEditPolish('note_content')}
                                            disabled={!!editPolishingField || !editForm.knowledge_content?.trim()}
                                        >
                                            {editPolishingField === 'note_content' ? '⏳ 润色中...' : '✨ AI润色'}
                                        </button>
                                    </div>
                                    <textarea
                                        className={styles.fieldTextarea}
                                        value={editForm.knowledge_content}
                                        onChange={(e) => handleEditFieldChange('knowledge_content', e.target.value)}
                                        placeholder="输入知识内容..."
                                        rows={6}
                                    />
                                    {editPolishPreview && editPolishPreview.field === 'note_content' && (
                                        <div className={styles.polishPreview}>
                                            <div className={styles.polishPreviewHeader}>
                                                <span>✨ AI润色结果</span>
                                            </div>
                                            <div className={styles.polishPreviewContent}>
                                                {editPolishPreview.content}
                                            </div>
                                            <div className={styles.polishPreviewActions}>
                                                <button
                                                    type="button"
                                                    className={styles.polishAcceptBtn}
                                                    onClick={handleEditPolishAccept}
                                                >
                                                    采纳
                                                </button>
                                                <button
                                                    type="button"
                                                    className={styles.polishRejectBtn}
                                                    onClick={handleEditPolishReject}
                                                >
                                                    放弃
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className={styles.formField}>
                                    <div className={styles.fieldHeader}>
                                        <label className={styles.fieldLabel}>📝 心得总结</label>
                                        <button
                                            type="button"
                                            className={styles.polishBtn}
                                            onClick={() => handleEditPolish('summary')}
                                            disabled={!!editPolishingField || !editForm.summary?.trim()}
                                        >
                                            {editPolishingField === 'summary' ? '⏳ 润色中...' : '✨ AI润色'}
                                        </button>
                                    </div>
                                    <textarea
                                        className={styles.fieldTextarea}
                                        value={editForm.summary}
                                        onChange={(e) => handleEditFieldChange('summary', e.target.value)}
                                        placeholder="输入心得总结..."
                                        rows={3}
                                    />
                                    {editPolishPreview && editPolishPreview.field === 'summary' && (
                                        <div className={styles.polishPreview}>
                                            <div className={styles.polishPreviewHeader}>
                                                <span>✨ AI润色结果</span>
                                            </div>
                                            <div className={styles.polishPreviewContent}>
                                                {editPolishPreview.content}
                                            </div>
                                            <div className={styles.polishPreviewActions}>
                                                <button
                                                    type="button"
                                                    className={styles.polishAcceptBtn}
                                                    onClick={handleEditPolishAccept}
                                                >
                                                    采纳
                                                </button>
                                                <button
                                                    type="button"
                                                    className={styles.polishRejectBtn}
                                                    onClick={handleEditPolishReject}
                                                >
                                                    放弃
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : (
                            <>
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
                            </>
                        )}

                        <div className={styles.modalActions}>
                            {isEditing ? (
                                <>
                                    <Button
                                        variant="accent"
                                        onClick={handleSaveEdit}
                                        loading={isSaving}
                                    >
                                        💾 保存
                                    </Button>
                                    <Button variant="ghost" onClick={handleCancelEdit} disabled={isSaving}>
                                        取消
                                    </Button>
                                </>
                            ) : (
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
