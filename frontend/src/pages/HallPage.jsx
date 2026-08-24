import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import { useHallStore } from '../stores/hallStore'
import GreetingSection from '../components/workbench/GreetingSection'
import PanelSection from '../components/workbench/PanelSection'
import ActivityLog from '../components/workbench/ActivityLog'
import StatusMonitor from '../components/workbench/StatusMonitor'
import TodayTasks from '../components/workbench/TodayTasks'
import styles from './HallPage.module.css'

function mapTaskStatus(s) {
    const map = { pending: 'PENDING', in_progress: 'IN_PROGRESS', done: 'DONE' }
    return map[s] || 'PENDING'
}

function mapTaskType(t) {
    const map = { problem: 'problem', solution: 'solution', technique: 'technique' }
    return map[t] || 'technique'
}

export default function HallPage() {
    const navigate = useNavigate()
    const { fetchAlgorithmInfo, fetchTopicOverview } = useHallStore()

    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState(null)
    const [tasks, setTasks] = useState(null)

    useEffect(() => {
        fetchAlgorithmInfo()
        fetchTopicOverview()

        let cancelled = false

        async function fetchData() {
            setLoading(true)
            try {
                const [todayTasks, dashboardStats, progressStats, overview, upcoming, todayStats, hallStats] = await Promise.allSettled([
                    cardService.getTodayTasks?.(),
                    cardService.getDashboardStats?.(),
                    cardService.getProgressStats?.(),
                    cardService.getOverview?.(),
                    cardService.getUpcomingTasks?.(),
                    cardService.getTodayStats?.(),
                    cardService.getHallStats?.(),
                ])

                if (cancelled) return

                const taskData = todayTasks.status === 'fulfilled' ? todayTasks.value : null
                const dashData = dashboardStats.status === 'fulfilled' ? dashboardStats.value : null
                const progData = progressStats.status === 'fulfilled' ? progressStats.value : null
                const overviewData = overview.status === 'fulfilled' ? overview.value : null
                const upcomingData = upcoming.status === 'fulfilled' ? upcoming.value : null
                const todayStatsData = todayStats.status === 'fulfilled' ? todayStats.value : null
                const hallStatsData = hallStats.status === 'fulfilled' ? hallStats.value : null

                const totalCards = (overviewData?.total_problems ?? 0) + (overviewData?.total_solutions ?? 0) + (overviewData?.total_techniques ?? 0)
                const nextReviewDays = upcomingData?.upcoming?.length > 0
                    ? Math.max(0, Math.ceil((new Date(upcomingData.upcoming[0].review_date) - new Date()) / (1000 * 60 * 60 * 24)))
                    : null

                setStats({
                    dueCount: dashData?.due_today_count ?? 0,
                    completedCount: dashData?.completed_today ?? 0,
                    totalCards: totalCards,
                    dueToday: dashData?.due_today_count ?? 0,
                    endangered: hallStatsData?.data?.endangered_cards ?? 0,
                    streakDays: todayStatsData?.data?.streak_days ?? 0,
                    weeklyProgress: `${dashData?.weekly_review_days ?? 0}/7`,
                    accuracy: progData?.accuracy_rate ?? 0,
                    totalReviews: dashData?.total_review_count ?? 0,
                    newToday: todayStatsData?.data?.total_new ?? 0,
                    nextReviewDays: nextReviewDays,
                })

                const taskList = taskData?.tasks || taskData?.data?.tasks || []
                setTasks(taskList.map(t => ({
                    id: t.id,
                    name: t.name || t.title || '未命名任务',
                    type: mapTaskType(t.type || t.card_type),
                    status: mapTaskStatus(t.status),
                })))
            } catch (err) {
                console.error('Failed to fetch hall data:', err)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        fetchData()
        return () => { cancelled = true }
    }, [fetchAlgorithmInfo, fetchTopicOverview])

    const handleTaskClick = useCallback((task) => {
        navigate(`/card/${task.type}/${task.id}`)
    }, [navigate])

    return (
        <div className={styles.hallPage}>
            <div className={styles.content}>
                <GreetingSection loading={loading} stats={stats} />

                <PanelSection number="01" title="system.log — 历程轨迹" path="/logs">
                    <ActivityLog />
                </PanelSection>

                <PanelSection number="02" title="system.status — 9 项指标 · 系统状态" path="/status">
                    <StatusMonitor loading={loading} stats={stats} />
                </PanelSection>

                <PanelSection number="03" title={`today.tasks — ${tasks?.length ?? 0} 项 · 今日任务列表`} path="/tasks">
                    <TodayTasks loading={loading} tasks={tasks} />
                </PanelSection>
            </div>
        </div>
    )
}