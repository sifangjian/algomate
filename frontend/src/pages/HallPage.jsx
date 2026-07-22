import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import AlgorithmMap from '../components/hall/AlgorithmMap'
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
  const { npcs, learningPath, loading, fetchNpcs, fetchStats, fetchAlgorithmInfo } = useHallStore()

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
    fetchAlgorithmInfo()
  }, [fetchNpcs, fetchStats, fetchAlgorithmInfo, navigate])

  return (
    <div className={styles.hallPage}>
      <HallHeader />
      {loading ? (
        <LoadingScreen />
      ) : (
        <AlgorithmMap />
      )}
    </div>
  )
}