import { useState } from 'react'
import styles from './HallHeader.module.css'
import CleanupModal from './CleanupModal'

export default function HallHeader() {
  const [showCleanup, setShowCleanup] = useState(false)

  return (
    <div className={styles.hallHeader}>
      <div className={styles.titleRow}>
        <h1 className={styles.pageTitle}>算法地图</h1>
        <button className={styles.cleanupBtn} onClick={() => setShowCleanup(true)}>清理空卡牌</button>
      </div>
      {showCleanup && <CleanupModal onClose={() => setShowCleanup(false)} />}
    </div>
  )
}