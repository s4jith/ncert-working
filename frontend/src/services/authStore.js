import { create } from 'zustand'
import { authApi } from './api'

export const useAuthStore = create((set, get) => ({
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: !!localStorage.getItem('token'),
    loading: false,
    error: null,

    login: async (username, password) => {
        set({ loading: true, error: null })
        try {
            const { data } = await authApi.login(username, password)
            localStorage.setItem('token', data.access_token)
            set({
                user: data.user,
                token: data.access_token,
                isAuthenticated: true,
                loading: false
            })
            return true
        } catch (err) {
            set({
                error: err.response?.data?.detail || 'Login failed',
                loading: false
            })
            return false
        }
    },

    register: async (userData) => {
        set({ loading: true, error: null })
        try {
            const { data } = await authApi.register(userData)
            localStorage.setItem('token', data.access_token)
            set({
                user: data.user,
                token: data.access_token,
                isAuthenticated: true,
                loading: false
            })
            return true
        } catch (err) {
            set({
                error: err.response?.data?.detail || 'Registration failed',
                loading: false
            })
            return false
        }
    },

    logout: () => {
        localStorage.removeItem('token')
        set({ user: null, token: null, isAuthenticated: false })
    },

    fetchUser: async () => {
        if (!get().token) return
        try {
            const { data } = await authApi.me()
            set({ user: data })
        } catch (err) {
            get().logout()
        }
    },
}))
