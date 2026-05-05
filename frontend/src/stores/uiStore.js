import { create } from 'zustand'

export const useUIStore = create((set, get) => ({
    toasts: [],
    taskDrawerOpen: false,
    tasks: [],
    tasksLoading: false,
    taskSummary: {},

    addToast: (toast) =>
        set((state) => ({
            toasts: [...state.toasts, { ...toast, id: Date.now() + Math.random() }],
        })),

    removeToast: (id) =>
        set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id),
        })),

    clearToasts: () => set({ toasts: [] }),

    setTaskDrawerOpen: (open) => set({ taskDrawerOpen: open }),

    setTasks: (tasks) => set({ tasks }),

    setTasksLoading: (loading) => set({ tasksLoading: loading }),

    setTaskSummary: (summary) => set({ taskSummary: summary }),

    fetchTaskSummary: async () => {
        try {
            const api = (await import('../services/api')).default
            const data = await api.get('/tasks/completed-count')
            set({ taskSummary: { completedToday: data.completed_today } })
        } catch {
            set({ taskSummary: { completedToday: 0 } })
        }
    },

    getTaskSummary: () => {
        const tasks = get().tasks
        const totalToday = tasks.length
        const completedToday = get().taskSummary.completedToday ?? 0
        return {
            totalToday,
            completedToday,
            hasIncomplete: totalToday > completedToday,
        }
    },
}))
