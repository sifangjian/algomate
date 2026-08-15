import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCardStore } from '../../stores/cardStore'
import { showToast } from '../ui/Toast/index'

export default function RetakeButton({ card }) {
  const navigate = useNavigate()
  const store = useCardStore()
  const retakeCard = store?.retakeCard
  const [loading, setLoading] = useState(false)

  if (!card || card.status !== 'pending_retake') {
    return null
  }

  const handleRetake = async () => {
    if (loading) return
    setLoading(true)
    try {
      const result = await retakeCard(card.id)
      showToast('重修成功', 'success')
      navigate(`/npc/npc${card.id}?dialogueId=${result?.dialogue_id || 'd1'}`)
    } catch (err) {
      if (err.message && err.message.includes('40003')) {
        showToast('该卡牌不在待重修状态', 'warning')
      } else {
        showToast(err.message || '重修失败', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleRetake}
      disabled={loading}
      data-loading={loading ? 'true' : 'false'}
    >
      {loading ? '重修中...' : '🔄 重修'}
    </button>
  )
}
