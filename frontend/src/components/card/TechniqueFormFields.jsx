import { useCallback } from 'react'
import TagSelector from '../ui/TagSelector/TagSelector'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import CodeEditor from '../ui/CodeEditor'
import styles from './CreateCardForm.module.css'

export default function TechniqueFormFields({ formData, onChange }) {
    const handleChange = useCallback((field, value) => {
        onChange(field, value)
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
                <label className={styles.formLabel}>注意事项</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.notes || ''}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    placeholder="记录使用此技巧时的注意事项、边界条件、易错点..."
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
        </>
    )
}
