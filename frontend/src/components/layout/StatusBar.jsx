import { useEffect, useState } from 'react'
import { Icon } from '../ui/Icons'
import { cardService } from '../../services/cardService'
import styles from './StatusBar.module.css'

export default function StatusBar() {
    const [stats, setStats] = useState(null)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await cardService.getProgressStats()
                setStats(data)
            } catch {
                setStats(null)
            }
        }

        fetchStats()
        const interval = setInterval(fetchStats, 60000)
        return () => clearInterval(interval)
    }, [])

    const val = (v) => (stats != null ? v : '—')

    return (
        <div className={styles.statusBar}>
            <div className={styles.left}>
                <span className={styles.dot}></span>
                <span className={styles.label}>AlgoMate</span>
            </div>
            <div className={styles.center}>
                <span className={styles.item}>v0.1.0</span>
                <span className={styles.separator}>|</span>
                <span className={`${styles.item} ${styles.statusOk}`}>
                    <Icon name="database" size={12} /> API
                </span>
                <span className={styles.separator}>|</span>
                <span className={`${styles.item} ${styles.statusOk}`}>
                    <Icon name="check" size={12} /> DB
                </span>
            </div>
            <div className={styles.right}>
                <span className={styles.item}>done: {val(stats?.completed_today)}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>cards: {val(stats?.total_cards)}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>reviews: {val(stats?.total_practice)}</span>
                <span className={styles.separator}>|</span>
                <span className={styles.item}>updated: just now</span>
            </div>
        </div>
    )
}
