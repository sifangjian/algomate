import React, { lazy, Suspense, useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom'
import TopTabs from './components/layout/TopTabs'
import SideNav from './components/layout/SideNav'
import StatusBar from './components/layout/StatusBar'
import BrandHeader from './components/layout/BrandHeader'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'
import CreateCardModal from './components/card/CreateCardModal'
import { cardService } from './services/cardService'

const HallPage = lazy(() => import('./pages/HallPage'))
const ProblemListPage = lazy(() => import('./pages/ProblemListPage'))
const SolutionListPage = lazy(() => import('./pages/SolutionListPage'))
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
    const [createModalOpen, setCreateModalOpen] = useState(false)

    const toggleSidebar = useCallback(() => {
        setSidebarCollapsed(prev => !prev)
    }, [])

    const navigate = useNavigate()

    const handleCardCreated = useCallback((newCard) => {
        setCreateModalOpen(false)
        if (newCard?.id) {
            const cardType = newCard.title ? 'problem' : newCard.problem_id ? 'solution' : 'technique'
            setTimeout(() => navigate(`/card/${cardType}/${newCard.id}`, { state: { autoEdit: true } }), 100)
        }
    }, [navigate])

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
                    due: reviews?.data?.due_count ?? 0,
                    endangered: reviews?.data?.endangered_count ?? 0,
                    completed: reviews?.data?.completed_count ?? 0,
                    learningDays: progress?.learning_days ?? 0,
                })
            } catch (err) {
                console.error('Failed to fetch sidebar data:', err)
            }
        }
        fetchSidebarData()
        return () => { cancelled = true }
    }, [])

    const handleCreateCard = useCallback(() => {
        setCreateModalOpen(true)
    }, [])

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
                            <Route path="/problems" element={<ProblemListPage />} />
                            <Route path="/solutions" element={<SolutionListPage />} />
                            <Route path="/techniques" element={<TechniqueListPage />} />
                            <Route path="/topic/:algorithmType" element={<TopicDetailPage />} />
                            <Route path="/workshop" element={<Navigate to="/" replace />} />
                            <Route path="/card/:type/:id" element={<CardDetailView />} />
                            <Route path="/study/:cardId" element={<StudyRedirect />} />
                            <Route path="*" element={<NotFound />} />
                        </Routes>
                    </Suspense>
                </main>
            </div>
            <StatusBar />
            <CreateCardModal
                open={createModalOpen}
                onClose={() => setCreateModalOpen(false)}
                onCreated={handleCardCreated}
            />
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
