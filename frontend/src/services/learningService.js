import api from './api'

export const taskService = {
  getTodayTasks: () => api.get('/tasks?date=today'),
}

export const learningService = {
  getTopics: () => api.get('/learning/topics'),

  chat: (data) => api.post('/learning/chat', data),

  generateQuiz: (topic) => api.post('/learning/generate-quiz', { topic }),

  saveToCard: (data) => api.post('/cards/', data),

  explainConcept: (topic, concept) =>
    api.get(`/learning/explain-concept?topic=${topic}&concept=${concept}`),
}
