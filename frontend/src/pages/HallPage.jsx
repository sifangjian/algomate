import { useEffect } from 'react'
import { useHallStore } from '../stores/hallStore'
import HallHeader from '../components/hall/HallHeader'
import LearningPathCard from '../components/hall/LearningPathCard'
import NpcGrid from '../components/hall/NpcGrid'
import NpcDetailModal from '../components/hall/NpcDetailModal'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import styles from './HallPage.module.css'

export default function HallPage() {
  const { npcs, learningPath, stats, filters, loading, fetchNpcs, fetchStats, setFilters } = useHallStore()

  useEffect(() => {
    fetchNpcs()
    fetchStats()
  }, [filters, fetchNpcs, fetchStats])

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
