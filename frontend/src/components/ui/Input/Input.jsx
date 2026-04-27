import { forwardRef } from 'react'
import styles from './Input.module.css'

const Input = forwardRef(function Input(
  {
    label,
    error,
    helperText,
    icon,
    type = 'text',
    className = '',
    ...props
  },
  ref
) {
  return (
    <div className={`${styles.wrapper} ${className}`}>
      {label && (
        <label className={styles.label} htmlFor={props.id}>
          {label}
        </label>
      )}
      <div className={styles.inputWrapper}>
        {icon && <span className={styles.inputIcon}>{icon}</span>}
        <input
          ref={ref}
          type={type}
          className={`
            ${styles.input}
            ${error ? styles.inputError : ''}
            ${icon ? styles.withIcon : ''}
          `}
          id={props.id}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined}
          {...props}
        />
      </div>
      {error && (
        <p id={`${props.id}-error`} className={styles.errorText} role="alert">
          {error}
        </p>
      )}
      {!error && helperText && (
        <p id={`${props.id}-helper`} className={styles.helperText}>
          {helperText}
        </p>
      )}
    </div>
  )
})

export default Input
