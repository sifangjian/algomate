import styles from './NpcAvatar.module.css'

const avatarEmojis = {
  laofuzi: '🧓',
  xiangguo: '⚔️',
  zhouxing: '🪐',
  hanbing: '❄️',
  linshui: '🌊',
  fengying: '🌪️',
  yunyuan: '☁️',
  leizhen: '⚡',
  huoqing: '🔥',
  tudun: '🛡️',
  jianxin: '⚔️',
  qifeng: '🗡️',
  yinsuan: '🌙',
  mingcha: '🔮',
  xingchen: '✨',
}

export default function NpcAvatar({ avatar, name, size = 48 }) {
  const displayContent = () => {
    if (!avatar) return '🧙'
    if (avatarEmojis[avatar]) return avatarEmojis[avatar]
    return avatar
  }

  return (
    <div className={styles.avatar} style={{ width: size, height: size }}>
      <span className={styles.avatarText}>{displayContent()}</span>
    </div>
  )
}
