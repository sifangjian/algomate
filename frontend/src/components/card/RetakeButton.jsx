import { useState, useCallback, useMemo, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { cardService } from '../../services/cardService'
import { useCardStore } from '../../stores/cardStore'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import styles from './RetakeButton.module.css'

function RetakeButton({ card }) {
  const navigate = useNavigate()
  const { setRetakeInfo } = useCardStore()
  const [loading, setLoading] = useState(false)

  const isPendingRetake = card.status === 'pending_retake'

  const handleRetake = useCallback(async () => {
    if (!isPendingRetake) return
    setLoading(true)
    try {
      const result = await cardService.retakeCard(card.id)
      setRetakeInfo(card.id, result.dialogue_id, result.npc_id)
      showToast(`开始重修「${card.name}」`, 'success')
      if (result.npc_id) {
        navigate(`/npc/${result.npc_id}?dialogueId=${result.dialogue_id}`)
      }
    } catch (err) {
      if (err.message?.includes('40003') || err.message?.includes('不是待重修状态')) {
        showToast('该卡牌不在待重修状态', 'warning')
      } else {
        showToast(`重修失败: ${err.message}`, 'error')
      }
    } finally {
      setLoading(false)
    }
  }, [card, isPendingRetake, navigate, setRetakeInfo])

  if (!isPendingRetake) return null

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleRetake}
      loading={loading}
      className={styles.retakeBtn}
    >
      🔄 重修
    </Button>
  )
}

export default memo(RetakeButton)
