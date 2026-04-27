import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { npcService } from '../services/npcService'
import { noteService } from '../services/noteService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './NpcDialogue.module.css'

const MOCK_NPC = {
    id: null,
    name: '引导者艾琳',
    avatar: '🧙‍♀️',
    realmId: 'novice_forest',
    greeting: '欢迎来到新手森林！我是这里的守护者艾琳。算法的世界充满奥秘，你想从哪里开始探索？',
    expertise: ['二分查找', '线性查找', '数组基础'],
    quickQuestions: [
        { id: 'qq_1', text: '什么是二分查找？' },
        { id: 'qq_2', text: '如何实现线性查找？' },
        { id: 'qq_3', text: '数组有哪些基本操作？' },
    ],
}

export default function NpcDialogue() {
    const { realmId } = useParams()
    const navigate = useNavigate()
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    const [npc, setNpc] = useState(MOCK_NPC)
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [noteContent, setNoteContent] = useState('')
    const [sessionId, setSessionId] = useState(null)
    const [showEndDialog, setShowEndDialog] = useState(false)

    useEffect(() => {
        if (!realmId) return
        npcService.getByRealmId(realmId).then((data) => {
            if (data) {
                setNpc(data)
                setMessages([{
                    id: 'greeting',
                    role: 'npc',
                    content: data.greeting || MOCK_NPC.greeting,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                }])
            }
        }).catch(() => {
            setMessages([{
                id: 'greeting',
                role: 'npc',
                content: MOCK_NPC.greeting,
                timestamp: new Date().toISOString(),
                displayed: true,
            }])
        })
    }, [realmId])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = useCallback(async (text) => {
        const msgText = text || inputValue.trim()
        if (!msgText || isLoading) return
        if (!npc.id) {
            showToast('NPC 加载中，请稍后再试', 'warning')
            return
        }

        const userMsg = {
            id: `user_${Date.now()}`,
            role: 'user',
            content: msgText,
            timestamp: new Date().toISOString(),
            displayed: true,
        }

        setMessages((prev) => [...prev, userMsg])
        setInputValue('')
        setIsLoading(true)

        try {
            const response = await npcService.chat(npc.id, msgText, sessionId)
            const newSessionId = response?.dialogue_id || sessionId

            if (newSessionId && newSessionId !== sessionId) {
                setSessionId(newSessionId)
            }

            const replyContent = response?.npc_response || '让我想想...'

            const npcMsg = {
                id: `npc_${Date.now()}`,
                role: 'npc',
                content: typeof replyContent === 'string' ? replyContent : JSON.stringify(replyContent),
                timestamp: new Date().toISOString(),
                displayed: false,
            }

            setMessages((prev) => [...prev, npcMsg])
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    id: `npc_err_${Date.now()}`,
                    role: 'npc',
                    content: `抱歉，我遇到了一些问题：${err.message}。请稍后再试。`,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                },
            ])
        } finally {
            setIsLoading(false)
        }
    }, [inputValue, isLoading, npc.id, sessionId])

    const handleQuickQuestion = useCallback(
        (question) => {
            handleSend(question.text)
        },
        [handleSend]
    )

    const handleSaveNote = useCallback(async () => {
        if (!noteContent.trim()) {
            showToast('请输入笔记内容', 'warning')
            return
        }
        try {
            await noteService.create({
                title: `${npc.name}对话记录 - ${new Date().toLocaleDateString()}`,
                content: noteContent,
                algorithm_type: npc.expertise?.[0] || '其他',
                tags: JSON.stringify(npc.expertise || []),
            })
            showToast('笔记已保存 ✓', 'success')
            setNoteContent('')
        } catch (err) {
            showToast(`保存失败: ${err.message}`, 'error')
        }
    }, [noteContent, npc])

    const handleEndSession = useCallback(() => {
        if (noteContent.trim()) {
            setShowEndDialog(true)
        } else {
            navigate('/')
        }
    }, [noteContent.trim(), navigate])

    const handleConfirmEnd = useCallback(async () => {
        if (noteContent.trim()) {
            await handleSaveNote()
        }
        setShowEndDialog(false)
        setTimeout(() => navigate('/'), 500)
    }, [handleSaveNote, navigate])

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
            }
        },
        [handleSend]
    )

    return (
        <div className={`${styles.container} page-container`}>
            <div className={styles.header}>
                <button className={styles.backBtn} onClick={() => navigate('/')} aria-label="返回地图">
                    ← 返回地图
                </button>
                <div className={styles.npcInfo}>
                    <span className={styles.npcAvatar}>{npc.avatar}</span>
                    <div>
                        <h2 className={styles.npcName}>{npc.name}</h2>
                        <span className={styles.npcRealm}>秘境向导</span>
                    </div>
                </div>
            </div>

            <div className={styles.layout}>
                <section className={styles.chatSection} aria-label="对话区域">
                    <div className={styles.messagesList} role="log" aria-live="polite">
                        {messages.map((msg) =>
                            msg.role === 'npc' ? (
                                <NpcMessage key={msg.id} message={msg} />
                            ) : (
                                <UserMessage key={msg.id} message={msg} />
                            )
                        )}
                        {isLoading && <TypingIndicator />}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className={styles.quickQuestions}>
                        {npc.quickQuestions?.map((q) => (
                            <button
                                key={q.id}
                                className={styles.quickQBtn}
                                onClick={() => handleQuickQuestion(q)}
                            >
                                {q.text}
                            </button>
                        ))}
                    </div>

                    <div className={styles.inputArea}>
                        <textarea
                            ref={inputRef}
                            className={styles.input}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="输入你的问题..."
                            rows={2}
                            disabled={isLoading}
                            aria-label="消息输入框"
                        />
                        <Button
                            variant="accent"
                            size="sm"
                            onClick={() => handleSend()}
                            disabled={!inputValue.trim() || isLoading}
                            loading={isLoading}
                            icon="➤"
                        >
                            发送
                        </Button>
                    </div>

                    <Button variant="ghost" size="sm" fullWidth onClick={handleEndSession} className={styles.endBtn}>
                        🏠 结束学习，返回地图
                    </Button>
                </section>

                <aside className={styles.noteSection} aria-label="笔记区域">
                    <h3 className={styles.noteTitle}>📝 学习笔记</h3>
                    <p className={styles.noteHint}>记录本次对话中的重点内容</p>
                    <textarea
                        className={styles.noteEditor}
                        value={noteContent}
                        onChange={(e) => setNoteContent(e.target.value)}
                        placeholder="在这里写下你的学习笔记..."
                        rows={10}
                        aria-label="笔记编辑器"
                    />
                    <Button
                        variant="primary"
                        size="sm"
                        fullWidth
                        onClick={handleSaveNote}
                        disabled={!noteContent.trim()}
                    >
                        💾 保存笔记
                    </Button>
                </aside>
            </div>

            <ConfirmDialog
                open={showEndDialog}
                onClose={() => setShowEndDialog(false)}
                onConfirm={handleConfirmEnd}
                title="结束学习"
                message="你有未保存的笔记，是否在离开前保存？"
                confirmText="保存并结束"
                cancelText="不保存直接结束"
            />
        </div>
    )
}

