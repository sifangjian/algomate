import api from './api'

export const taskService = {
    getTodayTasks: () => api.get('/v1/tasks?date=today'),

    getUpcomingTasks: (days = 7) => api.get(`/v1/tasks/upcoming?days=${days}`),

    executeDailyTasks: () => api.post('/v1/tasks/execute'),
}

export const learningService = {
    getTopics: () => api.get('/v1/learning/topics'),

    chat: (data) => api.post('/v1/learning/chat', data),

    generateQuiz: (topic) => api.post('/v1/learning/generate-quiz', { topic }),

    saveToCard: (data) => api.post('/v1/cards', data),

    explainConcept: (topic, concept) =>
        api.get(`/v1/learning/explain-concept?topic=${topic}&concept=${concept}`),
}
