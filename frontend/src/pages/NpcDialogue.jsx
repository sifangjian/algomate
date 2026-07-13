import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { npcService, REALM_ID_TO_NAME } from '../services/npcService'
import { dialogueService } from '../services/dialogueService'
import { useDialogueStore } from '../stores/dialogueStore'
import { useCardStore } from '../stores/cardStore'
import { cardService } from '../services/cardService'
import PostDialogueGuide from '../components/dialogue/PostDialogueGuide'
import CardEditForm from '../components/card/CardEditForm'
import QuickAsk from '../components/QuickAsk'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './NpcDialogue.module.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const SESSION_KEY = 'algomate_dialogue_session'

function saveDialogueSession(data) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(data))
}

function loadDialogueSession() {
    try {
        const raw = sessionStorage.getItem(SESSION_KEY)
        return raw ? JSON.parse(raw) : null
    } catch {
        return null
    }
}

function clearDialogueSession() {
    sessionStorage.removeItem(SESSION_KEY)
}

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
    const [searchParams] = useSearchParams()
    const urlDialogueId = searchParams.get('dialogueId')
    const messagesEndRef = useRef(null)
    const messagesListRef = useRef(null)
    const inputRef = useRef(null)
    const abortControllerRef = useRef(null)

    const [npc, setNpc] = useState(null)
    const [npcError, setNpcError] = useState(null)
    const [inputValue, setInputValue] = useState('')
    const [showEndConfirm, setShowEndConfirm] = useState(false)
    const [isNpcLoading, setIsNpcLoading] = useState(true)
    const [algorithmInfo, setAlgorithmInfo] = useState(null)
    const [isEnding, setIsEnding] = useState(false)
    const [isNearBottom, setIsNearBottom] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [isSearching, setIsSearching] = useState(false)
    const [showSearchDropdown, setShowSearchDropdown] = useState(false)
    const [asideCard, setAsideCard] = useState(null)
    const searchInputRef = useRef(null)
    const searchDropdownRef = useRef(null)

    const {
        dialogueId,
        messages,
        isStreaming,
        suggestions,
        dialogueCards,
        existingCard,
        status,
        startDialogue,
        sendMessage,
        createCard,
        endDialogue,
        startHeartbeat,
        loadHistory,
        reset,
    } = useDialogueStore()

    const { fetchCards, setSelectedCard, fetchCardDetail, updateCard } = useCardStore()

    useEffect(() => {
        if (!realmId) return
        setIsNpcLoading(true)

        const restoreFromSessionOrUrl = async (npcData) => {
            const saved = loadDialogueSession()
            const targetDialogueId = urlDialogueId || (saved?.realmId === realmId ? saved?.dialogueId : null)

            if (targetDialogueId) {
                try {
                    const historyData = await loadHistory(targetDialogueId)
                    if (historyData?.status === 'ended') {
                        try {
                            await dialogueService.resume(targetDialogueId)
                        } catch {
                            // resume 失败不丢弃已加载的历史
                        }
                    }
                    useDialogueStore.setState({ status: 'active' })
                    saveDialogueSession({ dialogueId: targetDialogueId, npcId: npcData.id, realmId })
                    startHeartbeat()
                    return
                } catch {
                    // loadHistory 本身失败，走新建流程
                    clearDialogueSession()
                }
            }

            await startDialogue(npcData.id)
            saveDialogueSession({ dialogueId: useDialogueStore.getState().dialogueId, npcId: npcData.id, realmId })
        }

        npcService.getByRealmId(realmId).then(async (resp) => {
            const data = resp?.data || resp
            if (data && data.id) {
                const mergedNpc = {
                    ...data,
                    quickQuestions: data.quickQuestions || [],
                }
                setNpc(mergedNpc)
                try {
                    await restoreFromSessionOrUrl(data)
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
        npcService.getByRealmId(realmId).then(async (resp) => {
            const data = resp?.data || resp
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

    const checkNearBottom = useCallback(() => {
        const el = messagesListRef.current
        if (!el) return true
        const threshold = 80
        return el.scrollHeight - el.scrollTop - el.clientHeight < threshold
    }, [])

    useEffect(() => {
        const el = messagesListRef.current
        if (!el) return
        const handleScroll = () => {
            setIsNearBottom(checkNearBottom())
        }
        el.addEventListener('scroll', handleScroll, { passive: true })
        return () => el.removeEventListener('scroll', handleScroll)
    }, [checkNearBottom])

    const prevIsStreamingRef = useRef(false)
    useEffect(() => {
        if (prevIsStreamingRef.current && !isStreaming) {
            setTimeout(() => inputRef.current?.focus(), 0)
        }
        prevIsStreamingRef.current = isStreaming
    }, [isStreaming])

    useEffect(() => {
        if (isNearBottom) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isNearBottom])

    useEffect(() => {
        npcService.getAlgorithmInfo().then((data) => {
            setAlgorithmInfo(data)
        }).catch((err) => {
            console.error('Failed to load algorithm info:', err)
        })
    }, [])

    useEffect(() => {
        fetchCards()
    }, [fetchCards])

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
        inputRef.current?.focus()
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

    const handleEndDialogue = useCallback(async () => {
        setIsEnding(true)
        try {
            if (dialogueId) {
                const result = await endDialogue()
                clearDialogueSession()
                if (result?.abandoned) {
                    showToast('本次修习未创建卡牌，记录已放弃', 'info')
                    navigate('/')
                    return
                }
                if (result?.cards?.length > 0) {
                    showToast(`修习完成，保存了${result.cards.length}张卡牌`, 'success')
                }
            }
            setShowEndConfirm(false)
        } catch (err) {
            showToast(`结束修习失败: ${err.message}`, 'error')
        } finally {
            setIsEnding(false)
        }
    }, [dialogueId, endDialogue, navigate])

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
            }
        },
        [handleSend]
    )


    // 搜索卡牌逻辑
    const performSearch = useCallback(async (query) => {
        const trimmed = query.trim()
        if (!trimmed) {
            setSearchResults([])
            setShowSearchDropdown(false)
            return
        }
        setIsSearching(true)
        try {
            const data = await cardService.getAll({ keyword: trimmed })
            const results = data.cards || []
            setSearchResults(results)
            setShowSearchDropdown(true)
        } catch {
            setSearchResults([])
        } finally {
            setIsSearching(false)
        }
    }, [])

    const searchDebounceRef = useRef(null)
    const handleSearchChange = useCallback((e) => {
        const value = e.target.value
        setSearchQuery(value)
        if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current)
        if (!value.trim()) {
            setSearchResults([])
            setShowSearchDropdown(false)
            return
        }
        searchDebounceRef.current = setTimeout(() => {
            performSearch(value)
        }, 300)
    }, [performSearch])

    const openCardInAside = useCallback(async (card) => {
        const detail = await fetchCardDetail(card.id)
        if (detail) {
            setAsideCard(detail)
            setSelectedCard(detail)
        }
        setSearchQuery('')
        setSearchResults([])
        setShowSearchDropdown(false)
    }, [fetchCardDetail, setSelectedCard])

    const handleSearchSelect = useCallback(async (card) => {
        await openCardInAside(card)
    }, [openCardInAside])

    const handleSearchKeyDown = useCallback(async (e) => {
        if (e.key !== 'Enter' || !searchQuery.trim()) return
        e.preventDefault()

        const trimmed = searchQuery.trim()
        setIsSearching(true)
        try {
            // 精确匹配
            const data = await cardService.getAll({ keyword: trimmed })
            const results = data.cards || []
            const exactMatch = results.find(c => c.name === trimmed)

            if (exactMatch) {
                await openCardInAside(exactMatch)
                showToast(`已打开卡牌「${trimmed}」`, 'success')
            } else {
                // 自动新建卡牌
                try {
                    const newCard = await createCard(trimmed)
                    if (newCard) {
                        await fetchCards()
                        const detail = await fetchCardDetail(newCard.id)
                        if (detail) {
                            setAsideCard(detail)
                            setSelectedCard(detail)
                        }
                        showToast(`新卡牌「${trimmed}」已创建并打开`, 'success')
                    }
                } catch (err) {
                    showToast(`创建卡牌失败: ${err.message}`, 'error')
                }
            }
        } catch {
            showToast('搜索卡牌失败', 'error')
        } finally {
            setIsSearching(false)
            setSearchQuery('')
            setSearchResults([])
            setShowSearchDropdown(false)
        }
    }, [searchQuery, createCard, fetchCards, fetchCardDetail, openCardInAside, setSelectedCard])

    // 点击外部关闭搜索下拉
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (searchDropdownRef.current && !searchDropdownRef.current.contains(e.target) &&
                searchInputRef.current && !searchInputRef.current.contains(e.target)) {
                setShowSearchDropdown(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const handleAsideCardSave = useCallback(async (cardId, payload) => {
        try {
            const updatedCard = await updateCard(cardId, payload)
            setAsideCard(updatedCard)
            setSelectedCard(updatedCard)
            showToast(`卡牌已更新`, 'success')
            return updatedCard
        } catch (err) {
            showToast(`保存失败: ${err.message}`, 'error')
            throw err
        }
    }, [updateCard, setSelectedCard])

    const handleAsideCardClose = useCallback(() => {
        setAsideCard(null)
    }, [])

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
                <Button
                    variant="danger"
                    size="sm"
                    onClick={() => setShowEndConfirm(true)}
                    disabled={!dialogueId || status === 'ended'}
                    loading={isEnding}
                >
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
                        <div className={styles.messagesList} ref={messagesListRef} role="log" aria-live="polite">
                            {messages.map((msg) =>
                                msg.role === 'npc' ? (
                                    <NpcMessage key={msg.id} message={msg} onSuggestionClick={handleSuggestionClick} />
                                ) : (
                                    <UserMessage key={msg.id} message={msg} />
                                )
                            )}
                            <div ref={messagesEndRef} />
                            {!isNearBottom && (
                                <button
                                    className={styles.scrollToBottomBtn}
                                    onClick={() => {
                                        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
                                        setIsNearBottom(true)
                                    }}
                                    aria-label="滚动到底部"
                                >
                                    ↓ 最新消息
                                </button>
                            )}
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

                    <aside className={styles.noteSection} aria-label="卡牌区域">
                        <div className={styles.searchArea}>
                            <div className={styles.searchInputWrapper}>
                                <span className={styles.searchIcon}>🔍</span>
                                <input
                                    ref={searchInputRef}
                                    className={styles.searchInput}
                                    placeholder="搜索或新建卡牌..."
                                    value={searchQuery}
                                    onChange={handleSearchChange}
                                    onKeyDown={handleSearchKeyDown}
                                    onFocus={() => { if (searchResults.length > 0) setShowSearchDropdown(true) }}
                                    aria-label="搜索卡牌"
                                />
                                {isSearching && <span className={styles.searchLoading}>⏳</span>}
                            </div>
                            {showSearchDropdown && searchResults.length > 0 && (
                                <div className={styles.searchDropdown} ref={searchDropdownRef}>
                                    {searchResults.map((card) => (
                                        <button
                                            key={card.id}
                                            className={styles.searchResultItem}
                                            onClick={() => handleSearchSelect(card)}
                                        >
                                            <span className={styles.searchResultIcon}>📜</span>
                                            <span className={styles.searchResultName}>{card.name}</span>
                                            {card.algorithm_type && (
                                                <span className={styles.searchResultType}>{card.algorithm_type}</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}
                            {showSearchDropdown && searchQuery.trim() && searchResults.length === 0 && !isSearching && (
                                <div className={styles.searchDropdown} ref={searchDropdownRef}>
                                    <div className={styles.searchNoResult}>
                                        未找到「{searchQuery.trim()}」，回车新建
                                    </div>
                                </div>
                            )}
                        </div>

                        {asideCard ? (
                            <div className={styles.asideCardEditor}>
                                <div className={styles.asideCardHeader}>
                                    <h3 className={styles.asideCardTitle}>
                                        📜 {asideCard.name}
                                    </h3>
                                    <button
                                        className={styles.asideCardClose}
                                        onClick={handleAsideCardClose}
                                        aria-label="关闭卡牌编辑"
                                    >
                                        ✕
                                    </button>
                                </div>
                                <CardEditForm
                                    card={asideCard}
                                    onSave={() => { }}
                                    onCancel={handleAsideCardClose}
                                />
                            </div>
                        ) : (
                            <div className={styles.asideEmpty}>
                                <span className={styles.asideEmptyIcon}>📜</span>
                                <p className={styles.asideEmptyText}>搜索或新建卡牌后，在此处编辑</p>
                            </div>
                        )}

                        {status === 'ended' && <PostDialogueGuide />}
                    </aside>
                </div>
            )}


            <ConfirmDialog
                open={showEndConfirm}
                onClose={() => setShowEndConfirm(false)}
                onConfirm={handleEndDialogue}
                onCancel={() => setShowEndConfirm(false)}
                title="结束修习"
                message="确定要结束本次修习吗？"
                confirmText="结束修习"
                cancelText="继续修习"
                loading={isEnding}
            />

            <QuickAsk
                npcId={npc?.id}
                npcName={npc?.name}
                visible={!!dialogueId && status === 'active'}
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
    const [isExpanded, setIsExpanded] = useState(true)
    const contentRef = useRef(null)
    const messageRef = useRef(null)

    const showToggle = !isStreaming && message.id !== 'greeting' && message.content
    const contentHeight = useRef(0)

    useEffect(() => {
        if (contentRef.current) {
            contentHeight.current = contentRef.current.scrollHeight
        }
    }, [message.content, isExpanded])

    const handleToggle = useCallback(() => {
        const messagesList = messageRef.current?.closest(`.${styles.messagesList}`)
        if (!messagesList || !messageRef.current) {
            setIsExpanded(!isExpanded)
            return
        }

        const messageTop = messageRef.current.offsetTop
        const scrollTop = messagesList.scrollTop
        const viewportHeight = messagesList.clientHeight
        const messageBottom = messageTop + messageRef.current.offsetHeight
        const isAboveViewport = messageTop < scrollTop
        const isBelowViewport = messageBottom > scrollTop + viewportHeight
        const isPartiallyVisible = !isAboveViewport && !isBelowViewport

        setIsExpanded(!isExpanded)

        if (isPartiallyVisible) {
            requestAnimationFrame(() => {
                const newMessageHeight = messageRef.current.offsetHeight
                const heightDiff = newMessageHeight - (isExpanded ? contentHeight.current : 0)
                messagesList.scrollTo({
                    top: scrollTop + heightDiff * 0.5,
                    behavior: 'smooth'
                })
            })
        }
    }, [isExpanded])

    return (
        <div className={styles.npcMsg} ref={messageRef}>
            <span className={styles.msgAvatar}>🧙</span>
            <div className={styles.npcMsgContent}>
                <GameCard className={styles.msgBubble}>
                    <div className={styles.msgBubbleInner}>
                        {message.id === 'greeting' ? (
                            <NpcGreetingMessage text={message.content} />
                        ) : (
                            <div
                                ref={contentRef}
                                className={`${styles.messageContent} ${isExpanded ? styles.expanded : styles.collapsed}`}
                                style={{ maxHeight: isExpanded ? 'none' : '80px' }}
                            >
                                {viewMode === 'rendered' ? (
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
                            </div>
                        )}
                        {isStreaming && <span className={styles.cursor}>|</span>}
                    </div>
                </GameCard>
                {showToggle && (
                    <div className={styles.messageControls}>
                        <button
                            className={styles.expandToggleBtn}
                            onClick={handleToggle}
                            title={isExpanded ? '收起内容' : '展开内容'}
                            aria-label={isExpanded ? '收起内容' : '展开内容'}
                            aria-expanded={isExpanded}
                        >
                            <span className={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
                            <span className={styles.expandText}>{isExpanded ? '收起' : '展开'}</span>
                        </button>
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
