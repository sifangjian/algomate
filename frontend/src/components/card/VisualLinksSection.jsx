import { useMemo, memo } from 'react'
import styles from './VisualLinksSection.module.css'

function VisualLinkItem({ link, index }) {
  return (
    <a
      className={styles.linkItem}
      href={link.url}
      target="_blank"
      rel="noopener noreferrer"
    >
      <span className={styles.linkIcon}>🔗</span>
      <span className={styles.linkTitle}>{link.title || link.url}</span>
      <span className={styles.linkArrow}>↗</span>
    </a>
  )
}

const MemoizedLinkItem = memo(VisualLinkItem)

export default function VisualLinksSection({ visualLinks }) {
  const links = useMemo(() => {
    if (!visualLinks) return []
    if (Array.isArray(visualLinks)) return visualLinks
    try {
      const parsed = JSON.parse(visualLinks)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }, [visualLinks])

  if (links.length === 0) return null

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>🌐 可视化链接</h3>
      <div className={styles.linkList}>
        {links.map((link, index) => (
          <MemoizedLinkItem key={index} link={link} index={index} />
        ))}
      </div>
    </div>
  )
}
