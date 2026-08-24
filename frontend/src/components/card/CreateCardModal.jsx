import { useState, useCallback, useEffect } from 'react'
import { cardService } from '../../services/cardService'
import Modal from '../ui/Modal/Modal'
import ProblemFormFields from './ProblemFormFields'
import SolutionFormFields from './SolutionFormFields'
import TechniqueFormFields from './TechniqueFormFields'
import styles from './CreateCardForm.module.css'

const TABS = [
    { key: 'problem', label: '题目卡' },
    { key: 'technique', label: '技巧卡' },
]

const INITIAL_FORM_DATA = {
    problem: {
        problemTitle: '',
        title: '',
        difficulty: '',
        leetcode_link: '',
        tags: [],
        my_status: '',
        notes: '',
        video_demo_link: '',
        related_problems: [],
        related_problem_ids: [],
        related_search: '',
        related_show_dropdown: false,
    },
    solution: {
        problem_id: '',
        problem_title: '',
        name: '',
        time_complexity: '',
        space_complexity: '',
        breakthrough: '',
        approach: '',
        code: '',
        pitfalls: '',
        technique_ids: [],
        techniques: [],
        related_solutions: [],
        related_solution_ids: [],
        related_solution_search: '',
        related_solution_show_dropdown: false,
    },
    technique: {
        name: '',
        category: '',
        use_cases: '',
        code_template: '',
        memory_anchors: '',
        proficiency: '',
        algorithm_type: '',
        difficulty: 3,
        notes: '',
        video_demo_link: '',
    },
}

function mapCardToFormData(cardType, data) {
    switch (cardType) {
        case 'problem':
            return {
                problemTitle: data.title || '',
                title: data.title || '',
                difficulty: data.difficulty || '',
                leetcode_link: data.leetcode_link || '',
                tags: data.tags || [],
                my_status: data.my_status || '',
                notes: data.notes || '',
                video_demo_link: data.video_demo_link || '',
                related_problems: data.related_problems || [],
                related_problem_ids: data.related_problem_ids || [],
            }
        case 'solution':
            return {
                problem_id: data.problem_id || '',
                problem_title: data.problem_title || '',
                name: data.name || '',
                algorithm_type: data.algorithm_type || '',
                time_complexity: data.time_complexity || '',
                space_complexity: data.space_complexity || '',
                breakthrough: data.breakthrough || '',
                approach: data.approach || '',
                code: data.code || '',
                pitfalls: Array.isArray(data.pitfalls) ? data.pitfalls.join('\n') : '',
                techniques: data.techniques || [],
                technique_ids: (data.techniques || []).map(t => t.id),
                related_solutions: data.related_solutions || [],
                related_solution_ids: data.related_solution_ids || [],
            }
        case 'technique':
            return {
                name: data.name || '',
                category: data.category || '',
                use_cases: data.use_cases || '',
                code_template: data.code_template || '',
                memory_anchors: data.memory_anchors || '',
                proficiency: data.proficiency != null ? String(data.proficiency) : '',
                algorithm_type: data.algorithm_type || '',
                difficulty: data.difficulty ?? 3,
                notes: data.notes || '',
                video_demo_link: data.video_demo_link || '',
            }
        default:
            return {}
    }
}

