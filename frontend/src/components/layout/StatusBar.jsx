import { useEffect, useState } from 'react'
import { Icon } from '../ui/Icons'
import { cardService } from '../../services/cardService'
import styles from './StatusBar.module.css'

export default function StatusBar() {
    const [data, setData] = useState(null)
    const [apiOk, setApiOk] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [today, progress] = await Promise.allSettled([
                    cardService.getTodayReviewTasks?.(),
                    cardService.getProgressStats?.(),
                ])
                setApiOk(true)
                const t = today.status === 'fulfilled' ? today.value?.data : null
                const p = progress.status === 'fulfilled' ? progress.value : null
                setData({
                    due: t?.due_count ?? 0,
                    endangered: t?.endangered_count ?? 0,
                    completedToday: p?.completed_today ?? 0,
                    totalCards: p?.total_cards ?? 0,
                    totalPractice: p?.total_practice ?? 0,
                })
            } catch {
                setApiOk(false)
                setData(null)
            }
        }

        fetchData()
        const interval = setInterval(fetchData, 60000)
        return () => clearInterval(interval)
    }, [])

    const v = (x) => (data != null ? x : '—')

    return (
        <div className={styles.statusBar}>
            <div className={styles.left}>
                <span className={styles.dot}></span>
                <span className={styles.brand}>AlgoMate</span>
                <span className={styles.ver}>v0.1.0</span>
            </div>

            <div className={styles.center}>
                <span className={`${styles.item} ${styles.apiOk}`}>
                    <Icon name={apiOk ? 'check' : 'alert'} size={12} /> API {apiOk ? '正常' : '异常'}
                </span>
                <span className={styles.sep}>·</span>
                <span className={styles.item}>待复习 <b>{v(data?.due)}</b></span>
                <span className={styles.sep}>·</span>
                <span className={`${styles.item} ${Number(data?.endangered) > 0 ? styles.warn : ''}`}>濒危 <b>{v(data?.endangered)}</b></span>
                <span className={styles.sep}>·</span>
                <span className={styles.item}>今日已练 <b>{v(data?.completedToday)}</b></span>
                <span className={styles.sep}>·</span>
                <span className={styles.item}>卡牌 <b>{v(data?.totalCards)}</b> 张</span>
                <span className={styles.sep}>·</span>
                <span className={styles.item}>累计练习 <b>{v(data?.totalPractice)}</b> 次</span>
            </div>

            <div className={styles.right}>
                <span className={styles.item}>更新于 刚刚</span>
            </div>
        </div>
    )
}
