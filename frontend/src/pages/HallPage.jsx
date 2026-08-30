import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../services/cardService'
import { useHallStore } from '../stores/hallStore'
import GreetingSection from '../components/workbench/GreetingSection'
import PanelSection from '../components/workbench/PanelSection'
import ActivityLog from '../components/workbench/ActivityLog'
import TodayReview from '../components/workbench/TodayReview'
import styles from './HallPage.module.css'

export default function HallPage() {
    const { fetchAlgorithmInfo, fetchTopicOverview } = useHallStore()

    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState(null)

    useEffect(() => {
        fetchAlgorithmInfo()
        fetchTopicOverview()

        let cancelled = false

        async function fetchData() {
            setLoading(true)
            try {
                const res = await cardService.getTodayReviewTasks?.()
                if (cancelled) return
                const t = res?.data || res || {}
                setStats({
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

    return (
        <div className={styles.hallPage}>
            <div className={styles.content}>
                <GreetingSection loading={loading} stats={stats} />

                <PanelSection number="01" title="system.log — 历程轨迹" path="/logs">
                    <ActivityLog />
                </PanelSection>

                <TodayReview />
            </div>
        </div>
    )
}
