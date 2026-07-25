import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import AlgorithmMap from '../components/hall/AlgorithmMap'
import CreateCardModal from '../components/card/CreateCardModal'
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
  const { loading, fetchNpcs, fetchStats, fetchAlgorithmInfo, fetchCardGraph } = useHallStore()

  const [createModalOpen, setCreateModalOpen] = useState(false)

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
    fetchCardGraph()
  }, [fetchNpcs, fetchStats, fetchAlgorithmInfo, fetchCardGraph, navigate])

  const handleCreateCard = useCallback(() => {
    setCreateModalOpen(true)
  }, [])

  const handleCardCreated = useCallback(() => {
    setCreateModalOpen(false)
    fetchAlgorithmInfo()
    fetchCardGraph()
  }, [fetchAlgorithmInfo, fetchCardGraph])

  return (
    <div className={styles.hallPage}>
      <HallHeader onCreateCard={handleCreateCard} />
      {loading ? <LoadingScreen /> : <AlgorithmMap />}
      <CreateCardModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleCardCreated}
      />
    </div>
  )
}
