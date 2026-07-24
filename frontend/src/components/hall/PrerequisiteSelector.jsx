import { useState, useEffect } from 'react'
import { useHallStore } from '../../stores/hallStore'
import { cardService } from '../../services/cardService'
import styles from './PrerequisiteSelector.module.css'

export default function PrerequisiteSelector({ cardId, currentPrerequisites = [] }) {
  const { addPrerequisite, removePrerequisite } = useHallStore()
  const [allCards, setAllCards] = useState([])
  const [prerequisites, setPrerequisites] = useState(currentPrerequisites)
  const [showSelector, setShowSelector] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    cardService.getAll().then(data => {
      const cards = data?.cards || []
      setAllCards(cards.filter(c => c.id !== cardId))
    })
  }, [cardId])

  useEffect(() => {
    setPrerequisites(currentPrerequisites)
  }, [currentPrerequisites])

  const handleAdd = async (prereqId) => {
    setError('')
    setLoading(true)
    try {
      await addPrerequisite(cardId, prereqId)
      const prereqCard = allCards.find(c => c.id === prereqId)
      setPrerequisites(prev => [...prev, { id: prereqId, name: prereqCard?.name || '' }])
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || '添加失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (prereqId) => {
    setError('')
    try {
      await removePrerequisite(cardId, prereqId)
      setPrerequisites(prev => prev.filter(p => p.id !== prereqId))
    } catch (err) {
      setError('移除失败')
    }
  }

  const existingIds = new Set(prerequisites.map(p => p.id))
  const availableCards = allCards.filter(c => !existingIds.has(c.id))

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.label}>前置卡牌</span>
        <button
          className={styles.addBtn}
          onClick={() => setShowSelector(!showSelector)}
          disabled={loading}
        >
          + 添加
        </button>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.tags}>
        {prerequisites.map(p => (
          <span key={p.id} className={styles.tag}>
            {p.name}
            <button className={styles.tagRemove} onClick={() => handleRemove(p.id)}>×</button>
          </span>
        ))}
        {prerequisites.length === 0 && (
          <span className={styles.noTags}>暂无前置卡牌</span>
        )}
      </div>

      {showSelector && (
        <div className={styles.selector}>
          {availableCards.length === 0 ? (
            <p className={styles.noAvailable}>没有可选的卡牌</p>
          ) : (
            <ul className={styles.cardList}>
              {availableCards.map(c => (
                <li key={c.id} className={styles.cardOption} onClick={() => handleAdd(c.id)}>
                  <span className={styles.cardName}>{c.name}</span>
                  <span className={styles.cardType}>{c.algorithm_type}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
