import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import BottomNav from './components/layout/BottomNav'
import ToastContainer from './components/ui/Toast/ToastContainer'
import LoadingScreen from './components/ui/Loading/LoadingScreen'

const AdventureMap = lazy(() => import('./pages/AdventureMap'))
const NpcDialogue = lazy(() => import('./pages/NpcDialogue'))
const BossBattle = lazy(() => import('./pages/BossBattle'))
const CardWorkshop = lazy(() => import('./pages/CardWorkshop'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  return (
    <BrowserRouter>
      <div className="app-wrapper">
        <Header />
        <main className="main-content">
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              <Route path="/" element={<AdventureMap />} />
              <Route path="/npc/:realmId" element={<NpcDialogue />} />
              <Route path="/boss/:bossId" element={<BossBattle />} />
              <Route path="/workshop" element={<CardWorkshop />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Suspense>
        </main>
        <BottomNav />
        <ToastContainer />
      </div>
    </BrowserRouter>
  )
}

export default App
