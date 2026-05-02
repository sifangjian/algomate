import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import SideNav from './components/layout/SideNav'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import TaskDrawer from './components/ui/TaskDrawer/TaskDrawer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'

const AdventureMap = lazy(() => import('./pages/AdventureMap'))
const NpcDialogue = lazy(() => import('./pages/NpcDialogue'))
const KnowledgeSpring = lazy(() => import('./pages/KnowledgeSpring'))
const BossBattle = lazy(() => import('./pages/BossBattle'))
const CardWorkshop = lazy(() => import('./pages/CardWorkshop'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  const [isMobile, setIsMobile] = React.useState(window.innerWidth <= 768)

  React.useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <BrowserRouter>
      <div className="app-wrapper">
        <Header />
        {isMobile ? <BottomNav /> : <SideNav />}
        <main className="main-content">
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              <Route path="/" element={<AdventureMap />} />
              <Route path="/knowledge-spring" element={<KnowledgeSpring />} />
              <Route path="/npc/:realmId" element={<NpcDialogue />} />
              <Route path="/boss/battle" element={<BossBattle />} />
              <Route path="/boss/:bossId" element={<BossBattle />} />
              <Route path="/workshop" element={<CardWorkshop />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Suspense>
        </main>
        <ToastContainer />
        <TaskDrawer />
      </div>
    </BrowserRouter>
  )
}

export default App
