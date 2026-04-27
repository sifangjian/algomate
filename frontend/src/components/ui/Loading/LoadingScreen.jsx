import styles from './LoadingScreen.module.css'

export default function LoadingScreen() {
  return (
    <div className={styles.container} role="status" aria-label="加载中">
      <div className={styles.loader}>
        <div className={styles.orb} />
        <div className={styles.orb} style={{ animationDelay: '0.2s' }} />
        <div className={styles.orb} style={{ animationDelay: '0.4s' }} />
      </div>
      <p className={styles.text}>正在加载算法大陆...</p>
    </div>
  )
}
