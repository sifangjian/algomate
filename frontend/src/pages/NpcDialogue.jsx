import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { npcService, REALM_ID_TO_NAME } from '../services/npcService'
import { useDialogueStore } from '../stores/dialogueStore'
import PostDialogueGuide from '../components/dialogue/PostDialogueGuide'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './NpcDialogue.module.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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
    const [inputValue, setInputValue] = useState('')
    const [noteContent, setNoteContent] = useState('')
    const [showEndDialog, setShowEndDialog] = useState(false)
    const [isNpcLoading, setIsNpcLoading] = useState(true)
    const [algorithmInfo, setAlgorithmInfo] = useState(null)
    const [isEnding, setIsEnding] = useState(false)

    const {
        dialogueId,
        messages,
        isStreaming,
        suggestions,
        earnedCard,
        existingCard,
        status,
        startDialogue,
        sendMessage,
        saveNote,
        endDialogue,
        reset,
    } = useDialogueStore()

    useEffect(() => {
        if (!realmId) return
        setIsNpcLoading(true)
        npcService.getByRealmId(realmId).then(async (data) => {
            if (data && data.id) {
                const mergedNpc = {
                    ...data,
                    quickQuestions: data.quickQuestions || [],
                }
                setNpc(mergedNpc)
                try {
                    await startDialogue(data.id)
                } catch (err) {
                    showToast(`启动修习失败: ${err.message}`, 'error')
                }
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

    useEffect(() => {
        return () => {
            reset()
        }
    }, [])

    const handleRetryNpc = useCallback(() => {
        setNpcError(null)
        setIsNpcLoading(true)
        npcService.getByRealmId(realmId).then(async (data) => {
            if (data && data.id) {
                const mergedNpc = { ...data, quickQuestions: data.quickQuestions || [] }
                setNpc(mergedNpc)
                try {
                    await startDialogue(data.id)
                } catch (err) {
                    showToast(`启动修习失败: ${err.message}`, 'error')
                }
            } else {
                setNpcError('NPC数据格式无效')
            }
        }).catch((err) => {
            setNpcError(err.message || '加载NPC数据失败')
        }).finally(() => setIsNpcLoading(false))
    }, [realmId, startDialogue])

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
        return algorithmInfo.topic_importance[topic.trim()] || null
    }

    const getTopicPrerequisitesDynamic = (topic) => {
        if (!algorithmInfo?.topic_prerequisites) return null
        return algorithmInfo.topic_prerequisites[topic.trim()] || null
    }

    const handleSend = useCallback(async (text) => {
        const msgText = text || inputValue.trim()
        if (!msgText || isStreaming) return
        if (!dialogueId) {
            showToast('修习会话加载中，请稍后再试', 'warning')
            return
        }

        setInputValue('')
        const controller = await sendMessage(msgText)
        if (controller) {
            abortControllerRef.current = controller
        }
    }, [inputValue, isStreaming, dialogueId, sendMessage])

    const handleQuickQuestion = useCallback(
        (question) => {
            const prereqs = getTopicPrerequisitesDynamic(question.text)
            if (prereqs) {
                useDialogueStore.setState((state) => ({
                    messages: [...state.messages, {
                        id: `hint_${Date.now()}`,
                        role: 'npc',
                        content: `💡 建议先修习：${prereqs.join('、')}，再挑战「${question.text}」会更有把握哦！`,
                        timestamp: new Date().toISOString(),
                        displayed: true,
                    }],
                }))
            }
            handleSend(question.text)
        },
        [handleSend]
    )

    const handleSuggestionClick = useCallback(
        (suggestion) => {
            const prereqs = getTopicPrerequisitesDynamic(suggestion)
            if (prereqs) {
                useDialogueStore.setState((state) => ({
                    messages: [...state.messages, {
                        id: `hint_${Date.now()}`,
                        role: 'npc',
                        content: `💡 建议先修习：${prereqs.join('、')}，再挑战「${suggestion}」会更有把握哦！`,
                        timestamp: new Date().toISOString(),
                        displayed: true,
                    }],
                }))
            }
            handleSend(suggestion)
        },
        [handleSend]
    )

    const handleSaveNote = useCallback(async () => {
        if (!noteContent.trim()) {
            showToast('请先输入修炼心得', 'warning')
            return false
        }
        if (!dialogueId) return false
        try {
            await saveNote(noteContent)
            showToast('修炼心得已保存', 'success')
            return true
        } catch (err) {
            showToast(`保存失败: ${err.message}`, 'error')
            return false
        }
    }, [noteContent, dialogueId, saveNote])

    const handleEndSession = useCallback(() => {
        if (noteContent.trim() || messages.length > 1) {
            setShowEndDialog(true)
        } else {
            navigate('/')
        }
    }, [noteContent.trim(), messages.length, navigate])

    const handleConfirmEnd = useCallback(async () => {
        setIsEnding(true)
        try {
            if (noteContent.trim() && dialogueId) {
                await saveNote(noteContent)
            }
            if (dialogueId) {
                const result = await endDialogue()
                if (result?.card) {
                    showToast('修习完成，获得知识卡牌 🎴', 'success')
                } else if (result?.error) {
                    showToast(`卡牌生成失败: ${result.error}`, 'warning')
                }
            }
            setShowEndDialog(false)
        } catch (err) {
            showToast(`结束修习失败: ${err.message}`, 'error')
        } finally {
            setIsEnding(false)
        }
    }, [noteContent, dialogueId, saveNote, endDialogue, navigate])

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
                        <span className={styles.npcAvatar}>{npc?.avatar}</span>
                        <div>
                            <h2 className={styles.npcName}>{npc?.name || '加载中...'}</h2>
                            <span className={styles.npcRealm}>秘境向导</span>
                        </div>
                    </div>
                </div>
                <Button variant="secondary" size="sm" onClick={handleEndSession} icon="🏠" disabled={isEnding}>
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
                            disabled={isStreaming}
                            aria-label="消息输入框"
                        />
                        <Button
                            variant="accent"
                            size="md"
                            onClick={() => handleSend()}
                            disabled={!inputValue.trim() || isStreaming}
                            loading={isStreaming}
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
                        disabled={!noteContent.trim() || !dialogueId}
                    >
                        💾 保存心得
                    </Button>

                    {earnedCard && (
                        <div className={styles.earnedCardSection}>
                            <h4 className={styles.earnedCardTitle}>🎴 获得卡牌</h4>
                            <div className={styles.earnedCardInfo}>
                                <p className={styles.earnedCardName}>{earnedCard.name}</p>
                                {earnedCard.algorithm_category && (
                                    <span className={styles.earnedCardTag}>{earnedCard.algorithm_category}</span>
                                )}
                                {earnedCard.summary && (
                                    <p className={styles.earnedCardContent}>
                                        {earnedCard.summary.length > 120
                                            ? `${earnedCard.summary.slice(0, 120)}...`
                                            : earnedCard.summary}
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    {status === 'ended' && <PostDialogueGuide />}
                </aside>
            </div>
            )}

            <ConfirmDialog
                open={showEndDialog}
                onClose={() => setShowEndDialog(false)}
                onConfirm={handleConfirmEnd}
                onCancel={handleEndWithoutSave}
                title="结束修习"
                message={noteContent.trim() ? "你有未保存的修习内容，是否在离开前保存并转化为卡牌？" : "确定要结束本次修习吗？"}
                confirmText={noteContent.trim() ? "保存并结束" : "结束修习"}
                cancelText="继续修习"
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
                        const badge = getImportanceBadge(null)
                        return (
                            <div key={i} className={styles.topicTagWrapper}>
                                <span className={styles.greetingTopicTag}>
                                    {badge} {topic}
                                </span>
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
    const [viewMode, setViewMode] = useState('rendered')

    const showToggle = !isStreaming && message.id !== 'greeting' && message.content

    return (
        <div className={styles.npcMsg}>
            <span className={styles.msgAvatar}>🧙</span>
            <div className={styles.npcMsgContent}>
                <GameCard className={styles.msgBubble}>
                    <div className={styles.msgBubbleInner}>
                        {message.id === 'greeting' ? (
                            <NpcGreetingMessage text={message.content} />
                        ) : viewMode === 'rendered' ? (
                            <div className={styles.markdownBody}>
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        a: ({ href, children, ...props }) => (
                                            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>{children}</a>
                                        )
                                    }}
                                >{message.content}</ReactMarkdown>
                            </div>
                        ) : (
                            <pre className={styles.rawText}>{message.content}</pre>
                        )}
                        {isStreaming && <span className={styles.cursor}>|</span>}
                    </div>
                </GameCard>
                {showToggle && (
                    <div className={styles.viewToggleBar}>
                        <button
                            className={styles.viewToggleBtn}
                            onClick={() => setViewMode(viewMode === 'rendered' ? 'raw' : 'rendered')}
                            title={viewMode === 'rendered' ? '查看Markdown原文' : '查看渲染视图'}
                            aria-label={viewMode === 'rendered' ? '切换到原文视图' : '切换到渲染视图'}
                        >
                            {viewMode === 'rendered' ? '⟨⟩ 原文' : '✦ 渲染'}
                        </button>
                    </div>
                )}
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
