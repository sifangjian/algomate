import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './CardWorkshop.module.css'

const MOCK_CARDS = [
  {
    id: 'card_001',
    name: '二分查找',
    algorithmCategory: 'Search',
    realmId: 'novice_forest',
    realmName: '新手森林',
    realmIcon: '🌲',
    durability: 65,
    maxDurability: 100,
    status: 'normal',
    createdAt: '2026-04-10T08:00:00Z',
    lastReviewed: '2026-04-20T15:30:00Z',
    reviewCount: 5,
    noteCount: 3,
    keyPoints: ['数组必须有序', '维护lo和hi指针', '每次缩小一半范围'],
    relatedAlgorithms: ['Binary Search', 'Lower Bound'],
    difficulty: 2,
  },
  {
    id: 'card_002',
    name: '快速排序',
    algorithmCategory: 'Sorting',
    realmId: 'novice_forest',
    realmName: '新手森林',
    realmIcon: '🌲',
    durability: 42,
    maxDurability: 100,
    status: 'warning',
    createdAt: '2026-04-12T10:00:00Z',
    lastReviewed: '2026-04-18T09:00:00Z',
    reviewCount: 3,
    noteCount: 2,
    keyPoints: ['选择pivot元素', '分区操作', '递归排序子数组'],
    relatedAlgorithms: ['QuickSort', 'MergeSort'],
    difficulty: 3,
  },
  {
    id: 'card_003',
    name: '动态规划-背包问题',
    algorithmCategory: 'Dynamic Programming',
    realmId: 'crystal_cave',
    realmName: '水晶洞穴',
    realmIcon: '💎',
    durability: 18,
    maxDurability: 100,
    status: 'danger',
    createdAt: '2026-03-20T14:00:00Z',
    lastReviewed: '2026-04-05T11:00:00Z',
    reviewCount: 8,
    noteCount: 5,
    keyPoints: ['定义状态转移方程', '边界条件处理', '空间优化技巧'],
    relatedAlgorithms: ['DP', '0/1 Knapsack'],
    difficulty: 4,
  },
  {
    id: 'card_004',
    name: '深度优先搜索',
    algorithmCategory: 'Graph',
    realmId: 'mist_swamp',
    realmName: '迷雾沼泽',
    realmIcon: '🌫️',
    durability: 88,
    maxDurability: 100,
    status: 'normal',
    createdAt: '2026-04-22T08:00:00Z',
    lastReviewed: '2026-04-26T16:00:00Z',
    reviewCount: 2,
    noteCount: 1,
    keyPoints: ['使用栈或递归', '标记已访问节点', '回溯恢复状态'],
    relatedAlgorithms: ['DFS', 'Backtracking'],
    difficulty: 2,
  },
  {
    id: 'card_005',
    name: 'BFS最短路径',
    algorithmCategory: 'Graph',
    realmId: 'mist_swamp',
    realmName: '迷雾沼泽',
    realmIcon: '🌫️',
    durability: 55,
    maxDurability: 100,
    status: 'normal',
    createdAt: '2026-04-15T12:00:00Z',
    lastReviewed: '2026-04-23T14:00:00Z',
    reviewCount: 4,
    noteCount: 2,
    keyPoints: ['队列存储待访问节点', '层次遍历', '无权图最短路径'],
    relatedAlgorithms: ['BFS', 'Shortest Path'],
    difficulty: 2,
  },
]

export default function CardWorkshop() {
  const navigate = useNavigate()
  const { cards, setCards, selectedCard, setSelectedCard, removeCard } = useCardStore()

  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedRealm, setSelectedRealm] = useState('all')
  const [sortBy, setSortBy] = useState('name')
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [cardToDelete, setCardToDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    cardService.getAll().then((data) => {
      if (Array.isArray(data) && data.length > 0) setCards(data)
    }).catch(() => {})
  }, [setCards])

  const filteredCards = useMemo(() => {
    let result = cards.length > 0 ? cards : MOCK_CARDS

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
    () => (cards.length > 0 ? cards : MOCK_CARDS).filter((c) => c.durability < 30).length,
    [cards]
  )

  const realms = useMemo(() => {
    const all = (cards.length > 0 ? cards : MOCK_CARDS)
    const unique = [...new Set(all.map((c) => c.realmId))]
    return unique.map((id) => {
      const card = all.find((c) => c.realmId === id)
      return { id, name: card?.realmName || id, icon: card?.realmIcon || '📍' }
    })
  }, [cards])

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
      navigate(`/npc/${card.realmId}`)
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
        <Button variant="accent" size="sm" icon="➕">
          创建新卡牌
        </Button>
      </div>

      {dangerCount > 0 && (
        <div className={styles.warningBanner} role="alert">
          <span>⚠️</span>
          <span>
            有 <strong>{dangerCount}</strong> 张卡牌濒危（耐久度 &lt; 30%），请及时复习！
          </span>
        </div>
      )}

      <div className={styles.toolbar}>
        <Input
          placeholder="搜索卡牌..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          icon="🔍"
          className={styles.searchInput}
        />
        <div className={styles.realmTabs}>
          <button
            className={`${styles.realmTab} ${selectedRealm === 'all' ? styles.activeTab : ''}`}
            onClick={() => setSelectedRealm('all')}
          >
            全部
          </button>
          {realms.map((r) => (
            <button
              key={r.id}
              className={`${styles.realmTab} ${selectedRealm === r.id ? styles.activeTab : ''}`}
              onClick={() => setSelectedRealm(r.id)}
            >
              {r.icon} {r.name}
            </button>
          ))}
        </div>
        <select
          className={styles.sortSelect}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          aria-label="排序方式"
        >
          <option value="name">按名称</option>
          <option value="durability">按耐久度</option>
          <option value="reviewedDate">按复习时间</option>
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
                <span>复习 {card.reviewCount}次</span>
                <span>笔记 {card.noteCount}</span>
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
              <span className={styles.detailLabel}>最后复习</span>
              <span>{new Date(selectedCard.lastReviewed).toLocaleDateString()}</span>
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

            <div className={styles.modalActions}>
              <Button variant="primary" onClick={() => handleReview(selectedCard)}>
                📖 复习此卡牌
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
        message={`确定要删除「${cardToDelete?.name}」卡牌吗？\n删除后关联的笔记将保留，但无法再通过卡牌访问。`}
        confirmText="确认删除"
        cancelText="取消"
        variant="danger"
        loading={isDeleting}
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
