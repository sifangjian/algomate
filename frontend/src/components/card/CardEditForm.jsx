import { useState, useCallback, useMemo, useEffect, memo } from 'react'
import { useCardStore } from '../../stores/cardStore'
import { cardService } from '../../services/cardService'
import { showToast } from '../ui/Toast/index'
import Button from '../ui/Button/Button'
import ExampleEditor from './ExampleEditor'
import CodeEditor from '../ui/CodeEditor'
import { ALGORITHM_CATEGORIES } from '../../constants/algorithmConstants'
import styles from './CardEditForm.module.css'

function parseJSON(value) {
    if (!value) return {}
    if (typeof value === 'object') return value
    try {
        return JSON.parse(value)
    } catch {
        return {}
    }
}

const TIER_FIELDS = {
    basic: [
        { key: 'concept_definition', label: '💡 概念定义', rows: 3 },
        { key: 'features', label: '🔑 特点', rows: 3 },
        { key: 'confusing_concepts', label: '🔀 易混淆概念', rows: 2 },
    ],
    advanced: [
        { key: 'common_mistakes', label: '❌ 易错点', rows: 3 },
        { key: 'extensions', label: '🔄 拓展方向', rows: 3 },
        { key: 'advanced_solutions', label: '⚡ 高级解法', rows: 3 },
    ],
}

const PRACTICAL_TEXT_FIELDS = [
    { key: 'applicable_scenarios', label: '📋 适用场景', rows: 3 },
    { key: 'precautions', label: '⚠️ 注意事项', rows: 2 },
]

function FieldTextarea({ label, value, onChange, rows, placeholder }) {
    return (
        <div className={styles.fieldGroup}>
            <div className={styles.fieldLabelRow}>
                <label className={styles.fieldLabel}>{label}</label>
            </div>
            <textarea
                className={styles.fieldTextarea}
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                rows={rows}
                placeholder={placeholder}
            />
        </div>
    )
}

// 卡牌搜索选择组件（用于关联题目、关联技巧等）
function CardSearchInput({ label, value, onChange, cardType, placeholder }) {
    const [searchText, setSearchText] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [searching, setSearching] = useState(false)
    const [showResults, setShowResults] = useState(false)
    const [loadedCards, setLoadedCards] = useState([])

    // 组件挂载时加载所有卡牌
    useEffect(() => {
        loadAllCards()
    }, [])

    const loadAllCards = async () => {
        setSearching(true)
        try {
            const result = await cardService.getAll({ keyword: '', limit: 200 })
            const cards = result.cards || []
            const filtered = cards.filter(c => !cardType || c.card_type === cardType)
            setLoadedCards(filtered)
        } catch {
            setLoadedCards([])
        } finally {
            setSearching(false)
        }
    }

    const handleSearch = useCallback(async (text) => {
        setSearchText(text)
        if (!text.trim()) {
            setSearchResults(loadedCards)
            setShowResults(true)
            return
        }
        const filtered = loadedCards.filter(c => c.name.includes(text))
        setSearchResults(filtered)
        setShowResults(true)
    }, [loadedCards])

    const handleSelect = useCallback((card) => {
        const newItem = `[[${card.name}]]`
        onChange([...(value || []), newItem])
        setSearchText('')
        setShowResults(false)
    }, [value, onChange])

    const handleRemove = useCallback((index) => {
        const newList = [...(value || [])]
        newList.splice(index, 1)
        onChange(newList)
    }, [value, onChange])

    return (
        <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>{label}</label>
            <div style={{ position: 'relative' }}>
                <input
                    className={styles.fieldInput}
                    value={searchText}
                    onChange={(e) => handleSearch(e.target.value)}
                    onFocus={() => {
                        setSearchResults(loadedCards)
                        setShowResults(true)
                    }}
                    onBlur={() => setTimeout(() => setShowResults(false), 200)}
                    placeholder={placeholder || "搜索并选择卡牌..."}
                />
                {searching && <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12, color: '#888' }}>搜索中...</span>}
                {showResults && searchResults.length > 0 && (
                    <div style={{
                        position: 'absolute', top: '100%', left: 0, right: 0,
                        background: '#1e1e1e', border: '1px solid #333', borderRadius: 6,
                        zIndex: 100, maxHeight: 200, overflowY: 'auto'
                    }}>
                        {searchResults.map(card => (
                            <div
                                key={card.id}
                                onMouseDown={() => handleSelect(card)}
                                style={{
                                    padding: '8px 12px', cursor: 'pointer', color: '#ccc', fontSize: '0.85rem',
                                    borderBottom: '1px solid #2a2a2a'
                                }}
                                onMouseEnter={e => e.target.style.background = '#2a2a2a'}
                                onMouseLeave={e => e.target.style.background = 'transparent'}
                            >
                                {card.name}
                            </div>
                        ))}
                    </div>
                )}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                {(value || []).map((item, i) => (
                    <span key={i} style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        padding: '3px 10px', background: 'rgba(99,102,241,0.1)',
                        border: '1px solid rgba(99,102,241,0.3)', borderRadius: 12,
                        fontSize: '0.8rem', color: '#a5b4fc'
                    }}>
                        {item.replace(/^\[\[|\]\]$/g, '')}
                        <button
                            type="button"
                            onClick={() => handleRemove(i)}
                            style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', padding: 0, fontSize: '0.8rem' }}
                        >
                            ×
                        </button>
                    </span>
                ))}
            </div>
        </div>
    )
}

