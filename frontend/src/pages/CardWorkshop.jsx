import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../stores/cardStore'
import useDebounce from '../hooks/useDebounce'
import GameCard from '../components/ui/Card/GameCard'
import Input from '../components/ui/Input/Input'
import EndangeredBanner from '../components/card/EndangeredBanner'
import PendingRetakeSection from '../components/card/PendingRetakeSection'
import CardDetailDrawer from '../components/card/CardDetailDrawer'
import CreateCardModal from '../components/card/CreateCardModal'
import DailyReview from './DailyReview'
import { ALGORITHM_ICONS, ALGORITHM_CATEGORIES } from '../constants/algorithmConstants'
import styles from './CardWorkshop.module.css'

const STATUS_OPTIONS = [
    { value: '', label: '全部状态' },
    { value: 'normal', label: '正常' },
    { value: 'endangered', label: '濒危' },
    { value: 'pending_retake', label: '待重修' },
]

export default function CardWorkshop() {
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState('cards')
    const {
        cards, selectedCard, setSelectedCard,
        endangeredCount, pendingRetakeCount, loading, filters,
        setFilters, fetchCards, fetchCardDetail,
    } = useCardStore()

    const [searchKeyword, setSearchKeyword] = useState('')
    const debouncedSearch = useDebounce(searchKeyword, 300)
    const [createModalOpen, setCreateModalOpen] = useState(false)
    const [detailLoading, setDetailLoading] = useState(false)

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
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>🎴 卡牌图鉴</h1>
                    <p className={styles.pageSubtitle}>管理你的算法知识卡牌</p>
                </div>
                <button
                    className={styles.createBtn}
                    onClick={() => setCreateModalOpen(true)}
                >
                    ➕ 创建新卡牌
                </button>
            </div>

            <div className={styles.tabBar}>
                <button
                    className={`${styles.tabBtn} ${activeTab === 'cards' ? styles.tabBtnActive : ''}`}
                    onClick={() => setActiveTab('cards')}
                >
                    📜 卡牌图鉴
                </button>
                <button
                    className={`${styles.tabBtn} ${activeTab === 'review' ? styles.tabBtnActive : ''}`}
                    onClick={() => setActiveTab('review')}
                >
                    📋 每日修炼
                </button>
            </div>

            {activeTab === 'cards' && (
                <>
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
                </>
            )}

            {activeTab === 'review' && <DailyReview />}

            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={() => { setCreateModalOpen(false); fetchCards() }}
            />
        </div>
    )
}
