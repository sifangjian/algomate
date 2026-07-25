import React, { lazy, Suspense, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/layout/Header'
import SideNav from './components/layout/SideNav'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'
import OnboardingController from './components/onboarding/OnboardingController'
import { useSettingsStore } from './stores/settingsStore'

const AdventureMap = lazy(() => import('./pages/AdventureMap'))
const HallPage = lazy(() => import('./pages/HallPage'))
const PracticePage = lazy(() => import('./pages/PracticePage'))
const NpcDialogue = lazy(() => import('./pages/NpcDialogue'))
const BossBattle = lazy(() => import('./pages/BossBattle'))
const CardStudyPage = lazy(() => import('./pages/CardStudyPage'))
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
            <Route path="/hall" element={<HallPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/adventure" element={<AdventureMap />} />
            <Route path="/npc/:realmId" element={<NpcDialogue />} />
            <Route path="/boss/battle" element={<BossBattle />} />
            <Route path="/workshop" element={<Navigate to="/" replace />} />
            <Route path="/study/:cardId" element={<CardStudyPage />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <ToastContainer />
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
