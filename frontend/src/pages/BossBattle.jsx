import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBossStore } from '../stores/bossStore'
import { useCardStore } from '../stores/cardStore'
import LoadingScreen from '../components/ui/Loading/LoadingScreen'
import { showToast } from '../components/ui/Toast/index'
import BossPageHeader from '../components/boss/BossPageHeader'
import BossLayout from '../components/boss/BossLayout'
import BossList from '../components/boss/BossList'
import BossRightPanel from '../components/boss/BossRightPanel'
import BossDetailPanel from '../components/boss/BossDetailPanel'
import CardSelector from '../components/boss/CardSelector'
import QuestionRenderer from '../components/boss/QuestionRenderer'
import BattleResultModal from '../components/boss/BattleResultModal'
import RecoveryDialog from '../components/boss/RecoveryDialog'
import NoCardDisabledState from '../components/boss/NoCardDisabledState'
import styles from './BossBattle.module.css'

export default function BossBattle() {
  const navigate = useNavigate()
  const [showRecovery, setShowRecovery] = useState(false)

  const bosses = useBossStore((s) => s.bosses)
  const selectedBoss = useBossStore((s) => s.selectedBoss)
  const hasAnyCard = useBossStore((s) => s.hasAnyCard)
  const weaknessCards = useBossStore((s) => s.weaknessCards)
  const otherCards = useBossStore((s) => s.otherCards)
  const hasWeaknessCard = useBossStore((s) => s.hasWeaknessCard)
  const battlePhase = useBossStore((s) => s.battlePhase)
  const currentQuestion = useBossStore((s) => s.currentQuestion)
  const selectedCardId = useBossStore((s) => s.selectedCardId)
  const battleResult = useBossStore((s) => s.battleResult)
  const loading = useBossStore((s) => s.loading)
  const error = useBossStore((s) => s.error)

  const fetchBosses = useBossStore((s) => s.fetchBosses)
  const selectBoss = useBossStore((s) => s.selectBoss)
  const startChallenge = useBossStore((s) => s.startChallenge)
  const submitAnswer = useBossStore((s) => s.submitAnswer)
  const resetBattle = useBossStore((s) => s.resetBattle)
  const resetBoss = useBossStore((s) => s.resetBoss)
  const saveBattleToLocalStorage = useBossStore((s) => s.saveBattleToLocalStorage)
  const restoreBattleFromLocalStorage = useBossStore((s) => s.restoreBattleFromLocalStorage)
  const clearBattleLocalStorage = useBossStore((s) => s.clearBattleLocalStorage)

  const cards = useCardStore((s) => s.cards)
  const fetchCards = useCardStore((s) => s.fetchCards)

  const cardCount = cards.filter((c) => c.status !== 'pending_retake').length

  useEffect(() => {
    fetchBosses()
    fetchCards()
  }, [fetchBosses, fetchCards])

  useEffect(() => {
    const hasRestored = restoreBattleFromLocalStorage()
    if (hasRestored) {
      setShowRecovery(true)
    }
  }, [restoreBattleFromLocalStorage])

  useEffect(() => {
    const handleBeforeUnload = () => {
      saveBattleToLocalStorage()
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [saveBattleToLocalStorage])

  useEffect(() => {
    if (error) {
      showToast(error, 'error')
    }
  }, [error])

  const handleSelectBoss = useCallback(
    async (boss) => {
      if (selectedBoss?.id === boss.id) return
      await selectBoss(boss)
    },
    [selectedBoss, selectBoss]
  )

  const handleStartChallenge = useCallback(
    async (cardId) => {
      if (!selectedBoss) return
      await startChallenge(selectedBoss.id, cardId)
    },
    [selectedBoss, startChallenge]
  )

  const handleSubmitAnswer = useCallback(
    async (answerData) => {
      if (!selectedBoss || !currentQuestion) return
      const payload = {
        card_id: selectedCardId,
        question_id: currentQuestion.id,
        ...answerData,
      }
      await submitAnswer(selectedBoss.id, payload)
    },
    [selectedBoss, currentQuestion, selectedCardId, submitAnswer]
  )

  const handleGiveUp = useCallback(async () => {
    if (!selectedBoss || !currentQuestion) return
    const payload = {
      card_id: selectedCardId,
      question_id: currentQuestion.id,
      is_solved: false,
    }
    await submitAnswer(selectedBoss.id, payload)
  }, [selectedBoss, currentQuestion, selectedCardId, submitAnswer])

  const handleContinueChallenge = useCallback(async () => {
    if (!selectedBoss) return
    const boss = selectedBoss
    resetBattle()
    await selectBoss(boss)
  }, [selectedBoss, resetBattle, selectBoss])

  const handleGoPractice = useCallback(() => {
    clearBattleLocalStorage()
    resetBoss()
    navigate('/')
  }, [clearBattleLocalStorage, resetBoss, navigate])

  const handleRecover = useCallback(async () => {
    setShowRecovery(false)
    if (selectedBoss) {
      await selectBoss(selectedBoss)
      if (battlePhase === 'answering' || battlePhase === 'submitting') {
        useBossStore.setState({ battlePhase: 'answering' })
      }
    }
  }, [selectedBoss, battlePhase, selectBoss])

  const handleDiscardRecovery = useCallback(() => {
    setShowRecovery(false)
    clearBattleLocalStorage()
    resetBoss()
  }, [clearBattleLocalStorage, resetBoss])

  const handleCloseResult = useCallback(() => {
    if (!battleResult?.is_correct) {
      resetBattle()
    }
  }, [battleResult, resetBattle])

  if (loading && bosses.length === 0) {
    return <LoadingScreen />
  }

  const showNoCard = !hasAnyCard && selectedBoss && !loading
  const isSubmitting = battlePhase === 'submitting' || (battlePhase === 'challenging' && loading)

  return (
    <div className={`${styles.container} page-container`}>
      <BossPageHeader cardCount={cardCount} />

      {showNoCard ? (
        <NoCardDisabledState onGoPractice={handleGoPractice} />
      ) : (
        <BossLayout
          left={
            <BossList
              bosses={bosses}
              selectedBossId={selectedBoss?.id}
              onSelect={handleSelectBoss}
            />
          }
          right={
            <BossRightPanel>
              {battlePhase === 'idle' && !selectedBoss && null}
              {(battlePhase === 'selecting_card' || (battlePhase === 'idle' && selectedBoss)) && (
                <>
                  <BossDetailPanel boss={selectedBoss} />
                  <CardSelector
                    weaknessCards={weaknessCards}
                    otherCards={otherCards}
                    hasWeaknessCard={hasWeaknessCard}
                    selectedCardId={selectedCardId}
                    onSelect={handleStartChallenge}
                    loading={loading}
                  />
                </>
              )}
              {battlePhase === 'challenging' && <LoadingScreen />}
              {(battlePhase === 'answering' || battlePhase === 'submitting') && currentQuestion && (
                <QuestionRenderer
                  question={currentQuestion}
                  onSubmit={handleSubmitAnswer}
                  onGiveUp={handleGiveUp}
                  loading={isSubmitting}
                />
              )}
            </BossRightPanel>
          }
        />
      )}

      <BattleResultModal
        result={battleResult}
        isOpen={battlePhase === 'result'}
        onClose={handleCloseResult}
        onContinue={handleContinueChallenge}
        onGoPractice={handleGoPractice}
      />

      <RecoveryDialog
        isOpen={showRecovery}
        onRecover={handleRecover}
        onDiscard={handleDiscardRecovery}
      />
    </div>
  )
}
