import { useState, useEffect, useCallback, memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import { showToast } from '../ui/Toast/index'
import styles from './CardLinkEditor.module.css'

const LINK_TYPES = [
  { value: 'related', label: '关联' },
  { value: 'prerequisite', label: '前置知识' },
  { value: 'comparison', label: '对比' },
  { value: 'keyword', label: '关键词' },
]

function CardLinkEditor({ cardId, onLinkAdded, onCancel }) {
  const { cards, addCardLink } = useCardStore()
  const [targetCardId, setTargetCardId] = useState('')
  const [linkType, setLinkType] = useState('related')
  const [sourceKeyword, setSourceKeyword] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isAdding, setIsAdding] = useState(false)

  const filteredCards = cards.filter(
    (c) => c.id !== cardId && (
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.algorithm_type?.toLowerCase().includes(searchQuery.toLowerCase())
    )
  )

  const handleSubmit = useCallback(async () => {
    if (!targetCardId) {
      showToast('请选择目标卡牌', 'warning')
      return
    }
    setIsAdding(true)
    try {
      await addCardLink(cardId, parseInt(targetCardId), linkType, sourceKeyword || null)
      showToast('关联已添加', 'success')
      onLinkAdded?.()
    } catch (err) {
      showToast(`添加失败: ${err.message}`, 'error')
    } finally {
      setIsAdding(false)
    }
  }, [cardId, targetCardId, linkType, sourceKeyword, addCardLink, onLinkAdded])

  return (
    <div className={styles.editor}>
      <div className={styles.field}>
        <label className={styles.label}>搜索卡牌</label>
        <input
          className={styles.searchInput}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="输入卡牌名称或算法类型..."
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label}>选择目标卡牌</label>
        <select
          className={styles.select}
          value={targetCardId}
          onChange={(e) => setTargetCardId(e.target.value)}
        >
          <option value="">-- 选择卡牌 --</option>
          {filteredCards.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.algorithm_type})
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label className={styles.label}>链接类型</label>
        <div className={styles.typeButtons}>
          {LINK_TYPES.map((t) => (
            <button
              key={t.value}
              className={`${styles.typeBtn} ${linkType === t.value ? styles.typeBtnActive : ''}`}
              onClick={() => setLinkType(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {linkType === 'keyword' && (
        <div className={styles.field}>
          <label className={styles.label}>关键词</label>
          <input
            className={styles.keywordInput}
            value={sourceKeyword}
            onChange={(e) => setSourceKeyword(e.target.value)}
            placeholder="触发链接的关键词"
          />
        </div>
      )}

      <div className={styles.actions}>
        <button
          className={styles.submitBtn}
          onClick={handleSubmit}
          disabled={!targetCardId || isAdding}
        >
          {isAdding ? '添加中...' : '确认关联'}
        </button>
        <button className={styles.cancelBtn} onClick={onCancel}>
          取消
        </button>
      </div>
    </div>
  )
}

export default memo(CardLinkEditor)
