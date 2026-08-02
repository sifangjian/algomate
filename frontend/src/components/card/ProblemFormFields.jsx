import { useCallback } from 'react'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import styles from './CreateCardForm.module.css'

const DIFFICULTY_OPTIONS = [
    { value: '', label: '选择难度' },
    { value: 'easy', label: 'Easy' },
    { value: 'medium', label: 'Medium' },
    { value: 'hard', label: 'Hard' },
]

const STATUS_OPTIONS = [
    { value: '', label: '选择状态' },
    { value: 'untried', label: '未尝试' },
    { value: 'accepted', label: '已通过' },
    { value: 'optimal', label: '最优解' },
]

export default function ProblemFormFields({ formData, onChange }) {
    const handleChange = useCallback((field, value) => {
        onChange(field, value)
    }, [onChange])

    return (
        <>
            <div className={styles.formGroup}>
                <label className={styles.formLabel}>题号/标题 *</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.problemTitle || ''}
                    onChange={(e) => handleChange('problemTitle', e.target.value)}
                    placeholder="如 645. 错误的集合"
                    required
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>难度</label>
                <select
                    className={styles.formSelect}
                    value={formData.difficulty || ''}
                    onChange={(e) => handleChange('difficulty', e.target.value)}
                >
                    {DIFFICULTY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>LeetCode 链接</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.leetcode_link || ''}
                    onChange={(e) => handleChange('leetcode_link', e.target.value)}
                    placeholder="https://leetcode.com/..."
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>我的状态</label>
                <select
                    className={styles.formSelect}
                    value={formData.my_status || ''}
                    onChange={(e) => handleChange('my_status', e.target.value)}
                >
                    {STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>
        </>
    )
}