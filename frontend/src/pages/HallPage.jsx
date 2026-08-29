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
    const [todayStats, setTodayStats] = useState({ due: 0, endangered: 0, completed: 0 })

    useEffect(() => {
        fetchAlgorithmInfo()
        fetchTopicOverview()

        let cancelled = false

        async function fetchData() {
            setLoading(true)
            try {
                const todayRes = await cardService.getTodayReviewTasks?.()
                if (cancelled) return
                const t = todayRes?.data || todayRes || {}
                setTodayStats({
                    due: t?.due_count ?? 0,
                    endangered: t?.endangered_count ?? 0,
                    completed: t?.completed_count ?? 0,
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

    // 今日行动建议（纯文字分析，不显示统计数字——统计统一放底部 StatusBar）
    const advice = (() => {
        if (loading) return '正在分析今日情况…'
        if (todayStats.due === 0) return '今天没有待复习的卡牌，去导入一道新题或回顾旧题吧。'
        if (todayStats.endangered > 0) {
            return `今天有 ${todayStats.due} 题待重做，其中 ${todayStats.endangered} 题已濒危，建议优先处理濒危题，避免遗忘加深。`
        }
        return `今天有 ${todayStats.due} 题待重做，按计划重做一遍即可巩固记忆。`
    })()

    return (
        <div className={styles.hallPage}>
            <div className={styles.content}>
                <GreetingSection loading={loading} stats={stats} />

                <PanelSection number="01" title="system.log — 历程轨迹" path="/logs">
                    <ActivityLog />
                </PanelSection>

                <PanelSection number="02" title="today.focus — 今日聚焦" path="/review">
                    <div
                        className={styles.focusCard}
                        onClick={() => navigate('/review')}
                        role="button"
                        title="查看今日修炼"
                    >
                        <div className={styles.focusAdvice}>
                            <span className={styles.focusIcon}>💡</span>
                            <span>{advice}</span>
                        </div>
                        <span className={styles.focusCta}>前往今日修炼 →</span>
                    </div>
                </PanelSection>
            </div>
        </div>
    )
}
