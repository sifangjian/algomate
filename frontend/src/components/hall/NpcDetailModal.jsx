import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHallStore } from '../../stores/hallStore'
import Modal from '../ui/Modal/Modal'
import NpcAvatar from './NpcAvatar'
import SpecialtyTags from './SpecialtyTags'
import Button from '../ui/Button/Button'
import { showToast } from '../ui/Toast/index'
import styles from './NpcDetailModal.module.css'

export default function NpcDetailModal() {
  const { selectedNpc, modalOpen, setModalOpen, fetchNpcDetail } = useHallStore()
  const navigate = useNavigate()
  const [isStarting, setIsStarting] = useState(false)

  useEffect(() => {
    if (selectedNpc?.id && modalOpen) {
      fetchNpcDetail(selectedNpc.id)
    }
  }, [selectedNpc?.id, modalOpen, fetchNpcDetail])

  const handleStartDialogue = async () => {
    if (!selectedNpc) return
    setIsStarting(true)
    try {
      navigate(`/npc/${selectedNpc.id}`)
      setModalOpen(false)
    } catch (err) {
      showToast(`进入对话失败: ${err.message}`, 'error')
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <Modal
      open={modalOpen}
      onClose={() => setModalOpen(false)}
      title={selectedNpc?.name || '导师详情'}
      ariaLabel={selectedNpc ? `${selectedNpc.name}详情` : '导师详情'}
    >
      {selectedNpc && (
        <div className={styles.npcDetail}>
          <div className={styles.detailHeader}>
            <NpcAvatar avatar={selectedNpc.avatar} name={selectedNpc.name} size="large" />
            <div className={styles.detailInfo}>
              <h2 className={styles.detailName}>{selectedNpc.name}</h2>
              <span className={styles.detailTitle}>{selectedNpc.title}</span>
            </div>
          </div>
          {selectedNpc.description && (
            <p className={styles.detailDesc}>{selectedNpc.description}</p>
          )}
          <div className={styles.detailSpecialties}>
            <h4>专长领域</h4>
            <SpecialtyTags specialties={selectedNpc.specialties} />
          </div>
          {selectedNpc.topics && selectedNpc.topics.length > 0 && (
            <div className={styles.detailTopics}>
              <h4>修习话题</h4>
              {selectedNpc.topics.map(topic => (
                <div key={topic.name || topic} className={styles.topicItem}>
                  <span>{topic.name || topic}</span>
                  {topic.has_card && <span className={styles.topicBadge}>已获卡牌</span>}
                </div>
              ))}
            </div>
          )}
          {selectedNpc.card_count > 0 && (
            <div className={styles.detailCardCount}>
              已获 {selectedNpc.card_count} 张卡牌
            </div>
          )}
          <Button
            variant="primary"
            onClick={handleStartDialogue}
            loading={isStarting}
            fullWidth
          >
            开始修习
          </Button>
        </div>
      )}
    </Modal>
  )
}
