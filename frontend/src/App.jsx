import React, { lazy, Suspense, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/layout/Header'
import SideNav from './components/layout/SideNav'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'

const HallPage = lazy(() => import('./pages/HallPage'))
const CardStudyPage = lazy(() => import('./pages/CardStudyPage'))
const ReviewPage = lazy(() => import('./pages/ReviewPage'))
const NotFound = lazy(() => import('./pages/NotFound'))

function AppContent() {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="app-wrapper">
      <Header />
      {isMobile ? <BottomNav /> : <SideNav />}
      <main className="main-content">
        <Suspense fallback={<LoadingScreen />}>
          <Routes>
            <Route path="/" element={<HallPage />} />
            <Route path="/hall" element={<HallPage />} />
            <Route path="/workshop" element={<Navigate to="/" replace />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/study/:cardId" element={<CardStudyPage />} />
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