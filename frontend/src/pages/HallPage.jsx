import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import AlgorithmMap from '../components/hall/AlgorithmMap'
import CreateCardModal from '../components/card/CreateCardModal'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import styles from './HallPage.module.css'

export default function HallPage() {
  const navigate = useNavigate()
  const { loading, fetchAlgorithmInfo, fetchCardGraph } = useHallStore()

  const [createModalOpen, setCreateModalOpen] = useState(false)

  useEffect(() => {
    fetchAlgorithmInfo()
    fetchCardGraph()
  }, [fetchAlgorithmInfo, fetchCardGraph])

  const handleCreateCard = useCallback(() => {
    setCreateModalOpen(true)
  }, [])

  const handleCardCreated = useCallback((newCard) => {
    setCreateModalOpen(false)
    fetchAlgorithmInfo()
    fetchCardGraph()
    if (newCard?.id) {
      navigate(`/study/${newCard.id}`, { state: { autoEdit: true } })
    }
  }, [fetchAlgorithmInfo, fetchCardGraph, navigate])

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