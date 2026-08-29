import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import { useHallStore } from '../stores/hallStore'
import GreetingSection from '../components/workbench/GreetingSection'
import PanelSection from '../components/workbench/PanelSection'
import ActivityLog from '../components/workbench/ActivityLog'
import styles from './HallPage.module.css'

export default function HallPage() {
    const navigate = useNavigate()
    const { fetchAlgorithmInfo, fetchTopicOverview } = useHallStore()

    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState(null)
    const [todayStats, setTodayStats] = useState({ due: 0, endangered: 0, completed: 0, totalCards: 0, totalPractice: 0 })

    useEffect(() => {
        fetchAlgorithmInfo()
        fetchTopicOverview()

        let cancelled = false

        async function fetchData() {
            setLoading(true)
            try {
                const [progressRes, todayRes] = await Promise.allSettled([
                    cardService.getProgressStats?.(),
                    cardService.getTodayReviewTasks?.(),
                ])
                if (cancelled) return
                const p = progressRes.status === 'fulfilled' ? progressRes.value : null
                const t = todayRes.status === 'fulfilled' ? todayRes.value?.data : null
                setTodayStats({
                    due: t?.due_count ?? 0,
                    endangered: t?.endangered_count ?? 0,
                    completed: t?.completed_count ?? 0,
                    totalCards: p?.total_cards ?? 0,
                    totalPractice: p?.total_practice ?? 0,
                })
                setStats({
                    weeklyProgress: `${p?.weekly_review_days ?? 0}/7`,
                    accuracy: p?.accuracy_rate ?? 0,
                })
            } catch (err) {
                console.error('Failed to fetch hall data:', err)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        fetchData()
        const interval = setInterval(fetchData, 60000)
        return () => { cancelled = true; clearInterval(interval) }
    }, [fetchAlgorithmInfo, fetchTopicOverview])

    const overviewCards = [
        { key: 'due', label: '待复习', value: todayStats.due, cls: 'warning', filter: '' },
        { key: 'endangered', label: '濒危', value: todayStats.endangered, cls: 'critical', filter: 'critical' },
        { key: 'completed', label: '已完成', value: todayStats.completed, cls: 'normal', filter: 'done' },
    ]

    return (
        <div className={styles.hallPage}>
            <div className={styles.content}>
                <GreetingSection loading={loading} stats={stats} />

                <PanelSection number="01" title="system.log — 历程轨迹" path="/logs">
                    <ActivityLog />
                </PanelSection>

                <PanelSection number="02" title="today.review — 今日修炼概览" path="/review">
                    <div className={styles.overviewGrid}>
                        {overviewCards.map((c) => (
                            <button
                                key={c.key}
                                className={`${styles.overviewCard} ${styles[c.cls]}`}
                                onClick={() => navigate(`/review${c.filter ? `?filter=${c.filter}` : ''}`)}
                            >
                                <span className={styles.overviewNum}>{loading ? '—' : c.value}</span>
                                <span className={styles.overviewLabel}>{c.label}</span>
                            </button>
                        ))}
                    </div>
                    <div className={styles.overviewFooter}>
                        <span>卡牌总数 {loading ? '—' : todayStats.totalCards} 张</span>
                        <span>累计练习 {loading ? '—' : todayStats.totalPractice} 次</span>
                        <button className={styles.reviewLink} onClick={() => navigate('/review')}>进入今日修炼 →</button>
                    </div>
                </PanelSection>
            </div>
        </div>
    )
}
