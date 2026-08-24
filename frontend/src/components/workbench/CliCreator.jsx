import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { cardService } from '../../services/cardService'
import { ALGORITHM_TYPES } from '../../constants/algorithmConstants'
import styles from './CliCreator.module.css'

const FIELD_DEFS = {
    problem: [
        { key: 'title', label: '题目全称', required: true, placeholder: '如 "645. 错误的集合"' },
        { key: 'difficulty', label: '难度', required: false, default: 'medium', options: ['easy', 'medium', 'hard'] },
        { key: 'leetcode_link', label: 'LeetCode 链接', required: false, placeholder: 'https://leetcode.cn/problems/...' },
        { key: 'tags', label: '标签（逗号分隔·输入可补全）', required: false, placeholder: '如: 数组,哈希表', list: true, options: ALGORITHM_TYPES, optionCount: ALGORITHM_TYPES.length },
        { key: 'my_status', label: '我的状态', required: false, default: 'untried', options: ['untried', 'accepted', 'optimal'] },
        { key: 'notes', label: '注意事项', required: false },
        { key: 'video_demo_link', label: '视频演示链接', required: false },
    ],
    solution: [
        { key: 'problem_search', label: '关联题目', required: true, search: true, placeholder: '输入题目名称搜索' },
        { key: 'name', label: '解法名称', required: true, placeholder: '如 "哈希表法"' },
        { key: 'algorithm_type', label: '算法类型', required: false, options: ALGORITHM_TYPES, optionCount: ALGORITHM_TYPES.length },
        { key: 'time_complexity', label: '时间复杂度', required: false, placeholder: '如 O(n)' },
        { key: 'space_complexity', label: '空间复杂度', required: false, placeholder: '如 O(n)' },
        { key: 'breakthrough', label: '突破口', required: false },
        { key: 'approach', label: '详细思路（Markdown，可后续编辑）', required: false },
        { key: 'code', label: '代码（可后续编辑）', required: false },
        { key: 'pitfalls', label: '易错点（逗号分隔）', required: false, list: true },
    ],
    technique: [
        { key: 'name', label: '技巧名称', required: true, placeholder: '如 "双指针技巧"' },
        { key: 'category', label: '分类', required: false, default: 'algorithm', options: ['data_structure', 'algorithm', 'template'] },
        { key: 'use_cases', label: '适用场景', required: false },
        { key: 'code_template', label: '标准代码模板（可后续编辑）', required: false },
        { key: 'memory_anchors', label: '记忆锚点/关键词', required: false },
        { key: 'proficiency', label: '熟练度 1-5', required: false, default: 1, type: 'number', options: [1, 2, 3, 4, 5] },
        { key: 'algorithm_type', label: '算法类型', required: false, options: ALGORITHM_TYPES, optionCount: ALGORITHM_TYPES.length },
        { key: 'difficulty', label: '难度 1-5', required: false, default: 3, type: 'number', options: [1, 2, 3, 4, 5] },
        { key: 'notes', label: '注意事项', required: false },
        { key: 'video_demo_link', label: '视频演示链接', required: false },
    ],
}

const CARD_TYPE_LABELS = {
    problem: '题目卡片 (problem)',
    solution: '解法卡片 (solution)',
    technique: '技巧卡片 (technique)',
}