export default function CreateCardModal({ open, onClose, onCreated, editType, editData, forceType, problemId }) {
    // 如果 forceType 设置，则强制使用该类型（不显示选项卡）；否则按编辑模式或默认
    const isEditing = !!(editType && editData)
    const initialType = forceType || (isEditing ? editType : 'problem')
    const [activeTab, setActiveTab] = useState(initialType)
    const [formData, setFormData] = useState(INITIAL_FORM_DATA)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState(null)
    const showTabs = !forceType && !isEditing

    // 当进入编辑模式时，初始化表单数据
    useEffect(() => {
        if (isEditing && editData && open) {
            setActiveTab(editType)
            setFormData(prev => ({
                ...prev,
                [editType]: mapCardToFormData(editType, editData),
            }))
            setError(null)
        }
    }, [isEditing, editType, editData, open])

    // 当 forceType 变化时同步 activeTab
    useEffect(() => {
        if (forceType) {
            setActiveTab(forceType)
        }
    }, [forceType])

    const resetForm = useCallback(() => {
        setFormData(INITIAL_FORM_DATA)
        setActiveTab(forceType || 'problem')
        setIsSubmitting(false)
        setError(null)
    }, [forceType])

    const handleClose = useCallback(() => {
        resetForm()
        onClose()
    }, [onClose, resetForm])

    const handleFieldChange = useCallback((field, value) => {
        setFormData((prev) => ({
            ...prev,
            [activeTab]: { ...prev[activeTab], [field]: value },
        }))
        setError(null)
    }, [activeTab])

    const handleTabChange = useCallback((tabKey) => {
        if (isEditing) return
        setActiveTab(tabKey)
        setError(null)
    }, [isEditing])

    const validate = useCallback(() => {
        const current = formData[activeTab]
        if (activeTab === 'problem' && !current.problemTitle?.trim()) {
            setError('请输入标题')
            return false
        }
        if (activeTab === 'solution') {
            if (!current.problem_id) {
                setError('请搜索并选择关联的题目')
                return false
            }
            if (!current.name?.trim()) {
                setError('请输入解法名称')
                return false
            }
        }
        if (activeTab === 'technique' && !current.name?.trim()) {
            setError('请输入技巧名称')
            return false
        }
        return true
    }, [activeTab, formData])

    const handleSubmit = useCallback(async () => {
        if (!validate()) return
        setIsSubmitting(true)
        setError(null)

        try {
            const data = { ...formData[activeTab] }

            // 清理空字符串和未填字段
            Object.keys(data).forEach((key) => {
                if (data[key] === '' || data[key] === null || data[key] === undefined) {
                    delete data[key]
                }
            })

            let result
            if (isEditing) {
                // 编辑模式：调用更新 API
                switch (activeTab) {
                    case 'problem':
                        // 将合并的标题字段映射到 title
                        if (data.problemTitle) {
                            data.title = data.problemTitle.trim()
                            delete data.problemTitle
                        }
                        if (typeof data.tags === 'string') {
                            data.tags = data.tags.split(',').map((t) => t.trim()).filter(Boolean)
                        }
                        delete data.related_problems
                        delete data.related_search
                        delete data.related_show_dropdown
                        result = await cardService.updateProblem(editData.id, data)
                        break
                    case 'solution': {
                        // 将 pitfalls 从文本转换为列表
                        if (typeof data.pitfalls === 'string') {
                            data.pitfalls = data.pitfalls.split('\n').map(p => p.trim()).filter(Boolean)
                        }
                        const techniqueIds = data.technique_ids
                        delete data.technique_ids
                        delete data.techniques
                        delete data.related_solutions
                        delete data.related_solution_search
                        delete data.related_solution_show_dropdown

                        result = await cardService.updateSolution(editData.id, data)

                        // Sync technique associations
                        if (techniqueIds && Array.isArray(techniqueIds)) {
                            const oldTechIds = (editData.techniques || []).map(t => t.id)
                            const newTechIds = techniqueIds

                            for (const oldId of oldTechIds) {
                                if (!newTechIds.includes(oldId)) {
                                    await cardService.unlinkTechnique(editData.id, oldId)
                                }
                            }

                            for (const newId of newTechIds) {
                                if (!oldTechIds.includes(newId)) {
                                    try {
                                        await cardService.linkTechnique(editData.id, newId)
                                    } catch (e) {
                                        if (!e.message?.includes('已关联')) throw e
                                    }
                                }
                            }
                        }
                        break
                    }
                    case 'technique':
                        result = await cardService.updateTechnique(editData.id, data)
                        break
                    default:
                        throw new Error('未知的卡片类型')
                }
            } else {
                // 创建模式
                switch (activeTab) {
                    case 'problem':
                        // 将合并的标题字段映射到 title
                        if (data.problemTitle) {
                            data.title = data.problemTitle.trim()
                            delete data.problemTitle
                        }
                        if (typeof data.tags === 'string') {
                            data.tags = data.tags.split(',').map((t) => t.trim()).filter(Boolean)
                        }
                        delete data.related_problems
                        delete data.related_search
                        delete data.related_show_dropdown
                        result = await cardService.createProblem(data)
                        break
                    case 'solution':
                        // 将 pitfalls 从文本转换为列表
                        if (typeof data.pitfalls === 'string') {
                            data.pitfalls = data.pitfalls.split('\n').map(p => p.trim()).filter(Boolean)
                        }
                        delete data.related_solutions
                        delete data.related_solution_search
                        delete data.related_solution_show_dropdown
                        result = await cardService.createSolution(data)
                        break
                    case 'technique':
                        result = await cardService.createTechnique(data)
                        break
                    default:
                        throw new Error('未知的卡片类型')
                }
            }

            onCreated?.(result)
            handleClose()
        } catch (err) {
            setError(err.message || (isEditing ? '保存失败，请重试' : '创建失败，请重试'))
        } finally {
            setIsSubmitting(false)
        }
    }, [activeTab, formData, validate, onCreated, handleClose, isEditing, editData])

    const renderFormFields = () => {
        const currentData = formData[activeTab]

        switch (activeTab) {
            case 'problem':
                return (
                    <ProblemFormFields
                        formData={currentData}
                        onChange={handleFieldChange}
                    />
                )
            case 'solution':
                return (
                    <SolutionFormFields
                        formData={currentData}
                        onChange={handleFieldChange}
                        problemId={problemId}
                    />
                )
            case 'technique':
                return (
                    <TechniqueFormFields
                        formData={currentData}
                        onChange={handleFieldChange}
                    />
                )
            default:
                return null
        }
    }

    const getTitle = () => {
        if (forceType === 'solution') return isEditing ? '编辑解法' : '添加解法'
        if (isEditing) return '编辑卡片'
        return '创建新卡片'
    }

    return (
        <Modal open={open} onClose={handleClose} title={getTitle()} size="lg" closeOnOverlay={false}>
            <div className={styles.formContainer}>
                {showTabs && (
                    <div className={styles.tabRow}>
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                type="button"
                                className={activeTab === tab.key ? styles.tabActive : styles.tab}
                                onClick={() => handleTabChange(tab.key)}
                                disabled={isEditing && activeTab !== tab.key}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                )}

                {error && (
                    <p className={styles.errorMsg} role="alert">
                        {error}
                    </p>
                )}

                {renderFormFields()}

                <div className={styles.buttonRow}>
                    <button
                        type="button"
                        className={styles.cancelBtn}
                        onClick={handleClose}
                        disabled={isSubmitting}
                    >
                        取消
                    </button>
                    <button
                        type="button"
                        className={styles.submitBtn}
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? (isEditing ? '保存中...' : '创建中...') : (isEditing ? '保存' : '创建')}
                    </button>
                </div>
            </div>
        </Modal>
    )
}