import { useSettingsStore } from '../../stores/settingsStore'
import WelcomeModal from './WelcomeModal'
import OnboardingSpotlight from './OnboardingSpotlight'
import OnboardingTooltip from './OnboardingTooltip'

export default function OnboardingController() {
  const { onboardingCompleted, onboardingStep, setOnboardingStep, completeOnboarding } = useSettingsStore()

  if (onboardingCompleted || !onboardingStep) return null

  const handleStart = () => {
    setOnboardingStep('select_npc')
  }

  const handleSkip = () => {
    completeOnboarding()
  }

  switch (onboardingStep) {
    case 'welcome':
      return (
        <WelcomeModal
          onStart={handleStart}
          onSkip={handleSkip}
        />
      )
    case 'select_npc':
      return (
        <OnboardingSpotlight
          targetSelector="[data-npc-name='老夫子']"
          tooltip={
            <OnboardingTooltip
              title="选择你的第一位导师"
              description="点击老夫子，开始你的算法修习之旅"
              step={2}
              totalSteps={5}
            />
          }
          onInteract={() => {
            setOnboardingStep('dialogue')
          }}
        />
      )
    case 'dialogue':
      return null
    case 'view_workshop':
      return (
        <OnboardingSpotlight
          targetSelector="[data-card-id]"
          tooltip={
            <OnboardingTooltip
              title="查看你的卡牌"
              description="点击卡牌查看详情，编辑内容维度"
              step={5}
              totalSteps={5}
            />
          }
          onInteract={() => {
            completeOnboarding()
          }}
        />
      )
    case 'complete':
      return null
    default:
      return null
  }
}
