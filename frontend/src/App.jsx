import React, { lazy, Suspense, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import SideNav from './components/layout/SideNav'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import TaskDrawer from './components/ui/TaskDrawer/TaskDrawer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'
import OnboardingController from './components/onboarding/OnboardingController'
import { useSettingsStore } from './stores/settingsStore'

const AdventureMap = lazy(() => import('./pages/AdventureMap'))
const HallPage = lazy(() => import('./pages/HallPage'))
const NpcDialogue = lazy(() => import('./pages/NpcDialogue'))
const KnowledgeSpring = lazy(() => import('./pages/KnowledgeSpring'))
const BossBattle = lazy(() => import('./pages/BossBattle'))
const CardWorkshop = lazy(() => import('./pages/CardWorkshop'))
const DailyReview = lazy(() => import('./pages/DailyReview'))
const Settings = lazy(() => import('./pages/Settings'))
const NotFound = lazy(() => import('./pages/NotFound'))

function AppContent() {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)
  const { fetchSettings } = useSettingsStore()

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

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
            <Route path="/boss" element={<BossBattle />} />
            <Route path="/workshop" element={<CardWorkshop />} />
            <Route path="/daily-review" element={<DailyReview />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <ToastContainer />
      <TaskDrawer />
      <OnboardingController />
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
