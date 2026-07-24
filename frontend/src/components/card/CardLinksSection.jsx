import { useState, useEffect, useCallback, memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import CardLinkEditor from './CardLinkEditor'
import styles from './CardLinksSection.module.css'

const LINK_TYPE_LABELS = {
  related: '关联',
  prerequisite: '前置',
  comparison: '对比',
  keyword: '关键词',
}

export default function CardLinksSection({ card }) {
  const { linkedCards, fetchLinkedCards, removeCardLink } = useCardStore()
  const [showEditor, setShowEditor] = useState(false)

  useEffect(() => {
    if (card?.id) {
      fetchLinkedCards(card.id)
    }
  }, [card?.id, fetchLinkedCards])

  const links = linkedCards[card?.id] || []

  const handleRemove = useCallback(async (linkId) => {
    await removeCardLink(linkId, card.id)
  }, [removeCardLink, card.id])

  const handleLinkAdded = useCallback(() => {
    setShowEditor(false)
    fetchLinkedCards(card.id)
  }, [fetchLinkedCards, card.id])

  if (!card) return null

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h4 className={styles.title}>🔗 知识关联</h4>
        <button className={styles.addBtn} onClick={() => setShowEditor(true)}>
          + 添加关联
        </button>
      </div>

      {links.length === 0 && !showEditor && (
        <p className={styles.empty}>暂无关联卡牌，点击上方按钮添加</p>
      )}

      <div className={styles.linksList}>
        {links.map((link) => {
          const linkName = link.direction === 'outgoing' ? link.target_card_name : link.source_card_name
          return (
          <div key={link.id} className={styles.linkItem}>
            <span className={styles.linkType}>
              {LINK_TYPE_LABELS[link.link_type] || link.link_type}
            </span>
            <span className={styles.linkName}>
              {linkName}
            </span>
            {link.source_keyword && (
              <span className={styles.keyword}>#{link.source_keyword}</span>
            )}
            <span className={styles.direction}>
              {link.direction === 'outgoing' ? '→' : '←'}
            </span>
            <button
              className={styles.removeBtn}
              onClick={() => handleRemove(link.id)}
              title="移除关联"
            >
              ✕
            </button>
          </div>
          )
        })}
      </div>

      {showEditor && (
        <CardLinkEditor
          cardId={card.id}
          onLinkAdded={handleLinkAdded}
          onCancel={() => setShowEditor(false)}
        />
      )}
    </div>
  )
}
