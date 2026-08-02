import { useCallback } from 'react'
import TagSelector from '../ui/TagSelector/TagSelector'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import CodeEditor from '../ui/CodeEditor'
import styles from './CreateCardForm.module.css'

const PROFICIENCY_OPTIONS = [
    { value: '', label: '选择熟练度' },
    { value: 1, label: '1 - 不了解' },
    { value: 2, label: '2 - 知道概念' },
    { value: 3, label: '3 - 能写出代码' },
    { value: 4, label: '4 - 熟练应用' },
    { value: 5, label: '5 - 精通' },
]

export default function TechniqueFormFields({ formData, onChange }) {
    const handleChange = useCallback((field, value) => {
        onChange(field, value)
    }, [onChange])

    const handleAlgoTypeChange = useCallback((tags) => {
        // 只取第一个选中的算法类型
        onChange('algorithm_type', tags.length > 0 ? tags[0] : '')
    }, [onChange])

    return (
        <>
            <div className={styles.formGroup}>
                <label className={styles.formLabel}>技巧名称 *</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="技巧名称"
                    required
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>算法类型</label>
                <TagSelector
                    value={formData.algorithm_type ? [formData.algorithm_type] : []}
                    onChange={handleAlgoTypeChange}
                    placeholder="搜索或选择算法类型..."
                    options={ALGORITHM_TYPES}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>适用场景</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.use_cases || ''}
                    onChange={(e) => handleChange('use_cases', e.target.value)}
                    placeholder="当题目中包含__，且__时考虑此技巧"
                    rows={3}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>标准代码模板</label>
                <CodeEditor
                    value={formData.code_template || ''}
                    onChange={(v) => handleChange('code_template', v)}
                    placeholder="标准代码模板"
                    rows={6}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>记忆锚点/关键词</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.memory_anchors || ''}
                    onChange={(e) => handleChange('memory_anchors', e.target.value)}
                    placeholder="记忆锚点/关键词"
                    rows={3}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>熟练度</label>
                <select
                    className={styles.formSelect}
                    value={formData.proficiency ?? ''}
                    onChange={(e) => handleChange('proficiency', e.target.value ? Number(e.target.value) : '')}
                >
                    {PROFICIENCY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>

            </>
    )
}