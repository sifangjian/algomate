import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../services/cardService'
import { useHallStore } from '../stores/hallStore'
import GreetingSection from '../components/workbench/GreetingSection'
import PanelSection from '../components/workbench/PanelSection'
import CliCreator from '../components/workbench/CliCreator'
import StatusMonitor from '../components/workbench/StatusMonitor'
import TodayTasks from '../components/workbench/TodayTasks'
import CreateCardModal from '../components/card/CreateCardModal'
import styles from './HallPage.module.css'

const DEFAULT_STATS = {
    dueCount: 5,
    completedCount: 1,
    totalCards: 0,
    dueToday: 5,
    endangered: 2,
    streakDays: 0,
    weeklyProgress: '0/7',
    accuracy: 0,
    totalReviews: 0,
    newToday: 0,
    nextReviewDays: null,
}

const DEFAULT_TASKS = []

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

    const [createModalOpen, setCreateModalOpen] = useState(false)
    const [stats, setStats] = useState(DEFAULT_STATS)
    const [tasks, setTasks] = useState(DEFAULT_TASKS)

    useEffect(() => {
        fetchAlgorithmInfo()
        fetchTopicOverview()

        let cancelled = false

        async function fetchData() {
            try {
                const [todayTasks, dashboardStats, progressStats, overview, upcoming] = await Promise.allSettled([
                    cardService.getTodayTasks?.(),
                    cardService.getDashboardStats?.(),
                    cardService.getProgressStats?.(),
                    cardService.getOverview?.(),
                    cardService.getUpcomingTasks?.(),
                ])

                if (cancelled) return

                const taskData = todayTasks.status === 'fulfilled' ? todayTasks.value : null
                const dashData = dashboardStats.status === 'fulfilled' ? dashboardStats.value : null
                const progData = progressStats.status === 'fulfilled' ? progressStats.value : null
                const overviewData = overview.status === 'fulfilled' ? overview.value : null
                const upcomingData = upcoming.status === 'fulfilled' ? upcoming.value : null

                setStats({
                    dueCount: dashData?.due_count ?? DEFAULT_STATS.dueCount,
                    completedCount: dashData?.completed_count ?? DEFAULT_STATS.completedCount,
                    totalCards: overviewData?.total_cards ?? DEFAULT_STATS.totalCards,
                    dueToday: dashData?.due_count ?? DEFAULT_STATS.dueToday,
                    endangered: dashData?.endangered_count ?? DEFAULT_STATS.endangered,
                    streakDays: progData?.streak_days ?? DEFAULT_STATS.streakDays,
                    weeklyProgress: dashData?.weekly_progress ?? DEFAULT_STATS.weeklyProgress,
                    accuracy: progData?.accuracy_rate ?? DEFAULT_STATS.accuracy,
                    totalReviews: dashData?.total_review_count ?? DEFAULT_STATS.totalReviews,
                    newToday: dashData?.new_today ?? DEFAULT_STATS.newToday,
                    nextReviewDays: upcomingData?.days_until_next ?? null,
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
            }
        }

        fetchData()
        return () => { cancelled = true }
    }, [fetchAlgorithmInfo, fetchTopicOverview])

    useEffect(() => {
        const handler = () => setCreateModalOpen(true)
        window.addEventListener('open-create-card', handler)
        return () => window.removeEventListener('open-create-card', handler)
    }, [])

    const handleCreateCard = useCallback(() => {
        setCreateModalOpen(true)
    }, [])

    const handleCardCreated = useCallback((newCard) => {
        setCreateModalOpen(false)
        fetchAlgorithmInfo()
        fetchTopicOverview()
        if (newCard?.id) {
            const cardType = newCard.title ? 'problem' : newCard.problem_id ? 'solution' : 'technique'
            navigate(`/card/${cardType}/${newCard.id}`, { state: { autoEdit: true } })
        }
    }, [fetchAlgorithmInfo, fetchTopicOverview, navigate])

    return (
        <div className={styles.hallPage}>
            <div className={styles.content}>
                <GreetingSection stats={stats} />

                <PanelSection number="01" title="session.input — 创建卡片 · 输入 /new 开始" path="/cli">
                    <CliCreator onCreateCard={handleCreateCard} />
                </PanelSection>

                <PanelSection number="02" title="system.status — 9 项指标 · 系统状态" path="/status">
                    <StatusMonitor stats={stats} />
                </PanelSection>

                <PanelSection number="03" title={`today.tasks — ${tasks.length} 项 · 今日任务列表`} path="/tasks">
                    <TodayTasks tasks={tasks} />
                </PanelSection>
            </div>
            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={handleCardCreated}
            />
        </div>
    )
}
