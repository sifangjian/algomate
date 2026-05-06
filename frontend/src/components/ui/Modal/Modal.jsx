import { useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import Button from '../Button/Button'
import styles from './Modal.module.css'

export default function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnOverlay = true,
  ariaLabel = '对话框',
}) {
  const contentRef = useRef(null)
  const previousFocus = useRef(null)

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Escape' && closeOnOverlay) {
        onClose()
      }
      if (e.key === 'Tab' && contentRef.current) {
        const focusable = contentRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        const first = focusable[0]
        const last = focusable[focusable.length - 1]

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    },
    [onClose, closeOnOverlay]
  )

  useEffect(() => {
    if (open) {
      previousFocus.current = document.activeElement
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
      setTimeout(() => contentRef.current?.focus(), 50)
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
      previousFocus.current?.focus?.()
    }
  }, [open, handleKeyDown])

  if (!open) return null

  return createPortal(
    <div className={styles.overlay} onClick={(e) => {
      if (closeOnOverlay && e.target === e.currentTarget) {
        onClose()
      }
    }} role="presentation">
      <div
        ref={contentRef}
        className={`${styles.modal} ${styles[size]}`}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel}
        tabIndex={-1}
      >
        <div className={styles.header}>
          <h2 className={styles.title}>{title}</h2>
          <button
            className={styles.closeBtn}
            onClick={onClose}
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        <div className={styles.body}>{children}</div>

        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body
  )
}

export function ConfirmDialog({ open, onClose, onConfirm, onCancel, title, message, confirmText = '确认', cancelText = '取消', variant = 'primary', loading = false }) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className={styles.confirmMessage}>{message}</p>
      <div className={styles.confirmActions}>
        <Button variant="ghost" onClick={onCancel || onClose}>
          {cancelText}
        </Button>
        <Button variant={variant} onClick={onConfirm} loading={loading}>
          {confirmText}
        </Button>
      </div>
    </Modal>
  )
}
