import { useState, useCallback, memo } from 'react'
import styles from './ExampleEditor.module.css'

function SolutionEditor({ solution, index, onChange, onRemove }) {
  const handleChange = useCallback((field, value) => {
    onChange(index, { ...solution, [field]: value })
  }, [solution, index, onChange])

  return (
    <div className={styles.solutionEditor}>
      <div className={styles.solutionHeader}>
        <input
          className={styles.solutionNameInput}
          value={solution.name || ''}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="解法名称（如：暴力解法、优化解法）"
        />
        <button className={styles.removeBtn} onClick={() => onRemove(index)} title="删除解法">✕</button>
      </div>
      <div className={styles.solutionFields}>
        <div className={styles.fieldRow}>
          <label className={styles.fieldLabel}>复杂度</label>
          <input
            className={styles.complexityInput}
            value={solution.complexity || ''}
            onChange={(e) => handleChange('complexity', e.target.value)}
            placeholder="O(n)"
          />
        </div>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>原理</label>
          <textarea
            className={styles.textarea}
            value={solution.principle || ''}
            onChange={(e) => handleChange('principle', e.target.value)}
            placeholder="解法原理说明..."
            rows={2}
          />
        </div>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>代码</label>
          <textarea
            className={`${styles.textarea} ${styles.codeTextarea}`}
            value={solution.code || ''}
            onChange={(e) => handleChange('code', e.target.value)}
            placeholder="解法代码..."
            rows={4}
          />
        </div>
      </div>
    </div>
  )
}

function ExampleEditor({ example, index, onChange, onRemove }) {
  const handleFieldChange = useCallback((field, value) => {
    onChange(index, { ...example, [field]: value })
  }, [example, index, onChange])

  const handleSolutionChange = useCallback((solIndex, updatedSolution) => {
    const newSolutions = [...(example.solutions || [])]
    newSolutions[solIndex] = updatedSolution
    onChange(index, { ...example, solutions: newSolutions })
  }, [example, index, onChange])

  const handleSolutionRemove = useCallback((solIndex) => {
    const newSolutions = (example.solutions || []).filter((_, i) => i !== solIndex)
    onChange(index, { ...example, solutions: newSolutions })
  }, [example, index, onChange])

  const handleAddSolution = useCallback(() => {
    const newSolutions = [...(example.solutions || []), { name: '', code: '', principle: '', complexity: '' }]
    onChange(index, { ...example, solutions: newSolutions })
  }, [example, index, onChange])

  return (
    <div className={styles.exampleEditor}>
      <div className={styles.exampleHeader}>
        <span className={styles.exampleIndex}>例题 {index + 1}</span>
        <input
          className={styles.titleInput}
          value={example.title || ''}
          onChange={(e) => handleFieldChange('title', e.target.value)}
          placeholder="例题标题"
        />
        <button className={styles.removeBtn} onClick={() => onRemove(index)} title="删除例题">✕</button>
      </div>
      <div className={styles.exampleBody}>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel}>题目描述</label>
          <textarea
            className={styles.textarea}
            value={example.problem || ''}
            onChange={(e) => handleFieldChange('problem', e.target.value)}
            placeholder="题目描述..."
            rows={3}
          />
        </div>
        <div className={styles.solutionsSection}>
          <div className={styles.solutionsHeader}>
            <span className={styles.fieldLabel}>解法列表</span>
            <button className={styles.addBtn} onClick={handleAddSolution}>+ 添加解法</button>
          </div>
          {(example.solutions || []).map((sol, si) => (
            <SolutionEditor
              key={si}
              solution={sol}
              index={si}
              onChange={handleSolutionChange}
              onRemove={handleSolutionRemove}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default memo(ExampleEditor)
