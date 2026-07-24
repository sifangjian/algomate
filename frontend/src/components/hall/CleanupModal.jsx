import { useState, useEffect } from 'react'
import { useHallStore } from '../../stores/hallStore'
import styles from './CleanupModal.module.css'

export default function CleanupModal({ onClose }) {
  const { emptyCards, fetchEmptyCards, cleanupEmptyCards } = useHallStore()
  const [cleaning, setCleaning] = useState(false)
  const [report, setReport] = useState(null)

  useEffect(() => {
    fetchEmptyCards()
  }, [fetchEmptyCards])

  const handleCleanup = async () => {
    setCleaning(true)
    try {
      const result = await cleanupEmptyCards()
      setReport(result)
    } catch (err) {
      console.error('Cleanup failed:', err)
    } finally {
      setCleaning(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <h3 className={styles.title}>清理空卡牌</h3>

        {!report ? (
          <>
            <p className={styles.desc}>
              以下 <strong>{emptyCards.length}</strong> 张卡牌内容为空，可以被清理：
            </p>
            <ul className={styles.cardList}>
              {emptyCards.map(card => (
                <li key={card.id} className={styles.cardItem}>
                  <span className={styles.cardName}>{card.name}</span>
                  <span className={styles.cardType}>{card.algorithm_type}</span>
                </li>
              ))}
            </ul>
            {emptyCards.length === 0 && (
              <p className={styles.noEmpty}>没有需要清理的空卡牌</p>
            )}
            <div className={styles.actions}>
              <button className={styles.cancelBtn} onClick={onClose}>取消</button>
              <button
                className={styles.confirmBtn}
                onClick={handleCleanup}
                disabled={cleaning || emptyCards.length === 0}
              >
                {cleaning ? '清理中...' : '确认清理'}
              </button>
            </div>
          </>
        ) : (
          <>
            <p className={styles.reportText}>
              清理完成！共删除 <strong>{report.deleted_count}</strong> 张空卡牌。
            </p>
            <ul className={styles.cardList}>
              {report.deleted_cards?.map(card => (
                <li key={card.id} className={styles.cardItem}>
                  <span className={styles.cardName}>{card.name}</span>
                  <span className={styles.cardType}>{card.algorithm_type}</span>
                </li>
              ))}
            </ul>
            <div className={styles.actions}>
              <button className={styles.confirmBtn} onClick={onClose}>确定</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
