import { useUIStore } from '../../../stores/uiStore'

export function showToast(message, type = 'info', duration = 3000) {
  const { addToast } = useUIStore.getState()
  addToast({ message, type, duration })
}
