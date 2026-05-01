import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { npcService, REALM_ID_TO_NAME } from '../services/npcService'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Input from '../components/ui/Input/Input'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './NpcDialogue.module.css'

const MOCK_NPC = {
    id: 1,
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
    const [isNpcLoading, setIsNpcLoading] = useState(true)
    const [activeSuggestions, setActiveSuggestions] = useState([])

    useEffect(() => {
        if (!realmId) return
        setIsNpcLoading(true)
        npcService.getByRealmId(realmId).then((data) => {
            if (data && data.id) {
                const mergedNpc = {
                    ...data,
                    quickQuestions: data.quickQuestions || MOCK_NPC.quickQuestions,
                }
                setNpc(mergedNpc)
                setMessages([{
                    id: 'greeting',
                    role: 'npc',
                    content: data.greeting || MOCK_NPC.greeting,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                }])
            } else {
                console.error('Invalid NPC data received:', data)
                showToast('NPC数据加载失败', 'error')
            }
        }).catch((err) => {
            console.error('Failed to load NPC:', err)
            showToast(`加载NPC失败: ${err.message}`, 'error')
            setNpc({ ...MOCK_NPC, id: 1 })
            setMessages([{
                id: 'greeting',
                role: 'npc',
                content: MOCK_NPC.greeting,
                timestamp: new Date().toISOString(),
                displayed: true,
            }])
        }).finally(() => setIsNpcLoading(false))
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
            const suggestions = response?.suggestions || []

            const npcMsg = {
                id: `npc_${Date.now()}`,
                role: 'npc',
                content: typeof replyContent === 'string' ? replyContent : JSON.stringify(replyContent),
                timestamp: new Date().toISOString(),
                displayed: false,
                suggestions: suggestions,
            }

            setMessages((prev) => [...prev, npcMsg])
            setActiveSuggestions(suggestions)
        } catch (err) {
            console.error('NPC Chat Error:', err)

            setMessages((prev) => [
                ...prev,
                {
                    id: `npc_err_${Date.now()}`,
                    role: 'npc',
                    content: `抱歉，我遇到了一些问题：${err.message}。请稍后再试或刷新页面。`,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                },
            ])

            showToast(`对话失败: ${err.message}`, 'error')
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

    const handleSuggestionClick = useCallback(
        (suggestion) => {
            setActiveSuggestions([])
            handleSend(suggestion)
        },
        [handleSend]
    )

    const [earnedCard, setEarnedCard] = useState(null)

    const handleSaveNote = useCallback(async () => {
        if (!noteContent.trim()) {
            showToast('请输入心得内容', 'warning')
            return
        }
        try {
            const domainName = npc.location || REALM_ID_TO_NAME[realmId] || realmId
            console.log('Creating card with domain:', domainName, 'npc.location:', npc.location, 'realmId:', realmId)
            const result = await cardService.createCard({
                name: `${npc.expertise?.[0] || '算法'}修习记录`,
                domain: domainName,
                knowledge_content: noteContent,
                algorithm_category: npc.expertise?.[0] || null,
            })
            setEarnedCard(result)
            showToast('知识已转化为卡牌 🎴', 'success')
            setNoteContent('')
        } catch (err) {
            console.error('Create card error:', err)
            showToast(`保存失败: ${err.message}`, 'error')
        }
    }, [noteContent, npc, realmId])

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
                <div className={styles.headerLeft}>
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
                <Button variant="secondary" size="sm" onClick={handleEndSession} icon="🏠">
                    结束修习
                </Button>
            </div>

            <div className={styles.layout}>
                <section className={styles.chatSection} aria-label="对话区域">
                    <div className={styles.messagesList} role="log" aria-live="polite">
                        {messages.map((msg) =>
                            msg.role === 'npc' ? (
                                <NpcMessage key={msg.id} message={msg} onSuggestionClick={handleSuggestionClick} />
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
                            size="md"
                            onClick={() => handleSend()}
                            disabled={!inputValue.trim() || isLoading}
                            loading={isLoading}
                            icon="➤"
                        >
                            发送
                        </Button>
                    </div>


                </section>

                <aside className={styles.noteSection} aria-label="修炼日记区域">
                    <h3 className={styles.noteTitle}>📝 修炼日记</h3>
                    <p className={styles.noteHint}>按模板记录修炼过程，转化为知识卡牌</p>

                    <textarea
                        className={styles.noteEditor}
                        value={noteContent}
                        onChange={(e) => setNoteContent(e.target.value)}
                        placeholder={"📌 今日主题：学习的算法/知识点\n💡 核心理解：用自己的话概括关键思路\n⚠️ 易错难点：踩过的坑或容易混淆的点\n🔑 关键代码：核心代码片段或伪代码\n🧠 个人感悟：总结与反思"}
                        rows={10}
                        aria-label="修炼日记编辑器"
                    />
                    <Button
                        variant="primary"
                        size="sm"
                        fullWidth
                        onClick={handleSaveNote}
                        disabled={!noteContent.trim()}
                    >
                        🎴 转化为卡牌
                    </Button>

                    {earnedCard && (
                        <div className={styles.earnedCardSection}>
                            <h4 className={styles.earnedCardTitle}>🎴 获得卡牌</h4>
                            <div className={styles.earnedCardInfo}>
                                <p className={styles.earnedCardName}>{earnedCard.name}</p>
                                {earnedCard.algorithmCategory && (
                                    <span className={styles.earnedCardTag}>{earnedCard.algorithmCategory}</span>
                                )}
                                {earnedCard.knowledgeContent && (
                                    <p className={styles.earnedCardContent}>
                                        {earnedCard.knowledgeContent.length > 120
                                            ? `${earnedCard.knowledgeContent.slice(0, 120)}...`
                                            : earnedCard.knowledgeContent}
                                    </p>
                                )}
                            </div>
                        </div>
                    )}
                </aside>
            </div>

            <ConfirmDialog
                open={showEndDialog}
                onClose={() => setShowEndDialog(false)}
                onConfirm={handleConfirmEnd}
                title="结束修习"
                message="你有未保存的修习内容，是否在离开前转化为卡牌？"
                confirmText="保存并结束"
                cancelText="不保存直接结束"
            />
        </div>
    )
}

function NpcGreetingMessage({ text }) {
    const lines = text.split('\n')

    let capabilitiesText = ''
    let topicsText = ''
    let welcomeText = ''
    let foundTopics = false

    for (const line of lines) {
        if (!foundTopics && (line.includes('**我是') || line.includes('我可以帮你'))) {
            capabilitiesText += (capabilitiesText ? '\n' : '') + line
        } else if (line.startsWith('📖') || line.includes('可修习话题')) {
            topicsText = line
            foundTopics = true
        } else if (foundTopics) {
            welcomeText += (welcomeText ? '\n' : '') + line
        } else {
            capabilitiesText += (capabilitiesText ? '\n' : '') + line
        }
    }

    const renderCapabilities = (str) => {
        if (!str) return null
        const parts = str.split(/(\*\*[^*]+\*\*)/g)
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i}>{part.slice(2, -2)}</strong>
            }
            return <span key={i}>{part}</span>
        })
    }

    const parseTopics = (str) => {
        if (!str) return []
        const colonIndex = str.indexOf('：')
        if (colonIndex === -1) return [str]
        const topicsStr = str.slice(colonIndex + 1).trim()
        if (!topicsStr) return []
        return topicsStr.split(' · ').filter(Boolean)
    }

    return (
        <div className={styles.greetingContainer}>
            {capabilitiesText && (
                <div className={styles.greetingCapabilities}>{renderCapabilities(capabilitiesText)}</div>
            )}
            {topicsText && parseTopics(topicsText).length > 0 && (
                <div className={styles.greetingTopics}>
                    {parseTopics(topicsText).map((topic, i) => (
                        <span key={i} className={styles.greetingTopicTag}>{topic}</span>
                    ))}
                </div>
            )}
            {welcomeText && (
                <div className={styles.greetingWelcome}>{welcomeText}</div>
            )}
        </div>
    )
}

function NpcMessage({ message, onSuggestionClick }) {
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
    const suggestions = message.suggestions || []
    const showSuggestions = suggestions.length > 0 && !isTyping

    return (
        <div className={styles.npcMsg}>
            <span className={styles.msgAvatar}>🧙</span>
            <div className={styles.npcMsgContent}>
                <GameCard className={styles.msgBubble}>
                    {message.id === 'greeting' ? (
                        <NpcGreetingMessage text={textToShow} />
                    ) : (
                        <p className={styles.msgText}>{textToShow}</p>
                    )}
                    {isTyping && <span className={styles.cursor}>|</span>}
                </GameCard>
                {showSuggestions && (
                    <div className={styles.suggestionsList}>
                        {suggestions.map((s, i) => (
                            <button
                                key={`sug_${i}`}
                                className={styles.suggestionBtn}
                                onClick={() => onSuggestionClick?.(s)}
                            >
                                💡 {s}
                            </button>
                        ))}
                    </div>
                )}
            </div>
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
                <span className={styles.typingText}>AI正在思考中...</span>
            </GameCard>
        </div>
    )
}
