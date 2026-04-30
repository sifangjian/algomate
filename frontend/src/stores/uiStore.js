import { create } from 'zustand'

export const useUIStore = create((set, get) => ({
    toasts: [],
    taskDrawerOpen: false,
    modalOpen: false,
    modalContent: null,
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

    setModalOpen: (open) => set({ modalOpen: open }),

    setModalContent: (content) => set({ modalContent: content }),

    setTasks: (tasks) => set({ tasks }),

    setTasksLoading: (loading) => set({ tasksLoading: loading }),

    setTaskSummary: (summary) => set({ taskSummary: summary }),

    getTaskSummary: () => {
        const tasks = get().tasks
        const totalToday = tasks.length
        const completedToday = 0
        return {
            totalToday,
            completedToday,
            hasIncomplete: totalToday > completedToday,
        }
    },
}))
