import { useState, useCallback, useRef, useEffect } from 'react'
import styles from './TagSelector.module.css'

export default function TagSelector({ value = [], onChange, placeholder = '选择标签...', options = [] }) {
  const [inputValue, setInputValue] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  const selectedTags = Array.isArray(value) ? value : []

  const filteredOptions = options.filter(
    (opt) =>
      !selectedTags.includes(opt) &&
      opt.toLowerCase().includes(inputValue.toLowerCase())
  )

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = useCallback((e) => {
    setInputValue(e.target.value)
    setIsOpen(true)
  }, [])

  const handleSelect = useCallback((tag) => {
    onChange([...selectedTags, tag])
    setInputValue('')
    setIsOpen(true)
  }, [onChange, selectedTags])

  const handleRemove = useCallback((tag) => {
    onChange(selectedTags.filter((t) => t !== tag))
  }, [onChange, selectedTags])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Backspace' && inputValue === '' && selectedTags.length > 0) {
      handleRemove(selectedTags[selectedTags.length - 1])
    }
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      const exactMatch = options.find(
        (opt) => opt.toLowerCase() === inputValue.trim().toLowerCase()
      )
      if (exactMatch && !selectedTags.includes(exactMatch)) {
        handleSelect(exactMatch)
      } else if (filteredOptions.length > 0) {
        handleSelect(filteredOptions[0])
      }
    }
    if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }, [inputValue, selectedTags, options, filteredOptions, handleRemove, handleSelect])

  return (
    <div className={styles.container} ref={containerRef}>
      <div
        className={styles.inputWrapper}
        onClick={() => setIsOpen(true)}
      >
        {selectedTags.map((tag) => (
          <span key={tag} className={styles.tag}>
            {tag}
            <button
              type="button"
              className={styles.removeBtn}
              onClick={(e) => {
                e.stopPropagation()
                handleRemove(tag)
              }}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          className={styles.input}
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={selectedTags.length === 0 ? placeholder : ''}
        />
      </div>

      {isOpen && filteredOptions.length > 0 && (
        <div className={styles.dropdown}>
          {filteredOptions.map((opt) => (
            <div
              key={opt}
              className={styles.option}
              onClick={() => handleSelect(opt)}
            >
              {opt}
            </div>
          ))}
        </div>
      )}

      {isOpen && inputValue && filteredOptions.length === 0 && (
        <div className={styles.dropdown}>
          <div className={styles.noResult}>未找到匹配的标签</div>
        </div>
      )}
    </div>
  )
}