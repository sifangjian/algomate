import { useEffect, useCallback } from 'react'
import { useUIStore } from '../../../stores/uiStore'
import styles from './ToastContainer.module.css'

const ICON_MAP = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useUIStore()

  return (
    <div className={styles.container} aria-live="polite" aria-label="通知">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>
  )
}

function ToastItem({ toast, onRemove }) {
  const handleRemove = useCallback(() => {
    onRemove(toast.id)
  }, [toast.id, onRemove])

  useEffect(() => {
    if (toast.duration !== Infinity) {
      const timer = setTimeout(handleRemove, toast.duration || 3000)
      return () => clearTimeout(timer)
    }
  }, [toast.duration, handleRemove])

  return (
    <div
      className={`${styles.toast} ${styles[toast.type || 'info']}`}
      role="alert"
    >
      <span className={styles.icon}>{ICON_MAP[toast.type] || ICON_MAP.info}</span>
      <p className={styles.message}>{toast.message}</p>
      {toast.duration !== Infinity && (
        <button
          className={styles.closeBtn}
          onClick={handleRemove}
          aria-label="关闭通知"
        >
          ✕
        </button>
      )}
    </div>
  )
}
