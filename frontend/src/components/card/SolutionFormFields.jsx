import { useState, useEffect, useCallback } from 'react'
import { cardService } from '../../services/cardService'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import ComplexityInput from './ComplexityInput'
import TagSelector from '../ui/TagSelector/TagSelector'
import CodeEditor from '../ui/CodeEditor'
import styles from './CreateCardForm.module.css'

export default function SolutionFormFields({ formData, onChange, problemId }) {
    const [allTechniques, setAllTechniques] = useState([])
    const [searchText, setSearchText] = useState('')
    const [showDropdown, setShowDropdown] = useState(false)

    const handleChange = useCallback((field, value) => {
        onChange(field, value)
    }, [onChange])

    useEffect(() => {
        cardService.getTechniques().then(data => {
            setAllTechniques(data || [])
        }).catch(() => {})
    }, [])

    // 如果提供了 problemId，自动设置
    useEffect(() => {
        if (problemId && !formData.problem_id) {
            onChange('problem_id', problemId)
        }
    }, [problemId, formData.problem_id, onChange])

    const currentTechniques = formData.techniques || []
    const currentTechniqueIds = new Set(currentTechniques.map(t => t.id))

    const addTechnique = useCallback((tech) => {
        if (currentTechniqueIds.has(tech.id)) return
        const updated = [...currentTechniques, { id: tech.id, name: tech.name, category: tech.category }]
        onChange('techniques', updated)
        onChange('technique_ids', updated.map(t => t.id))
        setSearchText('')
        setShowDropdown(false)
    }, [currentTechniques, currentTechniqueIds, onChange])

    const removeTechnique = useCallback((techId) => {
        const updated = currentTechniques.filter(t => t.id !== techId)
        onChange('techniques', updated)
        onChange('technique_ids', updated.map(t => t.id))
    }, [currentTechniques, onChange])

    const filteredTechniques = allTechniques
        .filter(t =>
            !currentTechniqueIds.has(t.id) &&
            t.name.toLowerCase().includes(searchText.toLowerCase())
        )
        .filter((t, i, arr) => arr.findIndex(item => item.name === t.name) === i)

    return (
        <>
            <div className={styles.formGroup}>
                <label className={styles.formLabel}>解法名称 *</label>
                <input
                    className={styles.formInput}
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="解法名称如 哈希表法"
                    required
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>关联技巧</label>
                <div className={styles.techniqueManager}>
                    {currentTechniques.length > 0 && (
                        <div className={styles.techniqueTags}>
                            {currentTechniques.map((tech) => (
                                <span key={tech.id} className={styles.techniqueTag}>
                                    <span>{tech.name}</span>
                                    <button
                                        type="button"
                                        className={styles.techniqueTagRemove}
                                        onClick={() => removeTechnique(tech.id)}
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
                            value={searchText}
                            onChange={(e) => { setSearchText(e.target.value); setShowDropdown(true) }}
                            onFocus={() => setShowDropdown(true)}
                            placeholder="搜索技巧..."
                        />
                        {showDropdown && searchText && filteredTechniques.length > 0 && (
                            <div className={styles.techniqueDropdown}>
                                {filteredTechniques.slice(0, 10).map((tech) => (
                                    <button
                                        key={tech.id}
                                        type="button"
                                        className={styles.techniqueDropdownItem}
                                        onClick={() => addTechnique(tech)}
                                    >
                                        {tech.name}
                                        {tech.category && <span className={styles.techniqueDropdownCat}>({tech.category})</span>}
                                    </button>
                                ))}
                            </div>
                        )}
                        {showDropdown && searchText && filteredTechniques.length === 0 && (
                            <div className={styles.techniqueDropdown}>
                                <div className={styles.techniqueDropdownEmpty}>无匹配技巧</div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>算法类型</label>
                <TagSelector
                    value={formData.algorithm_type ? [formData.algorithm_type] : []}
                    onChange={(tags) => handleChange('algorithm_type', tags.length > 0 ? tags[0] : '')}
                    placeholder="搜索或选择算法类型..."
                    options={ALGORITHM_TYPES}
                />
                <span className={styles.formHint}>设置解法所属的算法类型，用于主题归类</span>
            </div>

            <div className={styles.formRow}>
                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>时间复杂度</label>
                    <ComplexityInput
                        value={formData.time_complexity || ''}
                        onChange={(v) => handleChange('time_complexity', v)}
                        placeholder="O(n)"
                    />
                </div>
                <div className={styles.formGroup}>
                    <label className={styles.formLabel}>空间复杂度</label>
                    <ComplexityInput
                        value={formData.space_complexity || ''}
                        onChange={(v) => handleChange('space_complexity', v)}
                        placeholder="O(n)"
                    />
                </div>
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>突破口</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.breakthrough || ''}
                    onChange={(e) => handleChange('breakthrough', e.target.value)}
                    placeholder="突破口"
                    rows={3}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>详细思路</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.approach || ''}
                    onChange={(e) => handleChange('approach', e.target.value)}
                    placeholder="详细思路"
                    rows={5}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>代码</label>
                <CodeEditor
                    value={formData.code || ''}
                    onChange={(v) => handleChange('code', v)}
                    placeholder="代码"
                    rows={6}
                />
            </div>

            <div className={styles.formGroup}>
                <label className={styles.formLabel}>易错点</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.pitfalls || ''}
                    onChange={(e) => handleChange('pitfalls', e.target.value)}
                    placeholder="记录易错点..."
                    rows={3}
                />
                <span className={styles.formHint}>记录解题过程中的易错点</span>
            </div>
        </>
    )
}