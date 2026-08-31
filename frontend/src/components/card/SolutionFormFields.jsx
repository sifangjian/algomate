import { useState, useEffect, useCallback, useRef } from 'react'
import { cardService } from '../../services/cardService'
import ComplexityInput from './ComplexityInput'
import TagSelector from '../ui/TagSelector/TagSelector'
import CodeEditor from '../ui/CodeEditor'
import styles from './CreateCardForm.module.css'

export default function SolutionFormFields({ formData, onChange, problemId }) {
    const [allTechniques, setAllTechniques] = useState([])
    const [searchText, setSearchText] = useState('')
    const [showDropdown, setShowDropdown] = useState(false)
    // 题目搜索
    const [problemSearch, setProblemSearch] = useState('')
    const [problemSearchResults, setProblemSearchResults] = useState([])
    const [showProblemDropdown, setShowProblemDropdown] = useState(false)
    const [searchingProblem, setSearchingProblem] = useState(false)
    const searchTimerRef = useRef(null)

    const handleChange = useCallback((field, value) => {
        onChange(field, value)
    }, [onChange])

    useEffect(() => {
        cardService.getTechniques().then(data => {
            setAllTechniques(data || [])
        }).catch(() => {})
    }, [])

    useEffect(() => {
        cardService.getSolutions().then(data => {
            setAllSolutions(data || [])
        }).catch(() => {})
    }, [])

    // 如果提供了 problemId，自动设置
    useEffect(() => {
        if (problemId && !formData.problem_id) {
            onChange('problem_id', problemId)
        }
    }, [problemId, formData.problem_id, onChange])

    // 如果 problemId 变化但已有 problem_title，则显示在搜索框中
    useEffect(() => {
        if (problemId && formData.problem_title) {
            setProblemSearch(formData.problem_title)
        }
    }, [problemId, formData.problem_title])

    // 模糊搜索题目（防抖 300ms）
    useEffect(() => {
        if (searchTimerRef.current) {
            clearTimeout(searchTimerRef.current)
        }
        if (!problemSearch.trim()) {
            setProblemSearchResults([])
            setShowProblemDropdown(false)
            return
        }
        searchTimerRef.current = setTimeout(async () => {
            setSearchingProblem(true)
            try {
                const results = await cardService.searchProblems(problemSearch.trim())
                setProblemSearchResults(results || [])
                setShowProblemDropdown(true)
            } catch {
                setProblemSearchResults([])
            } finally {
                setSearchingProblem(false)
            }
        }, 300)
        return () => {
            if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
        }
    }, [problemSearch])

    // 选择题目
    const selectProblem = useCallback((problem) => {
        onChange('problem_id', problem.id)
        onChange('problem_title', problem.title)
        setProblemSearch(problem.title)
        setShowProblemDropdown(false)
    }, [onChange])

    // 清除已选题目
    const clearProblem = useCallback(() => {
        onChange('problem_id', '')
        onChange('problem_title', '')
        setProblemSearch('')
        setProblemSearchResults([])
        setShowProblemDropdown(false)
    }, [onChange])

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
            {/* 关联题目搜索 */}
            <div className={styles.formGroup}>
                <label className={styles.formLabel}>关联题目 *</label>
                {formData.problem_id ? (
                    <div className={styles.techniqueManager}>
                        <div className={styles.techniqueTags}>
                            <span className={styles.techniqueTag}>
                                <span>{formData.problem_title || `题目 #${formData.problem_id}`}</span>
                                <button
                                    type="button"
                                    className={styles.techniqueTagRemove}
                                    onClick={clearProblem}
                                >
                                    ✕
                                </button>
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className={styles.techniqueSearch}>
                        <input
                            className={styles.formInput}
                            type="text"
                            value={problemSearch}
                            onChange={(e) => { setProblemSearch(e.target.value); setShowProblemDropdown(true) }}
                            onFocus={() => { if (problemSearchResults.length > 0) setShowProblemDropdown(true) }}
                            placeholder="搜索题目名称..."
                        />
                        {searchingProblem && (
                            <div className={styles.techniqueDropdown}>
                                <div className={styles.techniqueDropdownEmpty}>搜索中...</div>
                            </div>
                        )}
                        {!searchingProblem && showProblemDropdown && problemSearchResults.length > 0 && (
                            <div className={styles.techniqueDropdown}>
                                {problemSearchResults.slice(0, 10).map((p) => (
                                    <button
                                        key={p.id}
                                        type="button"
                                        className={styles.techniqueDropdownItem}
                                        onClick={() => selectProblem(p)}
                                    >
                                        {p.title}
                                        {p.difficulty && (
                                            <span className={styles.techniqueDropdownCat}>
                                                {p.difficulty === 'easy' ? '简单' : p.difficulty === 'medium' ? '中等' : '困难'}
                                            </span>
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}
                        {!searchingProblem && showProblemDropdown && problemSearch.trim() && problemSearchResults.length === 0 && (
                            <div className={styles.techniqueDropdown}>
                                <div className={styles.techniqueDropdownEmpty}>无匹配题目</div>
                            </div>
                        )}
                    </div>
                )}
            </div>

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
                <label className={styles.formLabel}>破题思路（此解法针对突破口具体怎么解决）</label>
                <textarea
                    className={styles.formTextarea}
                    value={formData.notes || ''}
                    onChange={(e) => handleChange('notes', e.target.value)}
                    placeholder="如：利用哈希表 O(1) 查询，一次遍历同时定位重复与缺失"
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

            <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                    <input
                        type="checkbox"
                        checked={!!formData.is_optimal}
                        onChange={(e) => handleChange('is_optimal', e.target.checked ? 1 : 0)}
                    />
                    标记此解法为最优解
                </label>
            </div>
        </>
    )
}