function NpcMessage({ message }) {
    const [displayedText, setDisplayedText] = useState('')
    const [isTyping, setIsTyping] = useState(false)
    const [started, setStarted] = useState(false)

    useEffect(() => {
        if (message.displayed || started) return
        setStarted(true)
        setIsTyping(true)
        setDisplayedText('')
        let index = 0
        const timer = setInterval(() => {
            setDisplayedText(message.content.slice(0, index + 1))
            index++
            if (index >= message.content.length) {
                clearInterval(timer)
                setIsTyping(false)
            }
        }, 50)
        return () => clearInterval(timer)
    }, [message])

    const textToShow = message.displayed ? message.content : displayedText

    return (
        <div className={styles.npcMsg}>
            <span className={styles.msgAvatar}>🧙</span>
            <GameCard className={styles.msgBubble}>
                <p className={styles.msgText}>{textToShow}</p>
                {isTyping && <span className={styles.cursor}>|</span>}
            </GameCard>
        </div>
    )
}

function UserMessage({ message }) {
    return (
        <div className={styles.userMsg}>
            <GameCard className={styles.msgBubbleUser}>
                <p className={styles.msgText}>{message.content}</p>
            </GameCard>
            <span className={styles.msgAvatarUser}>🧑</span>
        </div>
    )
}

function TypingIndicator() {
    return (
        <div className={styles.npcMsg}>
            <span className={styles.msgAvatar}>🧙</span>
            <GameCard className={styles.typingBubble}>
                <span className={styles.typingDot} style={{ animationDelay: '0ms' }} />
                <span className={styles.typingDot} style={{ animationDelay: '200ms' }} />
                <span className={styles.typingDot} style={{ animationDelay: '400ms' }} />
            </GameCard>
        </div>
    )
}
