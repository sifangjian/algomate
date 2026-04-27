import styles from './GameCard.module.css'

export default function GameCard({
  children,
  className = '',
  hoverable = true,
  glow = false,
  onClick,
  ...props
}) {
  return (
    <div
      className={`
        ${styles.card}
        ${hoverable ? styles.hoverable : ''}
        ${glow ? styles.glow : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          onClick()
        }
      }}
      {...props}
    >
      {children}
    </div>
  )
}
