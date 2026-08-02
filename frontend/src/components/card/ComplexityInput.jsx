import { useState, useRef, useEffect, useCallback } from 'react'
import styles from './CreateCardForm.module.css'

const COMMON_COMPLEXITIES = ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)', 'O(n²)', 'O(2ⁿ)', 'O(n!)']

export default function ComplexityInput({ value, onChange, placeholder = 'O(n)', label }) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [inputValue, setInputValue] = useState(value || '')
  const wrapperRef = useRef(null)

  useEffect(() => {
    setInputValue(value || '')
  }, [value])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = useCallback((e) => {
    const val = e.target.value
    setInputValue(val)
    onChange(val)
    setShowDropdown(true)
  }, [onChange])

  const handleSelect = useCallback((opt) => {
    setInputValue(opt)
    onChange(opt)
    setShowDropdown(false)
  }, [onChange])

  const filtered = COMMON_COMPLEXITIES.filter(c =>
    c.toLowerCase().includes(inputValue.toLowerCase())
  )

  return (
    <div className={styles.complexityWrapper} ref={wrapperRef}>
      <input
        className={styles.formInput}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={() => setShowDropdown(true)}
        placeholder={placeholder}
      />
      {showDropdown && filtered.length > 0 && (
        <div className={styles.complexityDropdown}>
          {filtered.map((opt) => (
            <button
              key={opt}
              type="button"
              className={`${styles.complexityDropdownItem} ${opt === inputValue ? styles.complexityDropdownItemActive : ''}`}
              onClick={() => handleSelect(opt)}
            >
              {opt}
            </button>
          ))}
          {!filtered.includes(inputValue) && inputValue.trim() && (
            <button
              type="button"
              className={styles.complexityDropdownItem}
              onClick={() => handleSelect(inputValue)}
            >
              使用: {inputValue}
            </button>
          )}
        </div>
      )}
    </div>
  )
}