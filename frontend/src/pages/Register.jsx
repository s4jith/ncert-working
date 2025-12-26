import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FaUserPlus, FaUser, FaEnvelope, FaLock, FaGraduationCap } from 'react-icons/fa'
import { useAuthStore } from '../services/authStore'

function Register() {
    const navigate = useNavigate()
    const { register, loading, error } = useAuthStore()
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        full_name: '',
        grade: '',
    })

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const data = { ...formData }
        if (data.grade) data.grade = parseInt(data.grade)
        const success = await register(data)
        if (success) {
            navigate('/dashboard')
        }
    }

    return (
        <div className="max-w-md mx-auto px-4 py-16">
            <div className="glass rounded-2xl p-8 animate-fade-in">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl mx-auto flex items-center justify-center mb-4">
                        <FaUserPlus className="text-2xl text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-800">Create Account</h1>
                    <p className="text-gray-600">Start your learning journey</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                        <div className="relative">
                            <FaUser className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                name="full_name"
                                value={formData.full_name}
                                onChange={handleChange}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500"
                                placeholder="Your full name"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                        <div className="relative">
                            <FaUser className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                name="username"
                                value={formData.username}
                                onChange={handleChange}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500"
                                placeholder="Choose a username"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <div className="relative">
                            <FaEnvelope className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500"
                                placeholder="your@email.com"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Grade</label>
                        <div className="relative">
                            <FaGraduationCap className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <select
                                name="grade"
                                value={formData.grade}
                                onChange={handleChange}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value="">Select your class</option>
                                {[5, 6, 7, 8, 9, 10, 11, 12].map(g => (
                                    <option key={g} value={g}>Class {g}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                        <div className="relative">
                            <FaLock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                className="w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500"
                                placeholder="Minimum 8 characters"
                                required
                                minLength={8}
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
                        {loading ? 'Creating account...' : 'Create Account'}
                    </button>
                </form>

                <p className="text-center text-gray-600 mt-6">
                    Already have an account?{' '}
                    <Link to="/login" className="text-indigo-600 hover:underline font-medium">
                        Sign In
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default Register
