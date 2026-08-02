import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import Header from './components/layout/Header'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'

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
    return (
        <div className="app-wrapper">
            <Header />
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