import { create } from 'zustand'

export const useUIStore = create((set) => ({
    toasts: [],
    taskDrawerOpen: false,
    modalOpen: false,
    modalContent: null,
    taskSummary: {
        totalToday: 3,
        completedToday: 1,
        hasIncomplete: true,
    },

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

    setTaskSummary: (summary) => set({ taskSummary: summary }),
}))
