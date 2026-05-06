import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Input from '../components/ui/Input/Input'
import Button from '../components/ui/Button/Button'
import Modal from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import EndangeredBanner from '../components/card/EndangeredBanner'
import PendingRetakeSection from '../components/card/PendingRetakeSection'
import CardDetailDrawer from '../components/card/CardDetailDrawer'
import styles from './CardWorkshop.module.css'

const ALGORITHM_CATEGORIES = [
    'Search', 'Sorting', 'Dynamic Programming', 'Graph',
    'Tree', 'Recursion', 'Array', 'String', 'Greedy', 'Math',
]

const ALGORITHM_ICONS = {
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
        algorithm_type: '',
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
            algorithm_type: '',
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
                algorithm_type: form.algorithm_type.trim() || null,
                difficulty: form.difficulty,
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
        <Modal open={open} onClose={handleClose} title="✨ 创建新卡牌" size="lg">
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
                    <label className={styles.fieldLabel} htmlFor="card-type">
                        算法类型
                    </label>
                    <input
                        id="card-type"
                        className={styles.fieldInput}
                        placeholder="如：Dynamic Programming"
                        value={form.algorithm_type}
                        onChange={(e) => handleFieldChange('algorithm_type', e.target.value)}
                        list="type-list"
                    />
                    <datalist id="type-list">
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
        cards, selectedCard, setSelectedCard,
        endangeredCount, pendingRetakeCount, loading, filters,
        setFilters, fetchCards, fetchCardDetail,
    } = useCardStore()

    const [searchKeyword, setSearchKeyword] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')
    const [createModalOpen, setCreateModalOpen] = useState(false)
    const [detailLoading, setDetailLoading] = useState(false)

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

    const displayCards = useMemo(
        () => cards.filter((c) => c.status !== 'pending_retake'),
        [cards]
    )

    const handleSearchChange = useCallback((e) => {
        setSearchKeyword(e.target.value)
    }, [])

    const handleStatusFilterChange = useCallback((e) => {
        setFilters({ status: e.target.value })
    }, [setFilters])

    const handleAlgorithmTypeClick = useCallback((type) => {
        setFilters({ algorithm_type: filters.algorithm_type === type ? '' : type })
    }, [filters.algorithm_type, setFilters])

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

    const handleDrawerClose = useCallback(() => {
        setSelectedCard(null)
    }, [setSelectedCard])

    const handleReview = useCallback(
        (card) => {
            navigate(`/boss/battle?cardId=${card.id}`)
        },
        [navigate]
    )

    const hasNoCards = cards.length === 0
    const hasNoFilters = !debouncedSearch && !filters.status && !filters.algorithm_type

    return (
        <div className={`${styles.container} page-container`}>
            <EndangeredBanner onCardClick={handleReview} />

            <div className={styles.mainLayout}>
                <aside className={styles.typeSidebar}>
                    <h3 className={styles.sidebarTitle}>算法类型</h3>
                    <div className={styles.typeList}>
                        <button
                            className={`${styles.typeTab} ${!filters.algorithm_type ? styles.typeTabActive : ''}`}
                            onClick={() => setFilters({ algorithm_type: '' })}
                        >
                            <span className={styles.typeTabIcon}>📜</span>
                            <span>全部</span>
                        </button>
                        {ALGORITHM_CATEGORIES.map((type) => (
                            <button
                                key={type}
                                className={`${styles.typeTab} ${filters.algorithm_type === type ? styles.typeTabActive : ''}`}
                                onClick={() => handleAlgorithmTypeClick(type)}
                            >
                                <span className={styles.typeTabIcon}>{ALGORITHM_ICONS[type]}</span>
                                <span>{type}</span>
                            </button>
                        ))}
                    </div>
                </aside>

                <div className={styles.mainArea}>
                    <div className={styles.pageHeader}>
                        <div>
                            <h1 className={styles.pageTitle}>🎴 卡牌工坊</h1>
                            <p className={styles.pageSubtitle}>管理你的算法知识卡牌</p>
                        </div>
                        <button
                            className={styles.createBtn}
                            onClick={() => setCreateModalOpen(true)}
                        >
                            ➕ 创建新卡牌
                        </button>
                    </div>

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
                            value={filters.status}
                            onChange={handleStatusFilterChange}
                            aria-label="状态筛选"
                        >
                            {STATUS_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className={styles.cardGrid}>
                        {loading ? (
                            <div className={styles.emptyState}>
                                <span className={styles.emptyIcon}>⏳</span>
                                <p>加载中...</p>
                            </div>
                        ) : hasNoCards && hasNoFilters ? (
                            <div className={styles.emptyGuide}>
                                <span className={styles.emptyGuideIcon}>🏔️</span>
                                <p className={styles.emptyGuideTitle}>还没有卡牌</p>
                                <p className={styles.emptyGuideDesc}>前往秘境修习，获取你的第一张卡牌</p>
                                <button className={styles.emptyGuideBtn} onClick={() => navigate('/hall')}>
                                    开始修习 →
                                </button>
                            </div>
                        ) : displayCards.length === 0 ? (
                            <div className={styles.emptyState}>
                                <span className={styles.emptyIcon}>🎴</span>
                                <p>没有找到匹配的卡牌</p>
                            </div>
                        ) : (
                            displayCards.map((card) => (
                                <GameCard
                                    key={card.id}
                                    card={card}
                                    onClick={() => handleCardClick(card)}
                                />
                            ))
                        )}
                    </div>

                    <PendingRetakeSection />
                </div>
            </div>

            <CardDetailDrawer
                open={!!selectedCard}
                onClose={handleDrawerClose}
            />

            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={() => { setCreateModalOpen(false); fetchCards() }}
            />
        </div>
    )
}
