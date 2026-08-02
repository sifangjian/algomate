import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import TopicGrid from '../components/hall/TopicGrid'
import CreateCardModal from '../components/card/CreateCardModal'
import styles from './HallPage.module.css'

export default function HallPage() {
  const navigate = useNavigate()
  const { fetchAlgorithmInfo, fetchTopicOverview } = useHallStore()

  const [createModalOpen, setCreateModalOpen] = useState(false)

  useEffect(() => {
    fetchAlgorithmInfo()
    fetchTopicOverview()
  }, [fetchAlgorithmInfo, fetchTopicOverview])

  const handleCreateCard = useCallback(() => {
    setCreateModalOpen(true)
  }, [])

  const handleCardCreated = useCallback((newCard) => {
    setCreateModalOpen(false)
    fetchAlgorithmInfo()
    fetchTopicOverview()
    if (newCard?.id) {
      // 根据返回数据的结构判断卡片类型
      const cardType = newCard.title ? 'problem' : newCard.problem_id ? 'solution' : 'technique'
      navigate(`/card/${cardType}/${newCard.id}`, { state: { autoEdit: true } })
    }
  }, [fetchAlgorithmInfo, fetchTopicOverview, navigate])

  return (
    <div className={styles.hallPage}>
      <HallHeader onCreateCard={handleCreateCard} />
      <TopicGrid />
      <CreateCardModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleCardCreated}
      />
    </div>
  )
}