import styles from './NpcAvatar.module.css'

const AVATAR_MAP = {
  laofuzi: '🧓',
  zhanzhe: '📚',
  zhaodao: '🐸',
  shuzhe: '🌳',
  tuling: '🕸️',
  migong: '🌀',
  tanlan: '👑',
  zhizhe: '🦉',
}

export default function NpcAvatar({ avatar, name, size = 'normal' }) {
  const emoji = AVATAR_MAP[avatar] || avatar || '🧙'
  return (
    <div className={`${styles.npcAvatar} ${styles[size]}`} aria-hidden="true">
      <span className={styles.avatarEmoji}>{emoji}</span>
    </div>
  )
}