export default function CliCreator() {
    const [inputValue, setInputValue] = useState('')
    const [messages, setMessages] = useState([
        { type: 'system', text: 'algoMate-cli v0.1.0' },
    ])
    const [loading, setLoading] = useState(true)
    const [wizard, setWizard] = useState(null)
    const [suggestions, setSuggestions] = useState({ filtered: [], highlighted: -1, visible: false })
    const [editPicker, setEditPicker] = useState(null) // { fields: [{key, label}], filter: '' }
    const [problemSearchResults, setProblemSearchResults] = useState([])
    const [searchingProblem, setSearchingProblem] = useState(false)
    const [pendingProblem, setPendingProblem] = useState(null) // { id, title }
    const [selectedProblemTitle, setSelectedProblemTitle] = useState('')
    const searchTimerRef = useRef(null)
    const logRef = useRef(null)
    const inputRef = useRef(null)

    const currentField = useMemo(() => {
        if (!wizard) return null
        const fields = FIELD_DEFS[wizard.cardType]
        return fields?.[wizard.fieldIndex] ?? null
    }, [wizard])

    useEffect(() => {
        async function fetchStats() {
            try {
                const overview = await cardService.getOverview()
                const totalCards = (overview.total_problems || 0) + (overview.total_solutions || 0) + (overview.total_techniques || 0)
                const totalDue = overview.total_due || 0

                setMessages(prev => [
                    ...prev,
                    { type: 'success', text: `✓ 已加载 ${totalCards} 张卡片 · ${totalDue} 项待复习` },
                    { type: 'system', text: '输入 /help 查看命令...' },
                ])
            } catch (err) {
                setMessages(prev => [
                    ...prev,
                    { type: 'error', text: '✗ 加载失败，请检查后端服务是否正常运行' },
                    { type: 'system', text: '输入 /help 查看命令...' },
                ])
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [])

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight
        }
    }, [messages])

    const promptCurrentField = useCallback((wizardState) => {
        const { cardType, fieldIndex, data } = wizardState
        const fields = FIELD_DEFS[cardType]
        if (fieldIndex >= fields.length) return null

        const field = fields[fieldIndex]
        const msgs = []

        // Main label
        msgs.push({ type: 'wizard', text: `请输入 ${field.label} (${field.key})` })

        // Required & default info
        const hints = []
        if (field.required) hints.push('[必填]')
        if (field.default !== undefined) hints.push(`[默认: ${field.default}]`)
        if (hints.length > 0) {
            msgs.push({ type: 'wizardReq', text: `  ${hints.join(' ')}` })
        }

        // Current value (when editing a previously filled field)
        if (data[field.key] !== undefined) {
            const currVal = Array.isArray(data[field.key])
                ? data[field.key].join(', ')
                : data[field.key]
            msgs.push({ type: 'wizardReq', text: `  [当前值: ${currVal}]` })
        }

        // Options
        if (field.options) {
            if (field.optionCount > 20) {
                msgs.push({ type: 'wizardOpt', text: `  可选值: ${field.options.slice(0, 8).join(', ')}... (共${field.optionCount}项)` })
            } else {
                msgs.push({ type: 'wizardOpt', text: `  可选值: ${field.options.join(', ')}` })
            }
        }

        // Example
        if (field.placeholder && !field.options) {
            msgs.push({ type: 'wizardEg', text: `  e.g. ${field.placeholder}` })
        }

        // Skip hint
        if (!field.required) {
            msgs.push({ type: 'wizardSkip', text: '  (直接回车跳过)' })
        }

        return msgs
    }, [])

    const startWizard = useCallback((cardType) => {
        const wizardState = { cardType, fieldIndex: 0, data: {}, returnToFieldIndex: null }
        setWizard(wizardState)
        setSuggestions({ filtered: [], highlighted: -1, visible: false })

        const newMessages = [
            { type: 'success', text: `开始创建 ${CARD_TYPE_LABELS[cardType]}` },
            { type: 'system', text: '输入 /cancel 取消，/edit 修改已填字段' },
        ]

        const prompts = promptCurrentField(wizardState)
        if (prompts) newMessages.push(...prompts)

        setMessages(prev => [...prev, ...newMessages])
    }, [promptCurrentField])

    // Build edit picker list from filled wizard fields
    const buildEditFields = useCallback((wizardState) => {
        if (!wizardState) return []
        const fields = FIELD_DEFS[wizardState.cardType]
        return Object.keys(wizardState.data)
            .map(key => {
                const f = fields.find(f => f.key === key)
                return f ? { key: f.key, label: f.label } : null
            })
            .filter(Boolean)
    }, [])

    const selectSuggestion = useCallback((value) => {
        // If in edit picker mode, selecting a field name
        if (editPicker) {
            // value is a field key
            const fields = FIELD_DEFS[wizard.cardType]
            const idx = fields.findIndex(f => f.key === value)
            if (idx >= 0) {
                const newData = { ...wizard.data }
                delete newData[value]
                const newWizard = {
                    ...wizard,
                    fieldIndex: idx,
                    data: newData,
                    returnToFieldIndex: wizard.fieldIndex,
                }
                setWizard(newWizard)
                setEditPicker(null)
                setSuggestions({ filtered: [], highlighted: -1, visible: false })
                setInputValue('')
                setMessages(prev => [...prev, { type: 'system', text: `返回修改 ${fields[idx].label}` }])
                const prompts = promptCurrentField(newWizard)
                if (prompts) setMessages(prev => [...prev, ...prompts])
            }
            return
        }

        if (currentField?.search) {
            // 搜索模式：找到匹配的题目并选中
            const problem = problemSearchResults.find(r => r.title === value)
            if (problem) {
                setPendingProblem({ id: problem.id, title: problem.title })
                setInputValue(problem.title)
                setSuggestions({ filtered: [], highlighted: -1, visible: false })
                setTimeout(() => {
                    const form = inputRef.current?.closest('form')
                    if (form) form.requestSubmit()
                }, 0)
            }
            return
        }

        if (currentField?.list) {
            const parts = inputValue.split(',')
            parts[parts.length - 1] = value
            setInputValue(parts.join(',') + ',')
            setSuggestions({ filtered: [], highlighted: -1, visible: false })
            inputRef.current?.focus()
        } else {
            setInputValue(value)
            setSuggestions({ filtered: [], highlighted: -1, visible: false })
            setTimeout(() => {
                const form = inputRef.current?.closest('form')
                if (form) form.requestSubmit()
            }, 0)
        }
    }, [currentField, inputValue, editPicker, wizard, promptCurrentField, problemSearchResults])

    const processWizardInput = useCallback(async (val, wizardState) => {
        const { cardType, fieldIndex, data, returnToFieldIndex } = wizardState
        const fields = FIELD_DEFS[cardType]
        const field = fields[fieldIndex]

        let value = val.trim()
        const newData = { ...data }

        // If editing an existing field and user entered empty, keep the old value
        if (value === '' && data[field.key] !== undefined) {
            value = data[field.key]
        }

        // Handle empty input for optional fields (only for new entries)
        if (value === '') {
            if (!field.required) {
                if (field.default !== undefined) {
                    value = field.default
                } else {
                    value = null
                }
            } else {
                setMessages(prev => [...prev, { type: 'error', text: '该字段为必填项，请重新输入' }])
                const prompts = promptCurrentField(wizardState)
                if (prompts) setMessages(prev => [...prev, ...prompts])
                return
            }
        }

        // Handle search field (problem_search)
        if (value !== null && field.search) {
            if (pendingProblem && pendingProblem.title === value) {
                // 用户通过建议下拉框选择了题目
                newData['problem_id'] = pendingProblem.id
                newData['problem_title'] = pendingProblem.title
                setPendingProblem(null)
                // 跳过后续的 Store the value 逻辑，直接跳转
                const displayVal = pendingProblem.title
                if (returnToFieldIndex !== null && returnToFieldIndex > fieldIndex) {
                    const returnWizard = {
                        ...wizardState,
                        fieldIndex: returnToFieldIndex,
                        data: newData,
                        returnToFieldIndex: null,
                    }
                    setWizard(returnWizard)
                    setSuggestions({ filtered: [], highlighted: -1, visible: false })
                    setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                    setMessages(prev => [...prev, { type: 'system', text: '已返回原位置，继续填写' }])
                    const prompts = promptCurrentField(returnWizard)
                    if (prompts) setMessages(prev => [...prev, ...prompts])
                    return
                }
                const nextIndex = fieldIndex + 1
                if (nextIndex >= fields.length) {
                    // 提交创建
                    setWizard(null)
                    setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                    setMessages(prev => [...prev, { type: 'system', text: '正在创建卡片...' }])
                    try {
                        let result
                        switch (cardType) {
                            case 'problem': result = await cardService.createProblem(newData); break
                            case 'solution': result = await cardService.createSolution(newData); break
                            case 'technique': result = await cardService.createTechnique(newData); break
                        }
                        setMessages(prev => [
                            ...prev,
                            { type: 'success', text: `✓ 创建成功! ${cardType === 'problem' ? '题目' : cardType === 'solution' ? '解法' : '技巧'}卡片 ID: ${result.id}` },
                            { type: 'wizardValue', text: `  名称: ${result.title || result.name || '(未命名)'}` },
                            { type: 'wizardValue', text: `  时间: ${result.created_at ? new Date(result.created_at).toLocaleString('zh-CN') : new Date().toLocaleString('zh-CN')}` },
                            { type: 'system', text: '输入 /help 查看命令...' },
                        ])
                    } catch (err) {
                        setMessages(prev => [
                            ...prev,
                            { type: 'error', text: `✗ 创建失败: ${err.response?.data?.detail || err.message || '未知错误'}` },
                            { type: 'system', text: '输入 /help 查看命令...' },
                        ])
                    }
                    return
                }
                const newWizard = { ...wizardState, fieldIndex: nextIndex, data: newData, returnToFieldIndex: null }
                setWizard(newWizard)
                setSuggestions({ filtered: [], highlighted: -1, visible: false })
                setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                const prompts = promptCurrentField(newWizard)
                if (prompts) setMessages(prev => [...prev, ...prompts])
                return
            } else {
                // 用户直接输入了文字，尝试搜索匹配
                try {
                    const results = await cardService.searchProblems(value)
                    if (results && results.length === 1) {
                        // 唯一匹配，自动选中
                        newData['problem_id'] = results[0].id
                        newData['problem_title'] = results[0].title
                        const displayVal = results[0].title
                        if (returnToFieldIndex !== null && returnToFieldIndex > fieldIndex) {
                            const returnWizard = {
                                ...wizardState,
                                fieldIndex: returnToFieldIndex,
                                data: newData,
                                returnToFieldIndex: null,
                            }
                            setWizard(returnWizard)
                            setSuggestions({ filtered: [], highlighted: -1, visible: false })
                            setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                            setMessages(prev => [...prev, { type: 'system', text: '已返回原位置，继续填写' }])
                            const prompts = promptCurrentField(returnWizard)
                            if (prompts) setMessages(prev => [...prev, ...prompts])
                            return
                        }
                        const nextIndex = fieldIndex + 1
                        if (nextIndex >= fields.length) {
                            setWizard(null)
                            setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                            setMessages(prev => [...prev, { type: 'system', text: '正在创建卡片...' }])
                            try {
                                let result
                                switch (cardType) {
                                    case 'problem': result = await cardService.createProblem(newData); break
                                    case 'solution': result = await cardService.createSolution(newData); break
                                    case 'technique': result = await cardService.createTechnique(newData); break
                                }
                                setMessages(prev => [
                                    ...prev,
                                    { type: 'success', text: `✓ 创建成功! ${cardType === 'problem' ? '题目' : cardType === 'solution' ? '解法' : '技巧'}卡片 ID: ${result.id}` },
                                    { type: 'wizardValue', text: `  名称: ${result.title || result.name || '(未命名)'}` },
                                    { type: 'wizardValue', text: `  时间: ${result.created_at ? new Date(result.created_at).toLocaleString('zh-CN') : new Date().toLocaleString('zh-CN')}` },
                                    { type: 'system', text: '输入 /help 查看命令...' },
                                ])
                            } catch (err) {
                                setMessages(prev => [
                                    ...prev,
                                    { type: 'error', text: `✗ 创建失败: ${err.response?.data?.detail || err.message || '未知错误'}` },
                                    { type: 'system', text: '输入 /help 查看命令...' },
                                ])
                            }
                            return
                        }
                        const newWizard = { ...wizardState, fieldIndex: nextIndex, data: newData, returnToFieldIndex: null }
                        setWizard(newWizard)
                        setSuggestions({ filtered: [], highlighted: -1, visible: false })
                        setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
                        const prompts = promptCurrentField(newWizard)
                        if (prompts) setMessages(prev => [...prev, ...prompts])
                        return
                    } else if (results && results.length > 1) {
                        setMessages(prev => [...prev, { type: 'error', text: `找到多个匹配，请使用 Tab 补全或从下拉菜单中选择: ${results.map(r => r.title).join(', ')}` }])
                        const prompts = promptCurrentField(wizardState)
                        if (prompts) setMessages(prev => [...prev, ...prompts])
                        return
                    } else {
                        setMessages(prev => [...prev, { type: 'error', text: `未找到匹配的题目: "${value}"` }])
                        const prompts = promptCurrentField(wizardState)
                        if (prompts) setMessages(prev => [...prev, ...prompts])
                        return
                    }
                } catch (err) {
                    setMessages(prev => [...prev, { type: 'error', text: `搜索失败: ${err.message || '未知错误'}` }])
                    const prompts = promptCurrentField(wizardState)
                    if (prompts) setMessages(prev => [...prev, ...prompts])
                    return
                }
            }
        }

        // Type conversion
        if (value !== null && field.type === 'number') {
            const parsed = parseInt(value, 10)
            if (isNaN(parsed)) {
                setMessages(prev => [...prev, { type: 'error', text: '请输入有效数字' }])
                const prompts = promptCurrentField(wizardState)
                if (prompts) setMessages(prev => [...prev, ...prompts])
                return
            }
            value = parsed
        }

        // List conversion
        if (value !== null && field.list) {
            value = value.split(',').map(s => s.trim()).filter(Boolean)
        }

        // Validate against options list
        if (value !== null && field.options) {
            const validOptions = field.options.map(String)
            if (field.list) {
                const invalid = value.filter(v => !validOptions.includes(v))
                if (invalid.length > 0) {
                    setMessages(prev => [...prev, { type: 'error', text: `"${invalid.join(', ')}" 不在可选值中，请重新输入` }])
                    const prompts = promptCurrentField({ ...wizardState, data: newData })
                    if (prompts) setMessages(prev => [...prev, ...prompts])
                    return
                }
            } else {
                if (!validOptions.includes(String(value))) {
                    setMessages(prev => [...prev, { type: 'error', text: `"${value}" 不在可选值中，请重新输入` }])
                    const prompts = promptCurrentField({ ...wizardState, data: newData })
                    if (prompts) setMessages(prev => [...prev, ...prompts])
                    return
                }
            }
        }

        // Store the value
        if (value !== null) {
            newData[field.key] = value
        }

        const displayVal = val.trim() || (data[field.key] !== undefined ? String(data[field.key]) : '(跳过)')

        // If we were editing a field (returnToFieldIndex is set), jump back to the original position
        if (returnToFieldIndex !== null && returnToFieldIndex > fieldIndex) {
            const returnWizard = {
                ...wizardState,
                fieldIndex: returnToFieldIndex,
                data: newData,
                returnToFieldIndex: null,
            }
            setWizard(returnWizard)
            setSuggestions({ filtered: [], highlighted: -1, visible: false })
            setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
            setMessages(prev => [...prev, { type: 'system', text: '已返回原位置，继续填写' }])
            const prompts = promptCurrentField(returnWizard)
            if (prompts) setMessages(prev => [...prev, ...prompts])
            return
        }

        // Move to next field
        const nextIndex = fieldIndex + 1

        if (nextIndex >= fields.length) {
            setWizard(null)
            setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
            setMessages(prev => [...prev, { type: 'system', text: '正在创建卡片...' }])

            try {
                let result
                switch (cardType) {
                    case 'problem':
                        result = await cardService.createProblem(newData)
                        break
                    case 'solution':
                        result = await cardService.createSolution(newData)
                        break
                    case 'technique':
                        result = await cardService.createTechnique(newData)
                        break
                }
                setMessages(prev => [
                    ...prev,
                    { type: 'success', text: `✓ 创建成功! ${cardType === 'problem' ? '题目' : cardType === 'solution' ? '解法' : '技巧'}卡片 ID: ${result.id}` },
                    { type: 'wizardValue', text: `  名称: ${result.title || result.name || '(未命名)'}` },
                    { type: 'wizardValue', text: `  时间: ${result.created_at ? new Date(result.created_at).toLocaleString('zh-CN') : new Date().toLocaleString('zh-CN')}` },
                    { type: 'system', text: '输入 /help 查看命令...' },
                ])
            } catch (err) {
                setMessages(prev => [
                    ...prev,
                    { type: 'error', text: `✗ 创建失败: ${err.response?.data?.detail || err.message || '未知错误'}` },
                    { type: 'system', text: '输入 /help 查看命令...' },
                ])
            }
        } else {
            const newWizard = { ...wizardState, fieldIndex: nextIndex, data: newData, returnToFieldIndex: null }
            setWizard(newWizard)
            setSuggestions({ filtered: [], highlighted: -1, visible: false })
            setMessages(prev => [...prev, { type: 'wizardValue', text: `✓ ${field.label}: ${displayVal}` }])
            const prompts = promptCurrentField(newWizard)
            if (prompts) setMessages(prev => [...prev, ...prompts])
        }
    }, [promptCurrentField, pendingProblem])

    const handleInputChange = useCallback((e) => {
        const val = e.target.value
        setInputValue(val)

        if (editPicker) {
            // Edit picker mode: filter field labels
            const filtered = val
                ? editPicker.filter(f => f.label.toLowerCase().includes(val.toLowerCase()))
                : editPicker
            setSuggestions({
                filtered: filtered.map(f => f.key),
                highlighted: -1,
                visible: filtered.length > 0,
            })
        } else if (wizard && currentField?.search) {
            // 搜索模式：调用 API 模糊搜索
            if (searchTimerRef.current) {
                clearTimeout(searchTimerRef.current)
            }
            if (!val.trim()) {
                setProblemSearchResults([])
                setSuggestions({ filtered: [], highlighted: -1, visible: false })
                return
            }
            searchTimerRef.current = setTimeout(async () => {
                setSearchingProblem(true)
                try {
                    const results = await cardService.searchProblems(val.trim())
                    setProblemSearchResults(results || [])
                    const titles = (results || []).map(r => r.title)
                    setSuggestions({
                        filtered: titles,
                        highlighted: -1,
                        visible: titles.length > 0,
                    })
                } catch {
                    setProblemSearchResults([])
                } finally {
                    setSearchingProblem(false)
                }
            }, 300)
        } else if (wizard && currentField?.options) {
            const opts = currentField.options.map(String)
            const searchToken = currentField.list ? val.split(',').pop().trim() : val
            const filtered = searchToken
                ? opts.filter(opt => opt.toLowerCase().includes(searchToken.toLowerCase()))
                : opts
            setSuggestions({
                filtered,
                highlighted: -1,
                visible: searchToken.length > 0 && filtered.length > 0 && filtered.length < opts.length,
            })
        } else {
            setSuggestions({ filtered: [], highlighted: -1, visible: false })
        }
    }, [wizard, currentField, editPicker])

    const handleKeyDown = useCallback((e) => {
        if (!suggestions.visible || suggestions.filtered.length === 0) return

        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSuggestions(prev => ({
                ...prev,
                highlighted: Math.min(prev.highlighted + 1, prev.filtered.length - 1),
            }))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSuggestions(prev => ({
                ...prev,
                highlighted: Math.max(prev.highlighted - 1, 0),
            }))
        } else if (e.key === 'Enter' && suggestions.highlighted >= 0) {
            e.preventDefault()
            selectSuggestion(suggestions.filtered[suggestions.highlighted])
        } else if (e.key === 'Tab') {
            if (suggestions.filtered.length === 1) {
                e.preventDefault()
                selectSuggestion(suggestions.filtered[0])
            } else if (suggestions.highlighted >= 0) {
                e.preventDefault()
                selectSuggestion(suggestions.filtered[suggestions.highlighted])
            }
        } else if (e.key === 'Escape') {
            e.preventDefault()
            if (editPicker) {
                setEditPicker(null)
                setSuggestions({ filtered: [], highlighted: -1, visible: false })
            } else {
                setSuggestions(prev => ({ ...prev, visible: false }))
            }
        }
    }, [suggestions, selectSuggestion, editPicker])

    // Get display label for a field key (for edit picker dropdown)
    const getFieldLabel = useCallback((key) => {
        if (!wizard) return key
        const fields = FIELD_DEFS[wizard.cardType]
        const f = fields.find(f => f.key === key)
        return f ? f.label : key
    }, [wizard])

    const handleSubmit = (e) => {
        e.preventDefault()
        const val = inputValue.trim()

        // Wizard mode: allow empty input for skipping optional fields
        if (wizard) {
            setMessages(prev => [...prev, { type: 'prompt', text: val || '(空)' }])
            setInputValue('')
            setSuggestions({ filtered: [], highlighted: -1, visible: false })

            if (val === '/cancel') {
                setWizard(null)
                setEditPicker(null)
                setMessages(prev => [
                    ...prev,
                    { type: 'system', text: '已取消创建' },
                    { type: 'system', text: '输入 /help 查看命令...' },
                ])
                return
            }

            if (val === '/help') {
                setMessages(prev => [...prev, {
                    type: 'help',
                    text: '向导模式中可用命令:\n  /edit          - 选择要修改的已填字段\n  /cancel        - 取消当前操作\n  /help          - 显示此帮助信息',
                }])
                return
            }

            if (val.startsWith('/edit')) {
                const parts = val.split(' ')
                const fieldKey = parts[1]
                const fields = FIELD_DEFS[wizard.cardType]
                const filledFields = Object.keys(wizard.data)

                if (filledFields.length === 0) {
                    setMessages(prev => [...prev, { type: 'error', text: '暂无已填字段可修改' }])
                    return
                }

                if (fieldKey) {
                    // Direct jump to a specific field key
                    const idx = fields.findIndex(f => f.key === fieldKey)
                    if (idx >= 0 && wizard.data[fieldKey] !== undefined) {
                        const newData = { ...wizard.data }
                        delete newData[fieldKey]
                        const newWizard = {
                            ...wizard,
                            fieldIndex: idx,
                            data: newData,
                            returnToFieldIndex: wizard.fieldIndex,
                        }
                        setWizard(newWizard)
                        setMessages(prev => [...prev, { type: 'system', text: `返回修改 ${fields[idx].label}` }])
                        const prompts = promptCurrentField(newWizard)
                        if (prompts) setMessages(prev => [...prev, ...prompts])
                        return
                    }
                    setMessages(prev => [...prev, { type: 'error', text: `字段 "${fieldKey}" 不存在或尚未填写` }])
                    return
                }

                // No field key - show interactive picker
                const editFields = buildEditFields(wizard)
                setEditPicker(editFields)
                // Show field list in the dropdown

                // Show the field list in messages too
                const fieldList = editFields.map((f, i) => `  ${i + 1}. ${f.label} (${f.key})`).join('\n')
                setMessages(prev => [...prev, {
                    type: 'wizardOpt',
                    text: '选择要修改的字段（↑↓ 切换，Enter 确认，Esc 取消）:',
                }, {
                    type: 'wizardOpt',
                    text: fieldList,
                }])

                // Set suggestions to show all edit fields
                setSuggestions({
                    filtered: editFields.map(f => f.key),
                    highlighted: 0,
                    visible: true,
                })
                return
            }

            processWizardInput(val, wizard)
            return
        }

        if (!val) return

        setMessages(prev => [...prev, { type: 'prompt', text: val }])
        setInputValue('')
        setSuggestions({ filtered: [], highlighted: -1, visible: false })

        // Normal command processing
        if (val === '/new') {
            setMessages(prev => [...prev, {
                type: 'wizard',
                text: '请选择卡片类型:',
            }, {
                type: 'wizardOpt',
                text: '  /new problem   - 题目卡片',
            }, {
                type: 'wizardOpt',
                text: '  /new solution  - 解法卡片',
            }, {
                type: 'wizardOpt',
                text: '  /new technique - 技巧卡片',
            }])
        } else if (val === '/new problem') {
            startWizard('problem')
        } else if (val === '/new solution') {
            startWizard('solution')
        } else if (val === '/new technique') {
            startWizard('technique')
        } else if (val === '/help') {
            setMessages(prev => [...prev, {
                type: 'help',
                text: '可用命令:\n  /new            - 交互式创建卡片\n  /new problem    - 创建题目卡片\n  /new solution   - 创建解法卡片\n  /new technique  - 创建技巧卡片\n  /edit <字段名>   - 修改已填字段\n  /cancel         - 取消当前操作\n  /help           - 显示此帮助信息',
            }])
        } else {
            setMessages(prev => [...prev, { type: 'error', text: `未知命令: ${val}，输入 /help 查看可用命令` }])
        }
    }

    return (
        <div className={styles.cliContainer}>
            <div className={styles.cliLog} ref={logRef}>
                {messages.map((entry, idx) => (
                    <div key={idx} className={`${styles.logLine} ${styles[entry.type] || styles.system}`}>
                        <span className={styles.promptSymbol}>
                            {entry.type === 'prompt' ? '>' : '$'}
                        </span>
                        <span className={styles.logText}>
                            {entry.type === 'help'
                                ? entry.text.split('\n').map((line, i) => (
                                    <span key={i}>{line}<br /></span>
                                ))
                                : entry.text.split('\n').map((line, i) => (
                                    <span key={i}>{line}<br /></span>
                                ))
                            }
                        </span>
                    </div>
                ))}
                {loading && (
                    <div className={`${styles.logLine} ${styles.system}`}>
                        <span className={styles.promptSymbol}>$</span>
                        <span className={styles.logText}>正在加载系统状态...</span>
                    </div>
                )}
            </div>
            <div className={styles.inputWrapper}>
                <form className={styles.cliInput} onSubmit={handleSubmit}>
                    <span className={styles.inputPrompt}>$</span>
                    <input
                        ref={inputRef}
                        type="text"
                        className={styles.inputField}
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        placeholder={editPicker ? '输入字段名搜索...' : wizard ? '输入值或 /cancel 取消...' : '输入 /new 创建卡片，/help 查看命令...'}
                        autoFocus
                        autoComplete="off"
                    />
                </form>
                {suggestions.visible && suggestions.filtered.length > 0 && (
                    <div className={styles.suggestionDropdown}>
                        {suggestions.filtered.map((opt, i) => {
                            const isSearch = currentField?.search
                            const problem = isSearch ? problemSearchResults.find(r => r.title === opt) : null
                            return (
                                <div
                                    key={i}
                                    className={`${styles.suggestionItem} ${i === suggestions.highlighted ? styles.suggestionHighlighted : ''}`}
                                    onMouseDown={(e) => { e.preventDefault(); selectSuggestion(opt) }}
                                    onMouseEnter={() => setSuggestions(prev => ({ ...prev, highlighted: i }))}
                                >
                                    {editPicker ? getFieldLabel(opt) : (
                                        <span className={styles.suggestionContent}>
                                            <span className={styles.suggestionText}>{opt}</span>
                                            {problem && (
                                                <span className={styles.suggestionMeta}>
                                                    {problem.difficulty === 'easy' ? '简单' : problem.difficulty === 'medium' ? '中等' : '困难'}
                                                </span>
                                            )}
                                        </span>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}