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

const REALM_OPTIONS = [
    { value: '新手森林', label: '🌲 新手森林' },
    { value: '迷雾沼泽', label: '🌫️ 迷雾沼泽' },
    { value: '智慧圣殿', label: '💡 智慧圣殿' },
    { value: '贪婪之塔', label: '🏰 贪婪之塔' },
    { value: '命运迷宫', label: '🌀 命运迷宫' },
    { value: '分裂山脉', label: '⛰️ 分裂山脉' },
    { value: '数学殿堂', label: '📐 数学殿堂' },
    { value: '试炼之地', label: '⚔️ 试炼之地' },
]

const ALGORITHM_CATEGORIES = [
    'Search', 'Sorting', 'Dynamic Programming', 'Graph',
    'Tree', 'Recursion', 'Array', 'String', 'Greedy', 'Math',
]

function CreateCardModal({ open, onClose, onCreated }) {
    const { addCard } = useCardStore()

    const [form, setForm] = useState({
        name: '',
        domain: '',
        algorithm_category: '',
        difficulty: 3,
        keyPoints: [],
        noteContent: '',
    })
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [keyPointInput, setKeyPointInput] = useState('')

    const [polishingField, setPolishingField] = useState(null)
    const [polishPreview, setPolishPreview] = useState(null)

    const resetForm = useCallback(() => {
        setForm({
            name: '',
            domain: '',
            algorithm_category: '',
            difficulty: 3,
            keyPoints: [],
            noteContent: '',
        })
        setErrors({})
        setKeyPointInput('')
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

    const handleAddKeyPoint = useCallback(() => {
        const trimmed = keyPointInput.trim()
        if (trimmed && !form.keyPoints.includes(trimmed)) {
            setForm((prev) => ({ ...prev, keyPoints: [...prev.keyPoints, trimmed] }))
            setKeyPointInput('')
        }
    }, [keyPointInput, form.keyPoints])

    const handleRemoveKeyPoint = useCallback((index) => {
        setForm((prev) => ({
            ...prev,
            keyPoints: prev.keyPoints.filter((_, i) => i !== index),
        }))
    }, [])

    const handleKeyPointKeyDown = useCallback((e) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddKeyPoint()
        }
    }, [handleAddKeyPoint])

    const handlePolish = useCallback(async (field) => {
        const content = field === 'key_points'
            ? form.keyPoints.join('\n')
            : form.noteContent

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
    }, [form.keyPoints, form.noteContent])

    const handleAcceptPolish = useCallback(() => {
        if (!polishPreview) return

        if (polishPreview.field === 'key_points') {
            const points = polishPreview.content
                .split('\n')
                .map((s) => s.replace(/^[-•*\d.)\s]+/, '').trim())
                .filter(Boolean)
            setForm((prev) => ({ ...prev, keyPoints: points }))
        } else {
            setForm((prev) => ({ ...prev, noteContent: polishPreview.content }))
        }

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
        if (!form.domain) newErrors.domain = '请选择所属秘境'
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }, [form.name, form.domain])

    const handleSubmit = useCallback(async () => {
        if (!validate()) return

        setIsSubmitting(true)
        try {
            const payload = {
                name: form.name.trim(),
                domain: form.domain,
                algorithm_category: form.algorithm_category.trim() || null,
                difficulty: form.difficulty,
                key_points: JSON.stringify(form.keyPoints),
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
                    <label className={styles.fieldLabel} htmlFor="card-domain">
                        所属秘境 <span className={styles.required}>*</span>
                    </label>
                    <select
                        id="card-domain"
                        className={`${styles.fieldSelect} ${errors.domain ? styles.fieldError : ''}`}
                        value={form.domain}
                        onChange={(e) => handleFieldChange('domain', e.target.value)}
                    >
                        <option value="">选择秘境...</option>
                        {REALM_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                    {errors.domain && <p className={styles.errorText}>{errors.domain}</p>}
                </div>

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
                        <label className={styles.fieldLabel}>关键要点</label>
                        <button
                            type="button"
                            className={styles.polishBtn}
                            onClick={() => handlePolish('key_points')}
                            disabled={!!polishingField || form.keyPoints.length === 0}
                        >
                            {polishingField === 'key_points' ? '⏳ 润色中...' : '✨ AI润色'}
                        </button>
                    </div>
                    <div className={styles.tagInput}>
                        <input
                            className={styles.tagInputField}
                            placeholder="输入要点后按回车添加"
                            value={keyPointInput}
                            onChange={(e) => setKeyPointInput(e.target.value)}
                            onKeyDown={handleKeyPointKeyDown}
                        />
                        <button
                            type="button"
                            className={styles.tagAddBtn}
                            onClick={handleAddKeyPoint}
                            disabled={!keyPointInput.trim()}
                        >
                            添加
                        </button>
                    </div>
                    {form.keyPoints.length > 0 && (
                        <div className={styles.tagList}>
                            {form.keyPoints.map((kp, i) => (
                                <span key={i} className={styles.tagItem}>
                                    {kp}
                                    <button
                                        type="button"
                                        className={styles.tagRemove}
                                        onClick={() => handleRemoveKeyPoint(i)}
                                        aria-label="移除"
                                    >
                                        ×
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                    {polishPreview && polishPreview.field === 'key_points' && (
                        <div className={styles.polishPreview}>
                            <div className={styles.polishPreviewHeader}>
                                <span>✨ AI润色结果</span>
                            </div>
                            <div className={styles.polishPreviewContent}>
                                {polishPreview.content.split('\n').map((line, i) => (
                                    <div key={i}>{line}</div>
                                ))}
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
    const [selectedRealm, setSelectedRealm] = useState('all')
    const [sortBy, setSortBy] = useState('name')
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

        if (searchKeyword.trim()) {
            const kw = searchKeyword.toLowerCase()
            result = result.filter(
                (c) =>
                    c.name.toLowerCase().includes(kw) ||
                    c.algorithmCategory?.toLowerCase().includes(kw) ||
                    c.keyPoints?.some((kp) => kp.toLowerCase().includes(kw))
            )
        }

        if (selectedRealm !== 'all') {
            result = result.filter((c) => c.realmId === selectedRealm)
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
    }, [cards, searchKeyword, selectedRealm, sortBy])

    const dangerCount = useMemo(
        () => cards.filter((c) => c.durability < 30).length,
        [cards]
    )

    const realms = useMemo(() => {
        const all = cards
        const unique = [...new Set(all.map((c) => c.realmId))]
        return unique.map((id) => {
            const card = all.find((c) => c.realmId === id)
            return { id, name: card?.realmName || id, icon: card?.realmIcon || '📍' }
        })
    }, [cards])

    const handleRealmChange = useCallback((realmId) => {
        const now = Date.now()
        if (now - lastClickTimeRef.current < DEBOUNCE_DELAY) {
            return
        }
        lastClickTimeRef.current = now
        setSelectedRealm(realmId)
    }, [])

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
        async (card) => {
            try {
                await cardService.startReview(card.id)
                showToast(`开始修炼「${card.name}」`, 'success')
                navigate(`/npc/${card.realmId}`)
            } catch (err) {
                showToast(`开始修炼失败: ${err.message}`, 'error')
            }
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
                        className={`${styles.realmTab} ${selectedRealm === 'all' ? styles.activeTab : ''}`}
                        onClick={() => handleRealmChange('all')}
                    >
                        全部
                    </button>
                    {realms.map((r) => (
                        <button
                            key={r.id}
                            className={`${styles.realmTab} ${selectedRealm === r.id ? styles.activeTab : ''}`}
                            onClick={() => handleRealmChange(r.id)}
                        >
                            {r.icon} {r.name}
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
                                <span>{card.realmIcon} {card.realmName}</span>
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
                title={`🎴 ${selectedCard?.name || ''}`}
                size="lg"
            >
                {selectedCard && (
                    <div className={styles.modalContent}>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>分类</span>
                            <span>{selectedCard.algorithmCategory}</span>
                        </div>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>所属秘境</span>
                            <span>
                                {selectedCard.realmIcon} {selectedCard.realmName}
                            </span>
                        </div>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>难度</span>
                            <span>{'★'.repeat(selectedCard.difficulty)}{'☆'.repeat(5 - selectedCard.difficulty)}</span>
                        </div>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>耐久度</span>
                            <div className={styles.durBarLarge}>
                                <div
                                    className={styles.durFill}
                                    style={{
                                        width: `${(selectedCard.durability / selectedCard.maxDurability) * 100}%`,
                                        background:
                                            selectedCard.durability >= 60
                                                ? 'var(--color-success)'
                                                : selectedCard.durability >= 30
                                                    ? 'var(--color-warning)'
                                                    : 'var(--color-danger)',
                                    }}
                                />
                                <span className={styles.durValue}>
                                    {selectedCard.durability}%{' '}
                                    {selectedCard.durability >= 60
                                        ? '(正常)'
                                        : selectedCard.durability >= 30
                                            ? '(注意)'
                                            : '(濒危)'}
                                </span>
                            </div>
                        </div>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>创建时间</span>
                            <span>{new Date(selectedCard.createdAt).toLocaleDateString()}</span>
                        </div>
                        <div className={styles.detailRow}>
                            <span className={styles.detailLabel}>最后修炼</span>
                            <span>{selectedCard.lastReviewed ? new Date(selectedCard.lastReviewed).toLocaleDateString() : '从未修炼'}</span>
                        </div>

                        {selectedCard.keyPoints?.length > 0 && (
                            <div className={styles.detailSection}>
                                <span className={styles.detailLabel}>关键要点</span>
                                <div className={styles.tagsList}>
                                    {selectedCard.keyPoints.map((kp, i) => (
                                        <span key={i} className={styles.tag}>{kp}</span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {selectedCard.knowledgeContent && (
                            <div className={styles.knowledgeSection}>
                                <span className={styles.detailLabel}>📖 知识内容</span>
                                <div className={styles.knowledgeContent}>
                                    {selectedCard.knowledgeContent}
                                </div>
                            </div>
                        )}

                        {selectedCard.summary && (
                            <div className={styles.detailRow}>
                                <span className={styles.detailLabel}>摘要</span>
                                <span className={styles.summaryText}>{selectedCard.summary}</span>
                            </div>
                        )}

                        {selectedCard.algorithmType && (
                            <div className={styles.detailRow}>
                                <span className={styles.detailLabel}>算法类型</span>
                                <span className={styles.tag}>{selectedCard.algorithmType}</span>
                            </div>
                        )}

                        {selectedCard.reviewLevel != null && (
                            <div className={styles.detailRow}>
                                <span className={styles.detailLabel}>修炼等级</span>
                                <span>Lv.{selectedCard.reviewLevel}</span>
                            </div>
                        )}

                        {selectedCard.nextReviewDate && (
                            <div className={styles.detailRow}>
                                <span className={styles.detailLabel}>下次修炼</span>
                                <span>{new Date(selectedCard.nextReviewDate).toLocaleDateString()}</span>
                            </div>
                        )}

                        <div className={styles.modalActions}>
                            <Button variant="primary" onClick={() => handleReview(selectedCard)}>
                                📖 修炼此卡牌
                            </Button>
                            <Button
                                variant="danger"
                                onClick={() => handleDeleteRequest(selectedCard)}
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
