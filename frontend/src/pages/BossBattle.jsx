import { useState, useEffect, useCallback, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useUserStore } from '../stores/userStore'
import { bossService } from '../services/bossService'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import { showToast } from '../components/ui/Toast/index'
import { ConfirmDialog } from '../components/ui/Modal/Modal'
import DurabilityChange from '../components/ui/DurabilityChange/DurabilityChange'
import styles from './BossBattle.module.css'

const DIFFICULTY_CONFIG = {
    easy: { emoji: '🟢', hpDrop: 33, stars: 1, timeLimit: 120 },
    medium: { emoji: '🟡', hpDrop: 50, stars: 2, timeLimit: 120 },
    hard: { emoji: '🔴', hpDrop: 100, stars: 3, timeLimit: 300 },
}

const QUESTION_TYPE_LABELS = {
    '选择题': '选择题',
    '简答题': '简答题',
    'LeetCode挑战': 'LeetCode挑战',
}

function getComboMultiplier(combo) {
    if (combo >= 5) return 2.0
    if (combo >= 3) return 1.5
    if (combo >= 2) return 1.2
    return 1.0
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function getAlgorithmIcon(category) {
    const map = {
        Search: '🔍',
        Sorting: '📊',
        'Dynamic Programming': '🎯',
        Graph: '🕸️',
        Tree: '🌲',
        Recursion: '🔄',
        Array: '📋',
        String: '📝',
        Greedy: '💰',
        Math: '🔢',
    }
    return map[category] || '📜'
}

export default function BossBattle() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const addExperience = useUserStore((s) => s.addExperience)
    const urlCardId = searchParams.get('cardId')
    const [phase, setPhase] = useState(urlCardId ? 'battle' : 'select')
    const [activeCardId, setActiveCardId] = useState(urlCardId)
    const [cards, setCards] = useState([])
    const [cardsLoading, setCardsLoading] = useState(true)
    const [loading, setLoading] = useState(!!urlCardId)
    const [bossData, setBossData] = useState(null)
    const [questionData, setQuestionData] = useState(null)
    const [cardData, setCardData] = useState(null)
    const [bossHP, setBossHP] = useState(100)
    const [combo, setCombo] = useState(0)
    const [attempts, setAttempts] = useState(0)
    const [selectedOption, setSelectedOption] = useState('')
    const [fillAnswer, setFillAnswer] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [battleResult, setBattleResult] = useState(null)
    const [isVictory, setIsVictory] = useState(null)
    const [showCardRef, setShowCardRef] = useState(false)
    const [showHint, setShowHint] = useState(true)
    const [shakeScreen, setShakeScreen] = useState(false)
    const [showFlash, setShowFlash] = useState(false)
    const [showHitText, setShowHitText] = useState(false)
    const [startTime, setStartTime] = useState(null)
    const [elapsedTime, setElapsedTime] = useState(0)
    const [totalExpGained, setTotalExpGained] = useState(0)
    const [speedBonus, setSpeedBonus] = useState(0)
    const [comboBonus, setComboBonus] = useState(0)
    const [showWrongOptions, setShowWrongOptions] = useState(false)
    const [changingQuestion, setChangingQuestion] = useState(false)
    const [showSolvedConfirm, setShowSolvedConfirm] = useState(false)
    const [showGiveUpConfirm, setShowGiveUpConfirm] = useState(false)
    const [durabilityChanges, setDurabilityChanges] = useState([])

    const timerRef = useRef(null)
    const hasLoadedRef = useRef(false)

    useEffect(() => {
        if (urlCardId) {
            if (hasLoadedRef.current) return
            hasLoadedRef.current = true

            const loadBattle = async () => {
                try {
                    setLoading(true)
                    const data = await bossService.generateForCard(urlCardId)
                    setBossData(data.boss)
                    setQuestionData(data.question)
                    setCardData(data.card)
                    setStartTime(Date.now())
                } catch (err) {
                    showToast(err.message || '加载Boss战失败', 'error')
                    navigate('/')
                } finally {
                    setLoading(false)
                }
            }

            loadBattle()
        } else {
            const loadCards = async () => {
                try {
                    setCardsLoading(true)
                    const data = await cardService.getAll()
                    const availableCards = Array.isArray(data) ? data.filter(c => !c.is_sealed) : []
                    setCards(availableCards)
                } catch (err) {
                    showToast(err.message || '加载卡牌失败', 'error')
                } finally {
                    setCardsLoading(false)
                }
            }
            loadCards()
        }
    }, [urlCardId])

    useEffect(() => {
        if (!startTime) return
        timerRef.current = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
        }, 1000)
        return () => clearInterval(timerRef.current)
    }, [startTime])

    const timeLimit = DIFFICULTY_CONFIG[bossData?.difficulty || 'medium']?.timeLimit || 120
    const remainingTime = Math.max(0, timeLimit - elapsedTime)

    useEffect(() => {
        if (remainingTime <= 0 && startTime && isVictory === null) {
            clearInterval(timerRef.current)
            setIsVictory(false)
            setBattleResult({
                feedback: '时间耗尽！Boss战超时失败',
                improvement: '尝试提高答题速度，或选择更低难度的Boss',
            })
        }
    }, [remainingTime, startTime, isVictory])

    useEffect(() => {
        if (showHint) {
            const t = setTimeout(() => setShowHint(false), 3000)
            return () => clearTimeout(t)
        }
    }, [showHint])

    useEffect(() => {
        if (shakeScreen) {
            const t = setTimeout(() => setShakeScreen(false), 400)
            return () => clearTimeout(t)
        }
    }, [shakeScreen])

    useEffect(() => {
        if (showFlash) {
            const t = setTimeout(() => setShowFlash(false), 500)
            return () => clearTimeout(t)
        }
    }, [showFlash])

    useEffect(() => {
        if (showHitText) {
            const t = setTimeout(() => setShowHitText(false), 1000)
            return () => clearTimeout(t)
        }
    }, [showHitText])

    const triggerHitAnimation = useCallback(() => {
        setShakeScreen(true)
        setShowFlash(true)
        setShowHitText(true)
    }, [])

    const handleSelectCard = useCallback(async (selectedId) => {
        try {
            setLoading(true)
            setActiveCardId(String(selectedId))
            const data = await bossService.generateForCard(selectedId)
            setBossData(data.boss)
            setQuestionData(data.question)
            setCardData(data.card)
            setStartTime(Date.now())
            setPhase('battle')
        } catch (err) {
            showToast(err.message || '加载Boss战失败', 'error')
        } finally {
            setLoading(false)
        }
    }, [])

    const handleSubmit = useCallback(async () => {
        if (!bossData || !questionData) return
        if (isSubmitting) return

        const qType = questionData.question_type
        let answerData = {}

        if (qType === '选择题') {
            if (!selectedOption) {
                showToast('请选择一个选项', 'warning')
                return
            }
            answerData = { answer: selectedOption, card_id: parseInt(activeCardId), question_id: questionData.id }
        } else if (qType === '简答题') {
            if (!fillAnswer.trim()) {
                showToast('请输入答案', 'warning')
                return
            }
            answerData = { answer: fillAnswer, card_id: parseInt(activeCardId), question_id: questionData.id }
        } else if (qType === 'LeetCode挑战') {
            answerData = { is_solved: true, card_id: parseInt(activeCardId), question_id: questionData.id }
        }

        setIsSubmitting(true)

        try {
            const result = await bossService.submitAnswer(bossData.id, answerData)

            if (result.is_correct) {
                setShowWrongOptions(false)
                const newCombo = combo + 1
                setCombo(newCombo)

                const difficulty = bossData.difficulty || 'medium'
                const hpDrop = DIFFICULTY_CONFIG[difficulty]?.hpDrop || 50
                const newHP = Math.max(0, bossHP - hpDrop)
                setBossHP(newHP)

                const baseExp = result.reward?.exp || 100
                const multiplier = getComboMultiplier(newCombo)
                const comboBonusVal = Math.round(baseExp * (multiplier - 1))
                setComboBonus((prev) => prev + comboBonusVal)

                const timeLimit = DIFFICULTY_CONFIG[difficulty]?.timeLimit || 120
                const remainingTime = Math.max(0, timeLimit - elapsedTime)
                const speedBonusVal = remainingTime > 0 ? Math.round(baseExp * (remainingTime / timeLimit) * 0.3) : 0
                setSpeedBonus(speedBonusVal)

                const totalExp = baseExp + comboBonusVal + speedBonusVal
                setTotalExpGained((prev) => prev + totalExp)
                addExperience(totalExp)

                if (newHP <= 0) {
                    setIsVictory(true)
                    setBattleResult({
                        ...result,
                        totalExp,
                        speedBonus: speedBonusVal,
                        comboBonus: comboBonusVal,
                    })
                    clearInterval(timerRef.current)
                } else {
                    showToast(`✅ 回答正确！Boss HP -${hpDrop}%`, 'success')
                }
            } else {
                const newAttempts = attempts + 1
                setAttempts(newAttempts)
                setCombo(0)
                setComboBonus(0)
                triggerHitAnimation()

                if (newAttempts >= 3) {
                    setIsVictory(false)
                    setBattleResult({
                        ...result,
                        attempts: newAttempts,
                    })
                    clearInterval(timerRef.current)
                } else {
                    setShowWrongOptions(true)
                    showToast(`❌ 回答错误！剩余机会 ${3 - newAttempts}/3`, 'error')
                }
            }
        } catch (err) {
            showToast(err.message || '提交失败', 'error')
        } finally {
            setIsSubmitting(false)
        }
    }, [bossData, questionData, selectedOption, fillAnswer, combo, attempts, bossHP, elapsedTime, isSubmitting, addExperience, triggerHitAnimation])


    const handleChangeQuestion = useCallback(async () => {
        try {
            setChangingQuestion(true)
            const data = await bossService.generateForCard(activeCardId)
            setBossData(data.boss)
            setQuestionData(data.question)
            setCardData(data.card)
            setSelectedOption('')
            setFillAnswer('')
            setShowWrongOptions(false)
        } catch (err) {
            showToast(err.message || '换题失败', 'error')
        } finally {
            setChangingQuestion(false)
        }
    }, [activeCardId])

    const handleRetryQuestion = useCallback(() => {
        setSelectedOption('')
        setFillAnswer('')
        setShowWrongOptions(false)
    }, [])

    const handleRetry = useCallback(async () => {
        try {
            setLoading(true)
            const data = await bossService.generateForCard(activeCardId)
            setBossData(data.boss)
            setQuestionData(data.question)
            setCardData(data.card)
            setBattleResult(null)
            setIsVictory(null)
            setBossHP(100)
            setCombo(0)
            setAttempts(0)
            setSelectedOption('')
            setFillAnswer('')
            setTotalExpGained(0)
            setSpeedBonus(0)
            setComboBonus(0)
            setShowWrongOptions(false)
            setStartTime(Date.now())
            setElapsedTime(0)
        } catch (err) {
            showToast(err.message || '重新生成题目失败', 'error')
        } finally {
            setLoading(false)
        }
    }, [activeCardId])

    const handleLeetCodeGiveUp = useCallback(async () => {
        if (!bossData || !questionData) return
        if (isSubmitting) return

        setIsSubmitting(true)
        try {
            const result = await bossService.submitAnswer(bossData.id, {
                is_solved: false,
                card_id: parseInt(activeCardId),
                question_id: questionData.id
            })
            setIsVictory(false)
            setBattleResult({
                ...result,
                attempts: 1,
            })
            clearInterval(timerRef.current)
        } catch (err) {
            showToast(err.message || '提交失败', 'error')
        } finally {
            setIsSubmitting(false)
        }
    }, [bossData, questionData, isSubmitting, activeCardId])

    const difficulty = bossData?.difficulty || 'medium'
    const diffConfig = DIFFICULTY_CONFIG[difficulty]
    const hpBarClass = bossHP > 60 ? '' : bossHP > 30 ? styles.yellow : styles.red
    const countdownPercent = timeLimit > 0 ? (remainingTime / timeLimit) * 100 : 0
    const countdownBarClass = countdownPercent <= 20 ? styles.critical : countdownPercent <= 50 ? styles.warning : ''

    if (loading) {
        return (
            <div className={`${styles.container} page-container`}>
                <div className={styles.loadingContainer}>
                    <div className={styles.loadingSpinner} />
                    <div className={styles.loadingText}>正在召唤Boss...</div>
                </div>
            </div>
        )
    }

    if (phase === 'select') {
        return (
            <div className={`${styles.container} page-container`}>
                <button className={styles.backBtn} onClick={() => navigate('/')} aria-label="返回地图">
                    ← 返回地图
                </button>
                <div className={styles.selectPhase}>
                    <h2 className={styles.selectTitle}>选择应战卡牌</h2>
                    {cardsLoading ? (
                        <div className={styles.loadingContainer}>
                            <div className={styles.loadingSpinner} />
                            <div className={styles.loadingText}>加载卡牌中...</div>
                        </div>
                    ) : cards.length === 0 ? (
                        <div className={styles.emptyState}>
                            <span className={styles.emptyIcon}>🎴</span>
                            <p className={styles.emptyText}>需要至少1张卡牌才能挑战Boss</p>
                            <button className={styles.emptyGuideBtn} onClick={() => navigate('/')}>前往修习 →</button>
                        </div>
                    ) : (
                        <div className={styles.selectCardGrid}>
                            {cards.map((card) => (
                                <button
                                    key={card.id}
                                    className={styles.selectCard}
                                    onClick={() => handleSelectCard(card.id)}
                                >
                                    <div className={styles.selectCardHeader}>
                                        <span className={styles.selectCardIcon}>{getAlgorithmIcon(card.algorithmCategory)}</span>
                                        <div className={styles.selectCardInfo}>
                                            <div className={styles.selectCardName}>{card.name}</div>
                                            <div className={styles.selectCardDomain}>{card.algorithmCategory || '未分类'}</div>
                                        </div>
                                    </div>
                                    <div className={styles.selectCardDurability}>
                                        <div className={styles.selectDurBar}>
                                            <div
                                                className={styles.selectDurFill}
                                                style={{
                                                    width: `${(card.durability / card.maxDurability) * 100}%`,
                                                    background: card.durability >= 60
                                                        ? 'linear-gradient(90deg, var(--color-success), #34d399)'
                                                        : card.durability >= 30
                                                            ? 'linear-gradient(90deg, var(--color-warning), #fbbf24)'
                                                            : 'linear-gradient(90deg, var(--color-danger), #f87171)',
                                                }}
                                            />
                                        </div>
                                        <span className={styles.selectDurText}>
                                            耐久 {card.durability}/{card.maxDurability}
                                        </span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        )
    }

    if (!bossData || !questionData) {
        return (
            <div className={`${styles.container} page-container`}>
                <div className={styles.loadingContainer}>
                    <div className={styles.loadingText}>加载失败，请返回重试</div>
                    <Button variant="secondary" onClick={() => navigate('/')}>返回地图</Button>
                </div>
            </div>
        )
    }

    const qType = questionData.question_type

    return (
        <div className={`${styles.container} ${shakeScreen ? styles.shakeScreen : ''} ${combo >= 3 ? styles.comboGlow : ''} page-container`}>
            {showFlash && <div className={styles.flashOverlay} />}
            {showHitText && <div className={styles.hitText}>受到攻击!</div>}

            {combo >= 2 && (
                <div className={styles.comboDisplay} key={combo}>
                    <span className={styles.comboText}>{combo}连击!</span>
                    <span className={styles.comboMultiplier}>x{getComboMultiplier(combo)}</span>
                </div>
            )}

            <div className={styles.header}>
                <button className={styles.backBtn} onClick={() => navigate('/')} aria-label="返回地图">
                    ← 返回地图
                </button>
                <div className={styles.bossInfoBar}>
                    <span className={`${styles.bossIcon} ${styles[difficulty]}`}>
                        {diffConfig.emoji}
                    </span>
                    <div className={styles.bossDetails}>
                        <div className={styles.bossName}>{bossData.name}</div>
                        <div className={styles.bossMeta}>
                            <span className={styles.difficultyStars}>
                                {'★'.repeat(diffConfig.stars)}{'☆'.repeat(3 - diffConfig.stars)}
                            </span>
                        </div>
                    </div>
                </div>
                <div className={styles.hpBarContainer}>
                    <div className={styles.hpBarLabel}>
                        <span>HP</span>
                        <span>{bossHP}%</span>
                    </div>
                    <div className={styles.hpBar}>
                        <div
                            className={`${styles.hpBarFill} ${hpBarClass}`}
                            style={{ width: `${bossHP}%` }}
                        />
                    </div>
                </div>
                <div className={styles.timerContainer}>
                    <div className={`${styles.timer} ${countdownPercent <= 20 ? styles.critical : countdownPercent <= 50 ? styles.warning : ''}`}>
                        {formatTime(remainingTime)}
                    </div>
                    <div className={styles.countdownBar}>
                        <div
                            className={`${styles.countdownBarFill} ${countdownBarClass}`}
                            style={{ width: `${countdownPercent}%` }}
                        />
                    </div>
                </div>
            </div>

            <div className={styles.battleLayout}>
                <div className={styles.leftPanel}>
                    <div className={styles.questionCard}>
                        <span className={`${styles.questionType} ${styles[qType === '选择题' ? 'choice' : qType === '简答题' ? 'fill' : 'leetcode']}`}>
                            {QUESTION_TYPE_LABELS[qType] || qType}
                        </span>
                        <div className={styles.questionContent}>
                            {questionData.content}
                        </div>
                    </div>

                    <div className={`${styles.cardRefSection} ${showCardRef ? styles.mobileOpen : ''}`}>
                        <button
                            className={styles.cardRefToggle}
                            onClick={() => setShowCardRef(!showCardRef)}
                        >
                            <span>🎴 查看卡牌</span>
                            <span className={`${styles.cardRefToggleIcon} ${showCardRef ? styles.expanded : ''}`}>
                                ▶
                            </span>
                        </button>
                        {showCardRef && cardData && (
                            <div className={styles.cardRefPanel}>
                                <div className={styles.cardRefName}>{cardData.name}</div>
                                {cardData.knowledge_content && (
                                    <div className={styles.cardRefContent}>
                                        {cardData.knowledge_content}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                <div className={styles.rightPanel}>
                    {qType === '选择题' && (
                        <>
                            <div className={styles.optionsGrid}>
                                {(Array.isArray(questionData.options)
                                    ? questionData.options
                                    : Object.keys(questionData.options || {}).sort().map(k => questionData.options[k])
                                ).map((option, i) => {
                                    const label = String.fromCharCode(65 + i)
                                    return (
                                        <button
                                            key={i}
                                            className={`${styles.optionCard} ${selectedOption === label ? styles.selected : ''}`}
                                            onClick={() => setSelectedOption(label)}
                                        >
                                            <span className={styles.optionLabel}>{label}</span>
                                            <span className={styles.optionText}>{option}</span>
                                        </button>
                                    )
                                })}
                            </div>
                            <div className={styles.submitArea}>
                                {showWrongOptions ? (
                                    <div className={styles.wrongOptions}>
                                        <div className={styles.wrongOptionsTitle}>回答错误，请选择下一步</div>
                                        <div className={styles.wrongOptionsBtns}>
                                            <Button
                                                variant="secondary"
                                                size="lg"
                                                onClick={handleChangeQuestion}
                                                loading={changingQuestion}
                                                disabled={changingQuestion}
                                                icon="🔄"
                                            >
                                                换一题
                                            </Button>
                                            <Button
                                                variant="danger"
                                                size="lg"
                                                onClick={handleRetryQuestion}
                                                disabled={changingQuestion}
                                                icon="🔁"
                                            >
                                                重试
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <Button
                                        variant="danger"
                                        size="lg"
                                        fullWidth
                                        onClick={handleSubmit}
                                        loading={isSubmitting}
                                        disabled={!selectedOption || isSubmitting}
                                        icon="⚔️"
                                    >
                                        提交挑战
                                    </Button>
                                )}
                            </div>
                        </>
                    )}

                    {qType === '简答题' && (
                        <>
                            <textarea
                                className={styles.fillTextarea}
                                value={fillAnswer}
                                onChange={(e) => setFillAnswer(e.target.value)}
                                placeholder="请输入你的答案..."
                                disabled={isSubmitting}
                            />
                            <div className={styles.submitArea}>
                                {showWrongOptions ? (
                                    <div className={styles.wrongOptions}>
                                        <div className={styles.wrongOptionsTitle}>回答错误，请选择下一步</div>
                                        <div className={styles.wrongOptionsBtns}>
                                            <Button
                                                variant="secondary"
                                                size="lg"
                                                onClick={handleChangeQuestion}
                                                loading={changingQuestion}
                                                disabled={changingQuestion}
                                                icon="🔄"
                                            >
                                                换一题
                                            </Button>
                                            <Button
                                                variant="danger"
                                                size="lg"
                                                onClick={handleRetryQuestion}
                                                disabled={changingQuestion}
                                                icon="🔁"
                                            >
                                                重试
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <Button
                                        variant="danger"
                                        size="lg"
                                        fullWidth
                                        onClick={handleSubmit}
                                        loading={isSubmitting}
                                        disabled={!fillAnswer.trim() || isSubmitting}
                                        icon="⚔️"
                                    >
                                        提交挑战
                                    </Button>
                                )}
                            </div>
                        </>
                    )}

                    {qType === 'LeetCode挑战' && (
                        <>
                            <div className={styles.leetcodeCard}>
                                <div className={styles.leetcodeHeader}>
                                    <span className={styles.leetcodeIcon}>🔗</span>
                                    <span className={styles.leetcodeTitle}>
                                        {questionData.leetcode_title || 'LeetCode 挑战'}
                                    </span>
                                    {questionData.leetcode_difficulty && (
                                        <span className={`${styles.leetcodeDiff} ${styles[questionData.leetcode_difficulty]}`}>
                                            {questionData.leetcode_difficulty === 'easy' ? '简单' :
                                                questionData.leetcode_difficulty === 'medium' ? '中等' : '困难'}
                                        </span>
                                    )}
                                </div>
                                {questionData.leetcode_description && (
                                    <div className={styles.leetcodeDesc}>
                                        {questionData.leetcode_description}
                                    </div>
                                )}
                                {questionData.leetcode_url && (
                                    <a
                                        className={styles.leetcodeLink}
                                        href={questionData.leetcode_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        前往 LeetCode 解题 →
                                    </a>
                                )}
                            </div>
                            <div className={styles.leetcodeActions}>
                                {showWrongOptions ? (
                                    <div className={styles.wrongOptions}>
                                        <div className={styles.wrongOptionsTitle}>回答错误，请选择下一步</div>
                                        <div className={styles.wrongOptionsBtns}>
                                            <Button
                                                variant="secondary"
                                                size="lg"
                                                onClick={handleChangeQuestion}
                                                loading={changingQuestion}
                                                disabled={changingQuestion}
                                                icon="🔄"
                                            >
                                                换一题
                                            </Button>
                                            <Button
                                                variant="danger"
                                                size="lg"
                                                onClick={handleRetryQuestion}
                                                disabled={changingQuestion}
                                                icon="🔁"
                                            >
                                                重试
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <Button
                                            variant="danger"
                                            size="lg"
                                            fullWidth
                                            onClick={() => setShowSolvedConfirm(true)}
                                            loading={isSubmitting}
                                            disabled={isSubmitting}
                                            icon="✅"
                                        >
                                            我已解决
                                        </Button>
                                        <Button
                                            variant="secondary"
                                            size="lg"
                                            fullWidth
                                            onClick={() => setShowGiveUpConfirm(true)}
                                            loading={isSubmitting}
                                            disabled={isSubmitting}
                                            icon="🏳️"
                                        >
                                            暂时放弃
                                        </Button>
                                    </>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {showHint && !showCardRef && (
                <div className={styles.cardRefHint}>💡 可展开卡牌参考</div>
            )}

            <button
                className={styles.mobileCardRefBtn}
                onClick={() => setShowCardRef(!showCardRef)}
            >
                🎴 {showCardRef ? '收起卡牌' : '查看卡牌'}
            </button>

            {battleResult && isVictory !== null && (
                <div className={styles.resultOverlay} onClick={(e) => e.target === e.currentTarget && null}>
                    <div className={`${styles.resultCard} ${isVictory ? styles.victory : styles.defeat}`}>
                        <div className={styles.resultHeader}>
                            <span className={styles.resultIcon}>
                                {isVictory ? '🏆' : '💀'}
                            </span>
                            <span className={styles.resultTitle}>
                                {isVictory ? '挑战成功!' : '挑战失败'}
                            </span>
                        </div>

                        {isVictory ? (
                            <>
                                <div className={styles.resultStats}>
                                    <div className={styles.resultStatRow}>
                                        <span className={styles.resultStatLabel}>基础经验</span>
                                        <span className={styles.resultStatValue}>
                                            +{battleResult.reward?.exp || 0} XP
                                        </span>
                                    </div>
                                    {battleResult.speedBonus > 0 && (
                                        <div className={styles.resultStatRow}>
                                            <span className={styles.resultStatLabel}>⚡ 速度奖励</span>
                                            <span className={`${styles.resultStatValue} ${styles.positive}`}>
                                                +{battleResult.speedBonus} XP
                                            </span>
                                        </div>
                                    )}
                                    {battleResult.comboBonus > 0 && (
                                        <div className={styles.resultStatRow}>
                                            <span className={styles.resultStatLabel}>🔥 连击奖励</span>
                                            <span className={`${styles.resultStatValue} ${styles.positive}`}>
                                                +{battleResult.comboBonus} XP
                                            </span>
                                        </div>
                                    )}
                                    <div className={styles.resultStatRow}>
                                        <span className={styles.resultStatLabel}>总计经验</span>
                                        <span className={`${styles.resultStatValue} ${styles.positive}`}>
                                            +{battleResult.totalExp} XP
                                        </span>
                                    </div>
                                    {battleResult.reward?.durability_change != null && battleResult.reward.durability_change !== 0 && (
                                        <div className={styles.resultStatRow} style={{ position: 'relative' }}>
                                            <span className={styles.resultStatLabel}>卡牌耐久</span>
                                            <span className={`${styles.resultStatValue} ${battleResult.reward.durability_change < 0 ? styles.negative : styles.positive}`}>
                                                {battleResult.reward.durability_change > 0 ? '+' : ''}
                                                {battleResult.reward.durability_change}
                                            </span>
                                            <DurabilityChange
                                                value={battleResult.reward.durability_change}
                                                onDone={() => setDurabilityChanges([])}
                                            />
                                        </div>
                                    )}
                                    {battleResult.reward?.durability_change != null && battleResult.reward.durability_change === 0 && (
                                        <div className={styles.resultStatRow}>
                                            <span className={styles.resultStatLabel}>卡牌耐久</span>
                                            <span className={styles.resultStatValue}>
                                                0
                                            </span>
                                        </div>
                                    )}
                                </div>
                                {battleResult.new_card_dropped && battleResult.dropped_card && (
                                    <div className={styles.droppedCard}>
                                        <div className={styles.droppedCardTitle}>🎁 掉落新卡牌!</div>
                                        <div className={styles.droppedCardName}>{battleResult.dropped_card.name}</div>
                                        <div className={styles.droppedCardMeta}>
                                            <span className={styles.droppedCardDomain}>
                                                {getAlgorithmIcon(battleResult.dropped_card.domain || battleResult.dropped_card.algorithm_type)}
                                                {' '}
                                                {battleResult.dropped_card.domain || battleResult.dropped_card.algorithm_type || '未分类'}
                                            </span>
                                        </div>
                                        <div className={styles.droppedCardDurability}>
                                            <div className={styles.droppedDurBar}>
                                                <div
                                                    className={styles.droppedDurFill}
                                                    style={{
                                                        width: `${((battleResult.dropped_card.durability || 0) / (battleResult.dropped_card.max_durability || 80)) * 100}%`,
                                                        background: (battleResult.dropped_card.durability || 0) >= 60
                                                            ? 'linear-gradient(90deg, var(--color-success), #34d399)'
                                                            : (battleResult.dropped_card.durability || 0) >= 30
                                                                ? 'linear-gradient(90deg, var(--color-warning), #fbbf24)'
                                                                : 'linear-gradient(90deg, var(--color-danger), #f87171)',
                                                    }}
                                                />
                                            </div>
                                            <span className={styles.droppedDurText}>
                                                耐久 {battleResult.dropped_card.durability || 0}/{battleResult.dropped_card.max_durability || 80}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className={styles.defeatInfo}>
                                <div className={styles.defeatInfoTitle}>错误分析</div>
                                <div className={styles.defeatInfoText}>
                                    {battleResult.feedback || '回答错误，请继续努力！'}
                                </div>
                                {battleResult.improvement && (
                                    <>
                                        <div className={styles.defeatInfoTitle} style={{ marginTop: '10px' }}>改进建议</div>
                                        <div className={styles.defeatInfoText}>{battleResult.improvement}</div>
                                    </>
                                )}
                                {questionData.explanation && (
                                    <>
                                        <div className={styles.defeatInfoTitle} style={{ marginTop: '10px' }}>正确解析</div>
                                        <div className={styles.defeatInfoText}>{questionData.explanation}</div>
                                    </>
                                )}
                            </div>
                        )}

                        <div className={styles.resultActions}>
                            <Button variant="secondary" size="sm" onClick={handleRetry}>
                                {isVictory ? '再战一次' : '重新挑战'}
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
                                返回地图
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            <ConfirmDialog
                open={showSolvedConfirm}
                onClose={() => setShowSolvedConfirm(false)}
                onCancel={() => setShowSolvedConfirm(false)}
                onConfirm={() => {
                    setShowSolvedConfirm(false)
                    handleSubmit()
                }}
                title="确认完成"
                message="确认已在LeetCode完成此题目？"
                confirmText="确认"
                cancelText="取消"
                variant="danger"
            />
            <ConfirmDialog
                open={showGiveUpConfirm}
                onClose={() => setShowGiveUpConfirm(false)}
                onCancel={() => setShowGiveUpConfirm(false)}
                onConfirm={() => {
                    setShowGiveUpConfirm(false)
                    handleLeetCodeGiveUp()
                }}
                title="确认放弃"
                message="确认暂时放弃此挑战？"
                confirmText="确认"
                cancelText="取消"
                variant="secondary"
            />
        </div>
    )
}
