import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Auth
export const authApi = {
    login: (username, password) =>
        api.post('/auth/login', new URLSearchParams({ username, password }), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        }),
    register: (data) => api.post('/auth/register', data),
    me: () => api.get('/auth/me'),
    refresh: () => api.post('/auth/refresh'),
}

// Chat
export const chatApi = {
    send: (data) => api.post('/chat/', data),
    history: (conversationId, page = 1) =>
        api.get('/chat/history', { params: { conversation_id: conversationId, page } }),
    report: (questionHash) => api.post('/chat/report', { question_hash: questionHash }),
}

// Quiz
export const quizApi = {
    chapters: (grade, subject) =>
        api.get('/quiz/chapters', { params: { grade, subject } }),
    questions: (chapterId, count = 10) =>
        api.get(`/quiz/questions/${chapterId}`, { params: { count } }),
    submit: (data) => api.post('/quiz/submit', data),
    history: () => api.get('/quiz/history'),
    analytics: () => api.get('/quiz/analytics'),
}

// Admin
export const adminApi = {
    dashboard: () => api.get('/admin/dashboard'),
    students: (page = 1, search = '') =>
        api.get('/admin/students', { params: { page, search } }),
    studentAnalytics: (studentId) => api.get(`/admin/students/${studentId}/analytics`),
    books: (page = 1, status = '') =>
        api.get('/admin/books', { params: { page, status } }),
    deleteBook: (bookId) => api.delete(`/admin/books/${bookId}`),
    uploadBook: (formData) => api.post('/upload/book', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    uploadStatus: (uploadId) => api.get(`/upload/status/${uploadId}`),
    cacheStats: () => api.get('/admin/cache/stats'),
}

export default api
