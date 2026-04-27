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

            {selectedCard.note && (
              <div className={styles.noteSection}>
                <div className={styles.noteHeader}>
                  <span className={styles.detailLabel}>📝 关联笔记</span>
                  {selectedCard.note.is_favorite === 1 && <span className={styles.favoriteIcon}>⭐</span>}
                </div>
                <div className={styles.noteCard}>
                  <h4 className={styles.noteTitle}>{selectedCard.note.title}</h4>
                  {selectedCard.note.summary && (
                    <p className={styles.noteSummary}>{selectedCard.note.summary}</p>
                  )}
                  <div className={styles.noteContent}>
                    {selectedCard.note.content}
                  </div>
                  {selectedCard.note.algorithm_type && (
                    <div className={styles.noteMeta}>
                      <span className={styles.noteTag}>{selectedCard.note.algorithm_type}</span>
                      {selectedCard.note.difficulty && (
                        <span className={styles.noteTag}>{selectedCard.note.difficulty}</span>
                      )}
                      <span className={styles.noteTag}>掌握度: {selectedCard.note.mastery_level}%</span>
                    </div>
                  )}
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