const COMMON_COMPLEXITIES = [
    '时间：O(1)  空间：O(1)',
    '时间：O(log n)  空间：O(1)',
    '时间：O(n)  空间：O(1)',
    '时间：O(n)  空间：O(n)',
    '时间：O(n log n)  空间：O(n)',
    '时间：O(n²)  空间：O(1)',
    '时间：O(n²)  空间：O(n)',
    '时间：O(2ⁿ)  空间：O(n)',
    '时间：O(n!)  空间：O(1)',
]

// 复杂度输入组件（支持输入和选择）
function ComplexityInput({ label, value, onChange }) {
    const [showOptions, setShowOptions] = useState(false)
    const [inputValue, setInputValue] = useState(value || '')

    useEffect(() => {
        setInputValue(value || '')
    }, [value])

    const handleSelect = (complexity) => {
        setInputValue(complexity)
        onChange(complexity)
        setShowOptions(false)
    }

    return (
        <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>{label}</label>
            <div style={{ position: 'relative' }}>
                <input
                    className={styles.fieldInput}
                    value={inputValue}
                    onChange={(e) => {
                        setInputValue(e.target.value)
                        onChange(e.target.value)
                    }}
                    onFocus={() => setShowOptions(true)}
                    onBlur={() => setTimeout(() => setShowOptions(false), 200)}
                    placeholder="输入或选择复杂度..."
                />
                {showOptions && (
                    <div style={{
                        position: 'absolute', top: '100%', left: 0, right: 0,
                        background: '#1e1e1e', border: '1px solid #333', borderRadius: 6,
                        zIndex: 100, maxHeight: 250, overflowY: 'auto'
                    }}>
                        {COMMON_COMPLEXITIES.map((c, i) => (
                            <div
                                key={i}
                                onMouseDown={() => handleSelect(c)}
                                style={{
                                    padding: '8px 12px', cursor: 'pointer', color: '#ccc', fontSize: '0.85rem',
                                    borderBottom: '1px solid #2a2a2a', fontFamily: 'monospace'
                                }}
                                onMouseEnter={e => e.target.style.background = '#2a2a2a'}
                                onMouseLeave={e => e.target.style.background = 'transparent'}
                            >
                                {c}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

function CardEditForm({ card, onSave, onCancel }) {
    const { updateCard, setSelectedCard } = useCardStore()
    const [form, setForm] = useState({})
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        if (!card) return
        const basic = parseJSON(card.basic_content)
        const practical = parseJSON(card.practical_content)
        const advanced = parseJSON(card.advanced_content)
        const newContent = parseJSON(card.content) || {}

        setForm({
            algorithm_type: card.algorithm_type || '',
            difficulty: card.difficulty || 3,
            content: {
                one_line_definition: newContent.one_line_definition || '',
                trigger_condition: newContent.trigger_condition || '',
                core_ideas: newContent.core_ideas || [],
                complexity: newContent.complexity || '',
                related_problems: newContent.related_problems || [],
                related_tips: newContent.related_tips || newContent.similar_tips || [],
                pitfall_guide: newContent.pitfall_guide || [],
                one_line_problem: newContent.one_line_problem || '',
                core_skills: newContent.core_skills || [],
                solution_approach: newContent.solution_approach || [],
                core_code_snippet: newContent.core_code_snippet || '',
            },
            visual_links: card.visual_links || '',
        })
    }, [card])

    const hasChanges = useMemo(() => {
        if (!card || !form.content) return false
        const origContent = parseJSON(card.content) || {}

        const contentChanged = JSON.stringify(form.content) !== JSON.stringify(origContent)
        const typeChanged = (form.algorithm_type || '') !== (card.algorithm_type || '')
        const difficultyChanged = (form.difficulty || 3) !== (card.difficulty || 3)
        return contentChanged || typeChanged || difficultyChanged
    }, [form, card])

    const handleBasicChange = useCallback((key, value) => {
        setForm(prev => ({ ...prev, basic: { ...prev.basic, [key]: value } }))
    }, [])

    const handleAdvancedChange = useCallback((key, value) => {
        setForm(prev => ({ ...prev, advanced: { ...prev.advanced, [key]: value } }))
    }, [])

    const handlePracticalTextChange = useCallback((key, value) => {
        setForm(prev => ({ ...prev, practical: { ...prev.practical, [key]: value } }))
    }, [])

    const handleExampleChange = useCallback((index, updatedExample) => {
        setForm(prev => {
            const examples = [...prev.practical.examples]
            examples[index] = updatedExample
            return { ...prev, practical: { ...prev.practical, examples } }
        })
    }, [])

    const handleExampleRemove = useCallback((index) => {
        setForm(prev => ({
            ...prev,
            practical: {
                ...prev.practical,
                examples: prev.practical.examples.filter((_, i) => i !== index),
            },
        }))
    }, [])

    const handleAddExample = useCallback(() => {
        setForm(prev => ({
            ...prev,
            practical: {
                ...prev.practical,
                examples: [...prev.practical.examples, { title: '', problem: '', solutions: [] }],
            },
        }))
    }, [])

    const handleSave = useCallback(async () => {
        if (!card || !hasChanges) return
        setIsSaving(true)
        try {
            const payload = {
                algorithm_type: form.algorithm_type || null,
                difficulty: form.difficulty || 3,
                content: form.content,
                visual_links: form.visual_links,
            }
            const updatedCard = await updateCard(card.id, payload)
            setSelectedCard(updatedCard)
            showToast(`卡牌「${card.name}」已更新`, 'success')
            onSave?.(updatedCard)
        } catch (err) {
            if (err.message?.includes('40002') || err.message?.includes('未变更')) {
                showToast('卡牌内容未变更', 'warning')
            } else {
                showToast(`保存失败: ${err.message}`, 'error')
            }
        } finally {
            setIsSaving(false)
        }
    }, [card, form, hasChanges, updateCard, setSelectedCard, onSave])

    if (!card || !form.content) return null

    return (
        <div className={styles.form}>
            {/* 算法分类 */}
            <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>算法分类</label>
                <input
                    className={styles.fieldInput}
                    list="edit-type-list"
                    value={form.algorithm_type || ''}
                    onChange={(e) => setForm(prev => ({ ...prev, algorithm_type: e.target.value }))}
                    placeholder="选择或输入算法类型"
                />
                <datalist id="edit-type-list">
                    {ALGORITHM_CATEGORIES.map((t) => (
                        <option key={t} value={t} />
                    ))}
                </datalist>
            </div>



            {/* 难度 */}
            <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>难度</label>
                <div className={styles.starRating}>
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            type="button"
                            className={`${styles.starBtn} ${star <= (form.difficulty || 3) ? styles.starActive : ''}`}
                            onClick={() => setForm(prev => ({ ...prev, difficulty: star }))}
                            aria-label={`${star}星`}
                        >
                            {star <= (form.difficulty || 3) ? '★' : '☆'}
                        </button>
                    ))}
                    <span className={styles.starLabel}>{form.difficulty || 3}/5</span>
                </div>
            </div>

            {/* 新版技巧卡编辑器 */}
            {card.card_type === 'tip' && (
                <div className={styles.tierSection} style={{ borderLeftColor: '#6366f1' }}>
                    <h4 className={styles.tierTitle}>💡 技巧卡内容</h4>

                    <FieldTextarea
                        label="一句话定义（≤30字）"
                        value={form.content.one_line_definition}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, one_line_definition: v } }))}
                        rows={2}
                        placeholder="例如：用两个指针在数组两端向中间移动，逐步缩小搜索范围"
                    />

                    <FieldTextarea
                        label="触发条件（固定句式）"
                        value={form.content.trigger_condition}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, trigger_condition: v } }))}
                        rows={2}
                        placeholder="当看到______，且要求______时，想到______"
                    />

                    <FieldTextarea
                        label="核心思路（每行一个要点）"
                        value={(form.content.core_ideas || []).join('\n')}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, core_ideas: v.split('\n') } }))}
                        rows={4}
                        placeholder="例如：① 初始化左右指针 ② 移动右指针扩展窗口 ③ 不满足条件时移动左指针收缩 ④ 每次更新答案"
                    />

                    <ComplexityInput
                        label="复杂度"
                        value={form.content.complexity}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, complexity: v } }))}
                    />

                    <CardSearchInput
                        label="关联题目（搜索并选择题目卡）"
                        value={form.content.related_problems}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, related_problems: v } }))}
                        cardType="problem"
                    />

                    <CardSearchInput
                        label="关联技巧（搜索并选择技巧卡）"
                        value={form.content.related_tips}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, related_tips: v } }))}
                        cardType="tip"
                    />

                    <FieldTextarea
                        label="避坑指南（每行一个）"
                        value={(form.content.pitfall_guide || []).join('\n')}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, pitfall_guide: v.split('\n') } }))}
                        rows={3}
                    />
                </div>
            )}

            {/* 新版题目卡编辑器 */}
            {card.card_type === 'problem' && (
                <div className={styles.tierSection} style={{ borderLeftColor: '#10b981' }}>
                    <h4 className={styles.tierTitle}>📝 题目卡内容</h4>

                    <FieldTextarea
                        label="一句话题干（≤40字）"
                        value={form.content.one_line_problem}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, one_line_problem: v } }))}
                        rows={2}
                        placeholder="例如：给定一个字符串，找出不含重复字符的最长子串长度"
                    />

                    <CardSearchInput
                        label="核心考点（搜索并选择技巧卡）"
                        value={form.content.core_skills}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, core_skills: v } }))}
                        cardType="tip"
                    />

                    <FieldTextarea
                        label="解法思路（每行一个要点）"
                        value={(form.content.solution_approach || []).join('\n')}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, solution_approach: v.split('\n') } }))}
                        rows={4}
                        placeholder="例如：① 用哈希集维护窗口内字符 ② 右指针移动时检查重复 ③ 重复则移动左指针移除 ④ 每次更新maxLen"
                    />

                    <div className={styles.fieldGroup}>
                        <label className={styles.fieldLabel}>核心代码片段（仅保留3-5行）</label>
                        <CodeEditor
                            value={form.content.core_code_snippet}
                            onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, core_code_snippet: v } }))}
                            rows={5}
                            placeholder="例如：\nleft = right = 0\nwhile right < len(s):\n    window.add(s[right])\n    while 条件不满足: window.remove(s[left]); left += 1\n    ans = max(ans, right - left + 1); right += 1"
                        />
                    </div>

                    <ComplexityInput
                        label="复杂度"
                        value={form.content.complexity}
                        onChange={(v) => setForm(prev => ({ ...prev, content: { ...prev.content, complexity: v } }))}
                    />
                </div>
            )}

            <div className={styles.actions}>
                <Button variant="accent" onClick={handleSave} loading={isSaving} disabled={!hasChanges}>
                    💾 保存
                </Button>
                <Button variant="ghost" onClick={onCancel} disabled={isSaving}>
                    取消
                </Button>
            </div>
        </div>
    )
}

export default memo(CardEditForm)