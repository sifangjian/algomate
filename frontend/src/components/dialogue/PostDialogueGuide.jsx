import GuideCard from '../guide/GuideCard'
import { useGuideStore } from '../../stores/guideStore'

const SCENE = 'after_dialogue'

export default function PostDialogueGuide() {
  const { currentGuide, visible } = useGuideStore()

  if (!visible || !currentGuide) {
    return null
  }

  return <GuideCard guide={currentGuide} scene={SCENE} />
}
