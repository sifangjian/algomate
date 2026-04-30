import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useUserStore } from '../stores/userStore'
import { bossService } from '../services/bossService'
import { cardService } from '../services/cardService'
import GameCard from '../components/ui/Card/GameCard'
import Button from '../components/ui/Button/Button'
import Modal, { ConfirmDialog } from '../components/ui/Modal/Modal'
import { showToast } from '../components/ui/Toast/index'
import styles from './BossBattle.module.css'

const MOCK_BOSS = {
  id: 'boss_slime_king',
  name: '迷雾史莱姆王',
  icon: '🐉',
  realmId: 'mist_swamp',
  difficulty: 2,
  difficultyLabel: '★★☆ 中等',
  weaknesses: ['DFS', 'BFS'],
  quote: '只有用正确的算法才能将它驱逐！',
  reward: {
    expMin: 100,
    expMax: 200,
    durabilityChange: -10,
  },
}

const MOCK_PROBLEM = {
  id: 'prob_001',
  title: '最长连续子数组',
  difficulty: 2,
  description:
    '给定一个整数数组 nums 和一个整数 k，找出该数组中长度为 k 的连续子数组的最大平均值。',
  examples: [
    {
      input: 'nums = [1,12,-5,-6,50,3], k = 4',
      output: '12.75',
      explanation: '最大平均值是 (12-5-6+50)/4 = 51/4 = 12.75',
    },
  ],
  constraints: [
    'n == nums.length',
    '1 <= k <= n <= 10^5',
    '-10^4 <= nums[i] <= 10^4',
  ],
  template: 'def solution(nums, k):\n    # 在这里编写你的代码\n    pass',
  hints: ['考虑使用滑动窗口来优化时间复杂度'],
  timeLimit: '1秒',
  memoryLimit: '256MB',
}

const MOCK_CARDS = [
  { id: 'card_001', name: '双指针', algorithmType: 'Two Pointers', durability: 85, maxDurability: 100, icon: '👆', isUsable: true },
  { id: 'card_002', name: '滑动窗口', algorithmType: 'Sliding Window', durability: 72, maxDurability: 100, icon: '🪟', isUsable: true },
  { id: 'card_003', name: '二分查找', algorithmType: 'Binary Search', durability: 25, maxDurability: 100, icon: '🔍', isUsable: true },
  { id: 'card_004', name: '动态规划', algorithmType: 'DP', durability: 0, maxDurability: 100, icon: '🎯', isUsable: false },
]

