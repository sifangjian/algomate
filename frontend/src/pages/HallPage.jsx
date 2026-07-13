import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import LearningPathCard from '../components/hall/LearningPathCard'
import NpcGrid from '../components/hall/NpcGrid'
import NpcDetailModal from '../components/hall/NpcDetailModal'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import styles from './HallPage.module.css'

const DIALOGUE_SESSION_KEY = 'algomate_dialogue_session'

function loadDialogueSession() {
  try {
    const raw = sessionStorage.getItem(DIALOGUE_SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export default function HallPage() {
  const navigate = useNavigate()
  const redirectedRef = useRef(false)
  const { npcs, learningPath, stats, filters, loading, fetchNpcs, fetchStats, setFilters } = useHallStore()

  useEffect(() => {
    if (redirectedRef.current) return
    const session = loadDialogueSession()
    if (session?.realmId && session?.dialogueId) {
      redirectedRef.current = true
      navigate(`/npc/${session.realmId}?dialogueId=${session.dialogueId}`, { replace: true })
      return
    }
    fetchNpcs()
    fetchStats()
  }, [filters, fetchNpcs, fetchStats, navigate])

  const isNewUser = stats?.is_new_user ?? false

  return (
    <div className={styles.hallPage}>
      <HallHeader
        filters={filters}
        onFilterChange={setFilters}
        onReset={useHallStore.getState().resetFilters}
      />
      {learningPath.length > 0 && (
        <LearningPathCard steps={learningPath} />
      )}
      {loading ? (
        <LoadingScreen />
      ) : (
        <NpcGrid npcs={npcs} isNewUser={isNewUser} />
      )}
      <NpcDetailModal />
    </div>
  )
}
