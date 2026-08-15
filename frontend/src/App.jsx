import React, { lazy, Suspense, useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import TopTabs from './components/layout/TopTabs'
import SideNav from './components/layout/SideNav'
import StatusBar from './components/layout/StatusBar'
import BrandHeader from './components/layout/BrandHeader'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'
import { cardService } from './services/cardService'

const HallPage = lazy(() => import('./pages/HallPage'))
const TechniqueListPage = lazy(() => import('./pages/TechniqueListPage'))
const TopicDetailPage = lazy(() => import('./pages/TopicDetailPage'))
const CardDetailView = lazy(() => import('./components/card/CardDetailView'))
const NotFound = lazy(() => import('./pages/NotFound'))

function StudyRedirect() {
    const { cardId } = useParams()
    return <Navigate to={`/card/technique/${cardId}`} replace />
}

function AppContent() {
    const [sidebarStats, setSidebarStats] = useState({
        due: 0,
        endangered: 0,
        completed: 0,
        learningDays: 0,
    })
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

    const toggleSidebar = useCallback(() => {
        setSidebarCollapsed(prev => !prev)
    }, [])

    useEffect(() => {
        const root = document.documentElement
        if (sidebarCollapsed) {
            root.style.setProperty('--sidebar-width', 'var(--sidebar-collapsed-width)')
        } else {
            root.style.setProperty('--sidebar-width', '240px')
        }
    }, [sidebarCollapsed])

    useEffect(() => {
        let cancelled = false
        async function fetchSidebarData() {
            try {
                const [reviewData, progressData] = await Promise.allSettled([
                    cardService.getTodayReviewTasks?.(),
                    cardService.getProgressStats?.(),
                ])
                if (cancelled) return
                const reviews = reviewData.status === 'fulfilled' ? reviewData.value : null
                const progress = progressData.status === 'fulfilled' ? progressData.value : null
                setSidebarStats({
                    due: reviews?.due_count ?? 0,
                    endangered: reviews?.endangered_count ?? 0,
                    completed: reviews?.completed_count ?? 0,
                    learningDays: progress?.learning_days ?? 0,
                })
            } catch (err) {
                console.error('Failed to fetch sidebar data:', err)
            }
        }
        fetchSidebarData()
        return () => { cancelled = true }
    }, [])

    const handleCreateCard = () => {
        const event = new CustomEvent('open-create-card')
        window.dispatchEvent(event)
    }

    return (
        <div className="app-wrapper">
            <BrandHeader collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
            <TopTabs />
            <div className="app-body">
                <SideNav onCreateCard={handleCreateCard} stats={sidebarStats} collapsed={sidebarCollapsed} />
                <main className="main-content">
                    <Suspense fallback={<LoadingScreen />}>
                        <Routes>
                            <Route path="/" element={<HallPage />} />
                            <Route path="/hall" element={<HallPage />} />
                            <Route path="/techniques" element={<TechniqueListPage />} />
                            <Route path="/topic/:algorithmType" element={<TopicDetailPage />} />
                            <Route path="/workshop" element={<Navigate to="/" replace />} />
                            <Route path="/review" element={<Navigate to="/" replace />} />
                            <Route path="/card/:type/:id" element={<CardDetailView />} />
                            <Route path="/study/:cardId" element={<StudyRedirect />} />
                            <Route path="*" element={<NotFound />} />
                        </Routes>
                    </Suspense>
                </main>
            </div>
            <StatusBar />
            <ToastContainer />
        </div>
    )
}

function App() {
    return (
        <BrowserRouter>
            <AppContent />
        </BrowserRouter>
    )
}

export default App