export default function BossBattle() {
  const { bossId } = useParams()
  const navigate = useNavigate()
  const { addExperience } = useUserStore()

  const [boss] = useState(MOCK_BOSS)
  const [problem] = useState(MOCK_PROBLEM)
  const [cards, setCards] = useState(MOCK_CARDS)
  const [selectedCardId, setSelectedCardId] = useState(null)
  const [code, setCode] = useState(MOCK_PROBLEM.template)
  const [submissionStatus, setSubmissionStatus] = useState('idle')
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (bossId) {
      bossService.getBoss(bossId).catch(() => {})
      cardService.getAvailable().then((data) => {
        if (Array.isArray(data)) setCards(data)
      }).catch(() => {})
    }
    setCode(MOCK_PROBLEM.template)
  }, [bossId])

  const handleCardSelect = useCallback(
    (card) => {
      if (!card.isUsable) {
        showToast('该卡牌已损坏，无法使用', 'warning')
        return
      }
      setSelectedCardId(card.id === selectedCardId ? null : card.id)
    },
    [selectedCardId]
  )

  const handleSubmit = useCallback(async () => {
    if (!selectedCardId) {
      showToast('请选择一张应战卡牌', 'warning')
      return
    }
    if (!code.trim() || code.trim() === 'pass') {
      showToast('请编写代码', 'warning')
      return
    }

    setSubmissionStatus('submitting')
    setResult(null)

    try {
      const response = await bossService.submitAnswer(boss.id, code, selectedCardId)
      const submissionResult = response || {}

      setSubmissionStatus(submissionResult.success ? 'success' : 'fail')
      setResult(submissionResult)

      if (submissionResult.success && submissionResult.reward?.exp) {
        addExperience(submissionResult.reward.exp)
        showToast(`🎉 挑战成功！获得 ${submissionResult.reward.exp} XP`, 'success')
      } else if (!submissionResult.success) {
        showToast(`❌ 挑战失败: ${submissionResult.errorType || '答案错误'}`, 'error')
      }
    } catch (err) {
      setSubmissionStatus('fail')
      setResult({ errorType: 'System Error', message: err.message })
      showToast(`提交失败: ${err.message}`, 'error')
    }
  }, [selectedCardId, code, boss.id, addExperience])

  const handleRetry = useCallback(() => {
    setSubmissionStatus('idle')
    setResult(null)
  }, [])

  const selectedCard = cards.find((c) => c.id === selectedCardId)

  return (
    <div className={`${styles.container} page-container`}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => navigate('/')} aria-label="返回地图">
          ← 返回地图
        </button>
        <div className={styles.bossHeaderInfo}>
          <span className={styles.bossIcon}>{boss.icon}</span>
          <div>
            <h2 className={styles.bossName}>{boss.name}</h2>
            <span className={styles.difficultyLabel}>{boss.difficultyLabel}</span>
          </div>
        </div>
      </div>

      <p className={styles.quote}>「{boss.quote}」</p>

      <div className={styles.battleLayout}>
        <section className={styles.problemSection} aria-label="试炼区域">
          <GameCard className={styles.problemCard}>
            <h3 className={styles.problemTitle}>{problem.title}</h3>
            <div className={styles.problemMeta}>
              <span>⏱ {problem.timeLimit}</span>
              <span>💾 {problem.memoryLimit}</span>
              <span>难度: {'★'.repeat(problem.difficulty)}{'☆'.repeat(3 - problem.difficulty)}</span>
            </div>
            <pre className={styles.problemDesc}>{problem.description}</pre>

            <div className={styles.examplesSection}>
              <h4>示例</h4>
              {problem.examples.map((ex, i) => (
                <div key={i} className={styles.exampleBlock}>
                  <div><strong>输入:</strong> <code>{ex.input}</code></div>
                  <div><strong>输出:</strong> <code>{ex.output}</code></div>
                  {ex.explanation && <div className={styles.explain}><strong>解释:</strong> {ex.explanation}</div>}
                </div>
              ))}
            </div>

            <div className={styles.constraints}>
              <strong>约束:</strong>
              <ul>{problem.constraints?.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </div>

            {problem.hints?.length > 0 && (
              <div className={styles.hints}>
                <strong>💡 指引:</strong>
                <ul>{problem.hints.map((h, i) => <li key={i}>{h}</li>)}</ul>
              </div>
            )}
          </GameCard>
        </section>

        <section className={styles.actionSection} aria-label="操作区域">
          <div className={styles.cardSelectArea}>
            <h4 className={styles.sectionLabel}>选择应战卡牌</h4>
            <div className={styles.cardGrid}>
              {cards.map((card) => (
                <button
                  key={card.id}
                  className={`${styles.cardBtn} ${
                    selectedCardId === card.id ? styles.selected : ''
                  } ${!card.isUsable ? styles.disabled : ''}`}
                  onClick={() => handleCardSelect(card)}
                  disabled={!card.isUsable}
                  title={card.isUsable ? `使用 ${card.name}` : '卡牌已损坏'}
                >
                  <span className={styles.cardIcon}>{card.icon}</span>
                  <span className={styles.cardName}>{card.name}</span>
                  <div className={styles.cardDurability}>
                    <div
                      className={styles.durFill}
                      style={{
                        width: `${(card.durability / card.maxDurability) * 100}%`,
                        background:
                          card.durability >= 60
                            ? 'var(--color-success)'
                            : card.durability >= 30
                              ? 'var(--color-warning)'
                              : 'var(--color-danger)',
                      }}
                    />
                  </div>
                  <span className={styles.durText}>{card.durability}%</span>
                  {selectedCardId === card.id && <span className={styles.checkMark}>✓</span>}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.codeArea}>
            <h4 className={styles.sectionLabel}>代码编辑器</h4>
            <textarea
              className={styles.codeEditor}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
              rows={14}
              disabled={submissionStatus === 'submitting'}
              aria-label="代码编辑器"
            />
          </div>

          <Button
            variant="danger"
            size="lg"
            fullWidth
            onClick={handleSubmit}
            loading={submissionStatus === 'submitting'}
            disabled={submissionStatus !== 'idle' || !selectedCardId}
            icon='⚔️'
          >
            提交挑战
          </Button>

          {result && (
            <GameCard className={`${styles.resultCard} ${styles[submissionStatus]}`}>
              <div className={styles.resultHeader}>
                <span className={styles.resultIcon}>
                  {submissionStatus === 'success' ? '🎉' : '❌'}
                </span>
                <span className={styles.resultTitle}>
                  {submissionStatus === 'success' ? '挑战成功!' : '挑战失败'}
                </span>
              </div>
              {submissionStatus === 'success' && result.reward && (
                <div className={styles.resultRewards}>
                  <span>+{result.reward.exp || 0} XP</span>
                  {result.reward.durabilityChange != null && (
                    <span className={result.reward.durabilityChange < 0 ? styles.negative : styles.positive}>
                      耐久度 {result.reward.durabilityChange > 0 ? '+' : ''}
                      {result.reward.durabilityChange}
                    </span>
                  )}
                </div>
              )}
              {submissionStatus === 'fail' && (
                <div className={styles.resultError}>
                  <p><strong>错误类型:</strong> {result.errorType || 'Unknown'}</p>
                  {result.passedCases != null && (
                    <p>通过用例: {result.passedCases}/{result.totalCases}</p>
                  )}
                </div>
              )}
              <div className={styles.resultActions}>
                <Button variant="secondary" size="sm" onClick={handleRetry}>
                  {submissionStatus === 'success' ? '再战一次' : '重新挑战'}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
                  返回地图
                </Button>
              </div>
            </GameCard>
          )}
        </section>
      </div>
    </div>
  )
}
