import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { dialogueService } from '../../services/dialogueService'
import { getRealmIdByNpcId } from '../../services/npcService'
import { showToast } from '../ui/Toast/index'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './DialogueHistorySection.module.css'

export default function DialogueHistorySection({ card }) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)

  const loadHistory = useCallback(async () => {
    if (!card?.dialogue_id) return
    setLoading(true)
    try {
      const data = await dialogueService.getHistory(card.dialogue_id)
      setHistory(data.data || data)
    } catch {
      setHistory(null)
    } finally {
      setLoading(false)
    }
  }, [card?.dialogue_id])

  useEffect(() => {
    if (expanded && !history) {
      loadHistory()
    }
  }, [expanded, history, loadHistory])

  if (!card?.dialogue_id) return null

  const handleContinue = async () => {
    if (!history) return
    const realmId = getRealmIdByNpcId(history.npc_id)
    if (!realmId) {
      showToast('无法定位导师所在秘境', 'error')
      return
    }
    navigate(`/npc/${realmId}?dialogueId=${card.dialogue_id}`)
  }

  const handleClear = async () => {
    setClearing(true)
    try {
      await dialogueService.clearMessages(card.dialogue_id)
      setHistory(null)
      setShowClearConfirm(false)
      showToast('修习记录已清空', 'success')
    } catch (err) {
      showToast(`清空失败: ${err.message}`, 'error')
    } finally {
      setClearing(false)
    }
  }

  const msgCount = history?.messages?.length || 0

  return (
    <div className={styles.section}>
      <button
        className={styles.toggleBtn}
        onClick={() => setExpanded(!expanded)}
      >
        <span className={styles.toggleIcon}>{expanded ? '▼' : '▶'}</span>
        <span className={styles.toggleTitle}>💬 修习记录</span>
        {msgCount > 0 && <span className={styles.msgBadge}>{msgCount}条</span>}
      </button>

      {expanded && (
        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>加载中...</div>
          ) : !history || msgCount === 0 ? (
            <div className={styles.empty}>暂无修习记录</div>
          ) : (
            <>
              <div className={styles.timeline}>
                {history.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`${styles.msg} ${msg.role === 'user' ? styles.userMsg : styles.npcMsg}`}
                  >
                    {msg.role === 'assistant' && <span className={styles.avatar}>🧙</span>}
                    <div className={styles.msgBubble}>
                      <div className={styles.msgContent}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                    {msg.role === 'user' && <span className={styles.avatar}>🧑</span>}
                  </div>
                ))}
              </div>

              <div className={styles.actions}>
                <button className={styles.continueBtn} onClick={handleContinue}>
                  继续修习
                </button>
                {!showClearConfirm ? (
                  <button
                    className={styles.clearBtn}
                    onClick={() => setShowClearConfirm(true)}
                  >
                    清空记录
                  </button>
                ) : (
                  <div className={styles.clearConfirm}>
                    <span className={styles.clearConfirmText}>确定清空？</span>
                    <button
                      className={styles.confirmYes}
                      onClick={handleClear}
                      disabled={clearing}
                    >
                      {clearing ? '清空中...' : '确定'}
                    </button>
                    <button
                      className={styles.confirmNo}
                      onClick={() => setShowClearConfirm(false)}
                      disabled={clearing}
                    >
                      取消
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
