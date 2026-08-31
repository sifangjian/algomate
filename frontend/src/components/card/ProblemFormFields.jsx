import { useState, useEffect, useCallback } from 'react'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import { cardService } from '../../services/cardService'
import TagSelector from '../ui/TagSelector/TagSelector'
import styles from './CreateCardForm.module.css'

const DIFFICULTY_OPTIONS = [
    { value: '', label: '选择难度' },
    { value: 'easy', label: 'Easy' },
    { value: 'medium', label: 'Medium' },
    { value: 'hard', label: 'Hard' },
]

export default function ProblemFormFields({ formData, onChange }) {
    const [allProblems, setAllProblems] = useState([])

    useEffect(() => {
        cardService.getProblems().then(data => {
            setAllProblems(data || [])
        }).catch(() => {})
    }, [])

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
                <label className={styles.formLabel}>算法类型 *</label>
                <TagSelector
                    value={formData.tags || []}
                    onChange={(tags) => handleChange('tags', tags)}
                    placeholder="搜索或选择算法类型..."
                    options={ALGORITHM_TYPES}
                />
                <span className={styles.formHint}>选择题目所属的算法类型，至少选择一个</span>
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>突破口（本题要解决的核心问题）</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.breakthrough || ''}
                    onChange={(e) => handleChange('breakthrough', e.target.value)}
                    placeholder="如：找出数组中重复出现两次的数与缺失的数"
                    rows={3}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>变体题 slug（同考点，逗号分隔）</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.variants || ''}
                    onChange={(e) => handleChange('variants', e.target.value)}
                    placeholder="如：3sum,4sum"
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>视频演示链接</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.video_demo_link || ''}
                    onChange={(e) => handleChange('video_demo_link', e.target.value)}
                    placeholder="https://www.bilibili.com/video/..."
                />
            </div>
        </>
    )
}
