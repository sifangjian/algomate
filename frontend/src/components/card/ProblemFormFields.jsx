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

const STATUS_OPTIONS = [
    { value: '', label: '选择状态' },
    { value: 'untried', label: '未尝试' },
    { value: 'accepted', label: '已通过' },
    { value: 'optimal', label: '最优解' },
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
                <label className={styles.formLabel}>注意事项</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.notes || ''}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    placeholder="记录解题时的注意事项、边界条件、易错点..."
                    rows={3}
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

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>关联题目</label>
                <div className={styles.techniqueManager}>
                    {formData.related_problems?.length > 0 && (
                        <div className={styles.techniqueTags}>
                            {formData.related_problems.map((p) => (
                                <span key={p.id} className={styles.techniqueTag}>
                                    <span>{p.title}</span>
                                    <button
                                        type="button"
                                        className={styles.techniqueTagRemove}
                                        onClick={() => {
                                            const updated = (formData.related_problems || []).filter(item => item.id !== p.id)
                                            handleChange('related_problems', updated)
                                            handleChange('related_problem_ids', updated.map(item => item.id))
                                        }}
                                    >
                                        ✕
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                    <div className={styles.techniqueSearch}>
                        <input
                            className={styles.formInput}
                            type="text"
                            value={formData.related_search || ''}
                            onChange={(e) => { handleChange('related_search', e.target.value); /* setShowDropdown(true) */ }}
                            onFocus={() => handleChange('related_show_dropdown', true)}
                            placeholder="搜索题目..."
                        />
                        {(formData.related_show_dropdown) && formData.related_search && (
                            <div className={styles.techniqueDropdown}>
                                {(allProblems || [])
                                    .filter(p => 
                                        !(formData.related_problem_ids || []).includes(p.id) &&
                                        p.title.toLowerCase().includes((formData.related_search || '').toLowerCase())
                                    )
                                    .slice(0, 10)
                                    .map((p) => (
                                        <button
                                            key={p.id}
                                            type="button"
                                            className={styles.techniqueDropdownItem}
                                            onClick={() => {
                                                const updated = [...(formData.related_problems || []), { id: p.id, title: p.title }]
                                                handleChange('related_problems', updated)
                                                handleChange('related_problem_ids', updated.map(item => item.id))
                                                handleChange('related_search', '')
                                                handleChange('related_show_dropdown', false)
                                            }}
                                        >
                                            {p.title}
                                        </button>
                                    ))
                                }
                                {(formData.related_show_dropdown) && formData.related_search && (allProblems || []).filter(p => 
                                    !(formData.related_problem_ids || []).includes(p.id) &&
                                    p.title.toLowerCase().includes((formData.related_search || '').toLowerCase())
                                ).length === 0 && (
                                    <div className={styles.techniqueDropdown}>
                                        <div className={styles.techniqueDropdownEmpty}>无匹配题目</div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}