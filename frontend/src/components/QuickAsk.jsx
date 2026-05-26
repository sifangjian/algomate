import { useState, useRef, useCallback, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { quickAskService } from '../services/quickAskService'
import styles from './QuickAsk.module.css'

export default function QuickAsk({ npcId, npcName, visible }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const handleSend = useCallback(() => {
    const text = inputValue.trim()
    if (!text || isStreaming || !npcId) return

    setInputValue('')

    const userMsg = { id: `q_user_${Date.now()}`, role: 'user', content: text }
    const npcMsgId = `q_npc_${Date.now()}`
    const npcMsg = { id: npcMsgId, role: 'assistant', content: '', isStreaming: true }

    setMessages((prev) => [...prev, userMsg, npcMsg])
    setIsStreaming(true)

    const history = messages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.content }))

    let accumulated = ''

    const controller = quickAskService.askStream(npcId, npcName, text, history, {
      onChunk: (token) => {
        accumulated += token
        const current = accumulated
        setMessages((prev) =>
          prev.map((m) => (m.id === npcMsgId ? { ...m, content: current } : m))
        )
      },
      onDone: () => {
        setMessages((prev) =>
          prev.map((m) => (m.id === npcMsgId ? { ...m, isStreaming: false } : m))
        )
        setIsStreaming(false)
      },
      onError: (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === npcMsgId
              ? { ...m, content: `出错了：${err.message}`, isStreaming: false }
              : m
          )
        )
        setIsStreaming(false)
      },
    })

    abortRef.current = controller
  }, [inputValue, isStreaming, npcId, npcName, messages])

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleClear = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setMessages([])
    setIsStreaming(false)
  }, [])

  const handleClose = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setIsStreaming(false)
    setIsOpen(false)
  }, [])

  if (!visible) return null

  return (
    <>
      {!isOpen && (
        <button
          className={styles.fab}
          onClick={() => setIsOpen(true)}
          aria-label="打开旁问"
          title="旁问：临时提问，不记录"
        >
          <span className={styles.fabIcon}>💬</span>
          <span className={styles.fabLabel}>旁问</span>
        </button>
      )}

      {isOpen && (
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>💬 旁问</span>
            <div className={styles.panelActions}>
              {messages.length > 0 && (
                <button className={styles.headerBtn} onClick={handleClear} title="清空历史">
                  清空
                </button>
              )}
              <button className={styles.headerBtn} onClick={handleClose} title="关闭">
                ✕
              </button>
            </div>
          </div>

          <div className={styles.messagesList}>
            {messages.length === 0 && (
              <div className={styles.emptyHint}>随便问点什么，回答不会保存也不会影响主对话</div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`${styles.message} ${
                  msg.role === 'user' ? styles.userMsg : styles.assistantMsg
                }`}
              >
                {msg.role === 'assistant' && <span className={styles.msgAvatar}>🧙</span>}
                <div className={styles.msgBubble}>
                  {msg.content ? (
                    <div className={styles.msgContent}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  ) : msg.isStreaming ? (
                    <span className={styles.typingDot}>...</span>
                  ) : null}
                  {msg.isStreaming && msg.content && <span className={styles.cursor}>|</span>}
                </div>
                {msg.role === 'user' && <span className={styles.msgAvatar}>🧑</span>}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className={styles.inputArea}>
            <textarea
              className={styles.input}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="问个小问题..."
              rows={1}
              disabled={isStreaming}
            />
            <button
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
            >
              发送
            </button>
          </div>

          <div className={styles.footerHint}>旁问不记录、不追踪，关闭即消失</div>
        </div>
      )}
    </>
  )
}
