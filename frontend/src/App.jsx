import React, { lazy, Suspense, useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import Header from './components/layout/Header'
import SideNav from './components/layout/SideNav'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import TaskDrawer from './components/ui/TaskDrawer/TaskDrawer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'
import OnboardingGuide from './components/ui/OnboardingGuide/OnboardingGuide'

const AdventureMap = lazy(() => import('./pages/AdventureMap'))
const HallPage = lazy(() => import('./pages/HallPage'))
const NpcDialogue = lazy(() => import('./pages/NpcDialogue'))
const KnowledgeSpring = lazy(() => import('./pages/KnowledgeSpring'))
const BossBattle = lazy(() => import('./pages/BossBattle'))
const CardWorkshop = lazy(() => import('./pages/CardWorkshop'))
const DailyReview = lazy(() => import('./pages/DailyReview'))
const Settings = lazy(() => import('./pages/Settings'))
const NotFound = lazy(() => import('./pages/NotFound'))

const ONBOARDING_KEY = 'algomate_onboarding_completed'

function AppContent() {
  const navigate = useNavigate()
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)
  const [showOnboarding, setShowOnboarding] = useState(false)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_KEY)
    if (!completed) {
      setShowOnboarding(true)
    }
  }, [])

  const handleOnboardingClose = useCallback(() => {
    setShowOnboarding(false)
  }, [])

  const handleOnboardingNavigate = useCallback((path) => {
    navigate(path)
  }, [navigate])

  return (
    <div className="app-wrapper">
      <Header />
      {isMobile ? <BottomNav /> : <SideNav />}
      <main className="main-content">
        <Suspense fallback={<LoadingScreen />}>
          <Routes>
            <Route path="/" element={<HallPage />} />
            <Route path="/adventure" element={<AdventureMap />} />
            <Route path="/knowledge-spring" element={<KnowledgeSpring />} />
            <Route path="/npc/:realmId" element={<NpcDialogue />} />
            <Route path="/boss/battle" element={<BossBattle />} />
            <Route path="/boss/:bossId" element={<BossBattle />} />
            <Route path="/workshop" element={<CardWorkshop />} />
              <Route path="/daily-review" element={<DailyReview />} />
              <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <ToastContainer />
      <TaskDrawer />
      <OnboardingGuide
        open={showOnboarding}
        onClose={handleOnboardingClose}
        onNavigate={handleOnboardingNavigate}
      />
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
