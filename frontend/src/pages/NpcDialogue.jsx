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

function getImportanceBadge(level) {
    if (level === 'core') return '🔴'
    if (level === 'important') return '🟡'
    if (level === 'extension') return '🟢'
    return ''
}

function getImportanceLabel(level) {
    if (level === 'core') return '核心'
    if (level === 'important') return '重要'
    if (level === 'extension') return '拓展'
    return ''
}

export default function NpcDialogue() {
    const { realmId } = useParams()
    const navigate = useNavigate()
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)
    const abortControllerRef = useRef(null)

    const [npc, setNpc] = useState(null)
    const [npcError, setNpcError] = useState(null)
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [noteContent, setNoteContent] = useState('')
    const [sessionId, setSessionId] = useState(null)
    const [showEndDialog, setShowEndDialog] = useState(false)
    const [isNpcLoading, setIsNpcLoading] = useState(true)
    const [activeSuggestions, setActiveSuggestions] = useState([])
    const [showOverwriteDialog, setShowOverwriteDialog] = useState(false)
    const [existingCard, setExistingCard] = useState(null)
    const [pendingCardData, setPendingCardData] = useState(null)
    const [algorithmInfo, setAlgorithmInfo] = useState(null)

    useEffect(() => {
        if (!realmId) return
        setIsNpcLoading(true)
        npcService.getByRealmId(realmId).then((data) => {
            if (data && data.id) {
                const mergedNpc = {
                    ...data,
                    quickQuestions: data.quickQuestions || [],
                }
                setNpc(mergedNpc)
                setMessages([{
                    id: 'greeting',
                    role: 'npc',
                    content: data.greeting || '你好，让我们一起探索算法的奥秘吧！',
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
            setNpcError(err.message || '加载NPC数据失败')
        }).finally(() => setIsNpcLoading(false))
    }, [realmId])

    const handleRetryNpc = useCallback(() => {
        setNpcError(null)
        setIsNpcLoading(true)
        npcService.getByRealmId(realmId).then((data) => {
            if (data && data.id) {
                const mergedNpc = {
                    ...data,
                    quickQuestions: data.quickQuestions || [],
                }
                setNpc(mergedNpc)
                setMessages([{
                    id: 'greeting',
                    role: 'npc',
                    content: data.greeting || '你好，让我们一起探索算法的奥秘吧！',
                    timestamp: new Date().toISOString(),
                    displayed: true,
                }])
            } else {
                setNpcError('NPC数据格式无效')
            }
        }).catch((err) => {
            setNpcError(err.message || '加载NPC数据失败')
        }).finally(() => setIsNpcLoading(false))
    }, [realmId])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        npcService.getAlgorithmInfo().then((data) => {
            setAlgorithmInfo(data)
        }).catch((err) => {
            console.error('Failed to load algorithm info:', err)
        })
    }, [])

    const getTopicImportanceDynamic = (topic) => {
        if (!algorithmInfo?.topic_importance) return null
        const name = topic.trim()
        return algorithmInfo.topic_importance[name] || null
    }

    const getTopicPrerequisitesDynamic = (topic) => {
        if (!algorithmInfo?.topic_prerequisites) return null
        const name = topic.trim()
        return algorithmInfo.topic_prerequisites[name] || null
    }

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

        const npcMsgId = `npc_${Date.now()}`
        const npcMsg = {
            id: npcMsgId,
            role: 'npc',
            content: '',
            timestamp: new Date().toISOString(),
            displayed: true,
            isStreaming: true,
            suggestions: [],
        }

        setMessages((prev) => [...prev, userMsg, npcMsg])
        setInputValue('')
        setIsLoading(true)

        let accumulatedContent = ''

        const controller = npcService.chatStream(npc.id, msgText, sessionId, {
            onChunk: (token) => {
                accumulatedContent += token
                const currentContent = accumulatedContent
                setMessages((prev) => {
                    const updated = [...prev]
                    const idx = updated.findIndex((m) => m.id === npcMsgId)
                    if (idx >= 0) {
                        updated[idx] = { ...updated[idx], content: currentContent }
                    }
                    return updated
                })
            },
            onSuggestions: (suggestions) => {
                setActiveSuggestions(suggestions)
                setMessages((prev) => {
                    const updated = [...prev]
                    const idx = updated.findIndex((m) => m.id === npcMsgId)
                    if (idx >= 0) {
                        updated[idx] = { ...updated[idx], suggestions }
                    }
                    return updated
                })
            },
            onDone: (dialogueId) => {
                if (dialogueId && dialogueId !== sessionId) {
                    setSessionId(dialogueId)
                }
                setMessages((prev) => {
                    const updated = [...prev]
                    const idx = updated.findIndex((m) => m.id === npcMsgId)
                    if (idx >= 0) {
                        updated[idx] = { ...updated[idx], isStreaming: false }
                    }
                    return updated
                })
                setIsLoading(false)
            },
            onError: (err) => {
                console.error('NPC Chat SSE Error:', err)
                setMessages((prev) => {
                    const updated = [...prev]
                    const idx = updated.findIndex((m) => m.id === npcMsgId)
                    if (idx >= 0) {
                        updated[idx] = {
                            ...updated[idx],
                            content: `抱歉，我遇到了一些问题：${err.message}。请稍后再试。`,
                            isStreaming: false,
                        }
                    }
                    return updated
                })
                showToast(`对话失败: ${err.message}`, 'error')
                setIsLoading(false)
            },
        })

        abortControllerRef.current = controller
    }, [inputValue, isLoading, npc.id, sessionId])

    const handleQuickQuestion = useCallback(
        (question) => {
            const prereqs = getTopicPrerequisitesDynamic(question.text)
            if (prereqs) {
                setMessages((prev) => [...prev, {
                    id: `hint_${Date.now()}`,
                    role: 'npc',
                    content: `💡 建议先修习：${prereqs.join('、')}，再挑战「${question.text}」会更有把握哦！`,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                }])
            }
            handleSend(question.text)
        },
        [handleSend]
    )

    const handleSuggestionClick = useCallback(
        (suggestion) => {
            setActiveSuggestions([])
            const prereqs = getTopicPrerequisitesDynamic(suggestion)
            if (prereqs) {
                setMessages((prev) => [...prev, {
                    id: `hint_${Date.now()}`,
                    role: 'npc',
                    content: `💡 建议先修习：${prereqs.join('、')}，再挑战「${suggestion}」会更有把握哦！`,
                    timestamp: new Date().toISOString(),
                    displayed: true,
                }])
            }
            handleSend(suggestion)
        },
        [handleSend]
    )

    const [earnedCard, setEarnedCard] = useState(null)

    const handleSaveNote = useCallback(async () => {
        if (!noteContent.trim()) {
            showToast('请先输入修炼心得', 'warning')
            return false
        }
        try {
            const domainName = npc.location || REALM_ID_TO_NAME[realmId] || realmId
            const algorithmCategory = npc.expertise?.[0] || null

            const algorithmType = npc.expertise?.[0] || algorithmCategory
            if (algorithmType) {
                const existingCards = await cardService.getByAlgorithmTypeField(algorithmType)
                if (existingCards && existingCards.length > 0) {
                    setExistingCard(existingCards[0])
                    setPendingCardData({
                        name: `${algorithmCategory || '算法'}修习记录`,
                        domain: domainName,
                        knowledge_content: noteContent,
                        algorithm_category: algorithmCategory,
                        algorithm_type: algorithmType,
                    })
                    setShowOverwriteDialog(true)
                    return false
                }
            }

            const result = await cardService.createCard({
                name: `${algorithmCategory || '算法'}修习记录`,
                domain: domainName,
                knowledge_content: noteContent,
                algorithm_category: algorithmCategory,
            })
            setEarnedCard(result)
            showToast('知识已转化为卡牌 🎴', 'success')
            setNoteContent('')
            return true
        } catch (err) {
            console.error('Create card error:', err)
            showToast(`保存失败: ${err.message}`, 'error')
            return false
        }
    }, [noteContent, npc, realmId])

    const handleOverwriteCard = useCallback(async () => {
        if (!existingCard || !pendingCardData) return
        try {
            const updatePayload = {
                knowledge_content: pendingCardData.knowledge_content,
                algorithm_category: pendingCardData.algorithm_category,
            }
            if (pendingCardData.algorithm_type) {
                updatePayload.algorithm_type = pendingCardData.algorithm_type
            }
            if (pendingCardData.key_points) {
                updatePayload.key_points = pendingCardData.key_points
            }
            if (pendingCardData.summary) {
                updatePayload.summary = pendingCardData.summary
            }
            const result = await cardService.updateCard(existingCard.id, updatePayload)
            setEarnedCard(result)
            showToast('卡牌已覆盖更新 🎴', 'success')
            setNoteContent('')
            setShowOverwriteDialog(false)
            setExistingCard(null)
            setPendingCardData(null)
        } catch (err) {
            console.error('Overwrite card error:', err)
            showToast(`覆盖更新失败: ${err.message}`, 'error')
        }
    }, [existingCard, pendingCardData])

    const handleKeepOriginal = useCallback(() => {
        setShowOverwriteDialog(false)
        setExistingCard(null)
        setPendingCardData(null)
    }, [])

    const handleEndSession = useCallback(() => {
        if (noteContent.trim()) {
            setShowEndDialog(true)
        } else {
            navigate('/')
        }
    }, [noteContent.trim(), navigate])

    const handleConfirmEnd = useCallback(async () => {
        if (noteContent.trim()) {
            const saved = await handleSaveNote()
            if (!saved) {
                return
            }
        }
        setShowEndDialog(false)
        setTimeout(() => navigate('/'), 500)
    }, [handleSaveNote, navigate])

    const handleEndWithoutSave = useCallback(() => {
        setShowEndDialog(false)
        navigate('/')
    }, [navigate])

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

            {npcError && !npc && (
                <div className={styles.errorContainer}>
                    <p className={styles.errorText}>⚠️ 加载NPC失败：{npcError}</p>
                    <Button variant="primary" size="sm" onClick={handleRetryNpc}>重新加载</Button>
                </div>
            )}

            {npc && (
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
                        <div ref={messagesEndRef} />
                    </div>

                    <div className={styles.quickQuestions}>
                        {npc.quickQuestions?.map((q) => {
                            const importance = getTopicImportanceDynamic(q.text)
                            const badge = getImportanceBadge(importance)
                            return (
                                <button
                                    key={q.id}
                                    className={`${styles.quickQBtn} ${importance ? styles[`quickQ_${importance}`] : ''}`}
                                    onClick={() => handleQuickQuestion(q)}
                                >
                                    {badge} {q.text}
                                </button>
                            )
                        })}
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
            )}

            <ConfirmDialog
                open={showEndDialog}
                onClose={() => setShowEndDialog(false)}
                onConfirm={handleConfirmEnd}
                onCancel={handleEndWithoutSave}
                title="结束修习"
                message="你有未保存的修习内容，是否在离开前转化为卡牌？"
                confirmText="保存并结束"
                cancelText="不保存直接结束"
            />

            <ConfirmDialog
                open={showOverwriteDialog}
                onClose={handleKeepOriginal}
                onConfirm={handleOverwriteCard}
                title="卡牌覆盖确认"
                message={`已存在同类型卡牌「${existingCard?.name || ''}」，是否覆盖更新？`}
                confirmText="覆盖更新"
                cancelText="保留原有"
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
                    {parseTopics(topicsText).map((topic, i) => {
                        const importance = getTopicImportance(topic)
                        const prereqs = getTopicPrerequisites(topic)
                        const badge = getImportanceBadge(importance)
                        return (
                            <div key={i} className={styles.topicTagWrapper}>
                                <span
                                    className={`${styles.greetingTopicTag} ${importance ? styles[`topic_${importance}`] : ''}`}
                                    title={importance ? `${getImportanceLabel(importance)}话题${prereqs ? ` | 建议先修习：${prereqs.join('、')}` : ''}` : ''}
                                >
                                    {badge} {topic}
                                </span>
                                {prereqs && (
                                    <span className={styles.topicPrereqHint}>
                                        建议先修习：{prereqs.join('、')}
                                    </span>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
            {welcomeText && (
                <div className={styles.greetingWelcome}>{welcomeText}</div>
            )}
        </div>
    )
}

function NpcMessage({ message, onSuggestionClick }) {
    const isStreaming = message.isStreaming
    const suggestions = message.suggestions || []
    const showSuggestions = suggestions.length > 0 && !isStreaming

    return (
        <div className={styles.npcMsg}>
            <span className={styles.msgAvatar}>🧙</span>
            <div className={styles.npcMsgContent}>
                <GameCard className={styles.msgBubble}>
                    {message.id === 'greeting' ? (
                        <NpcGreetingMessage text={message.content} />
                    ) : (
                        <p className={styles.msgText}>{message.content}</p>
                    )}
                    {isStreaming && <span className={styles.cursor}>|</span>}
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


