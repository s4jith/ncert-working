import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FaSignInAlt, FaUser, FaLock } from 'react-icons/fa'
import { useAuthStore } from '../services/authStore'

function Login() {
    const navigate = useNavigate()
    const { login, loading, error } = useAuthStore()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault()
        const success = await login(username, password)
        if (success) {
            navigate('/dashboard')
        }
    }

    return (
        <div className="max-w-md mx-auto px-4 py-16">
            <div className="glass rounded-2xl p-8 animate-fade-in">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl mx-auto flex items-center justify-center mb-4">
                        <FaSignInAlt className="text-2xl text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-800">Welcome Back</h1>
                    <p className="text-gray-600">Sign in to continue learning</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                        <div className="relative">
                            <FaUser className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Enter your username"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                        <div className="relative">
                            <FaLock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="Enter your password"
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 gradient-primary text-white font-semibold rounded-xl hover:opacity-90 transition disabled:opacity-50"
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <p className="text-center text-gray-600 mt-6">
                    Don't have an account?{' '}
                    <Link to="/register" className="text-indigo-600 hover:underline font-medium">
                        Register
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default Login
