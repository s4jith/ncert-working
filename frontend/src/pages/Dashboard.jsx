import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../services/authStore'
import {
    FaChartLine, FaBook, FaBrain, FaComments, FaTrophy, FaFire,
    FaArrowUp, FaArrowDown, FaMinus, FaClock, FaStar, FaExclamationCircle
} from 'react-icons/fa'
import {
    LineChart, Line, BarChart, Bar, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { quizApi } from '../services/api'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function Dashboard() {
    const { user } = useAuthStore()
    const [analytics, setAnalytics] = useState(null)
    const [loading, setLoading] = useState(true)
    const [quizHistory, setQuizHistory] = useState([])

    useEffect(() => {
        loadAnalytics()
    }, [])

    const loadAnalytics = async () => {
        try {
            const [analyticsRes, historyRes] = await Promise.all([
                quizApi.analytics(),
                quizApi.history()
            ])
            setAnalytics(analyticsRes.data)
            setQuizHistory(historyRes.data?.attempts || [])
        } catch (err) {
            console.error('Failed to load analytics:', err)
        } finally {
            setLoading(false)
        }
    }

    // Use real data from API
    const quizTrendData = quizHistory.slice(-10).map((q, i) => ({
        name: `Quiz ${i + 1}`,
        score: q.percentage || 0
    }))

    const subjectPerformance = analytics?.subject_stats || []

    const stats = {
        totalQuizzes: analytics?.total_quizzes || quizHistory.length || 0,
        avgScore: analytics?.average_score || 0,
        totalChats: analytics?.total_chats || 0,
        streak: analytics?.streak_days || 0,
    }

    const getScoreColor = (score) => {
        if (score >= 80) return 'text-green-600'
        if (score >= 60) return 'text-yellow-600'
        return 'text-red-600'
    }

    const getScoreTrend = () => {
        if (quizTrendData.length < 2) return { icon: <FaMinus />, color: 'text-gray-500', text: 'No data' }
        const last = quizTrendData[quizTrendData.length - 1].score
        const prev = quizTrendData[quizTrendData.length - 2].score
        if (last > prev) return { icon: <FaArrowUp />, color: 'text-green-500', text: 'Improving' }
        if (last < prev) return { icon: <FaArrowDown />, color: 'text-red-500', text: 'Needs focus' }
        return { icon: <FaMinus />, color: 'text-gray-500', text: 'Stable' }
    }

    const trend = getScoreTrend()

    const NoDataMessage = ({ message }) => (
        <div className="flex flex-col items-center justify-center h-48 text-gray-400">
            <FaExclamationCircle className="text-3xl mb-2" />
            <p>{message}</p>
        </div>
    )

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
            </div>
        )
    }

    return (
        <div className="max-w-7xl mx-auto px-4">
            {/* Welcome Header */}
            <div className="mb-8 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800">
                    Welcome back, <span className="text-indigo-600">{user?.full_name || user?.username || 'Student'}!</span>
                </h1>
                <p className="text-gray-600 mt-1">
                    {user?.grade ? `Class ${user.grade}` : ''} • Track your learning progress
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div className="glass rounded-xl p-5 card-hover animate-fade-in">
                    <div className="flex items-center justify-between mb-2">
                        <FaBrain className="text-2xl text-indigo-500" />
                        <span className={`flex items-center gap-1 text-sm ${trend.color}`}>
                            {trend.icon} {trend.text}
                        </span>
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{stats.totalQuizzes}</div>
                    <div className="text-sm text-gray-600">Quizzes Taken</div>
                </div>

                <div className="glass rounded-xl p-5 card-hover animate-fade-in">
                    <div className="flex items-center justify-between mb-2">
                        <FaTrophy className="text-2xl text-yellow-500" />
                        <span className={`text-sm font-medium ${getScoreColor(stats.avgScore)}`}>
                            {stats.avgScore >= 80 ? 'Excellent!' : stats.avgScore >= 60 ? 'Good' : stats.avgScore > 0 ? 'Keep trying' : ''}
                        </span>
                    </div>
                    <div className={`text-3xl font-bold ${getScoreColor(stats.avgScore)}`}>{stats.avgScore}%</div>
                    <div className="text-sm text-gray-600">Average Score</div>
                </div>

                <div className="glass rounded-xl p-5 card-hover animate-fade-in">
                    <div className="flex items-center gap-2 mb-2">
                        <FaComments className="text-2xl text-blue-500" />
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{stats.totalChats}</div>
                    <div className="text-sm text-gray-600">Questions Asked</div>
                </div>

                <div className="glass rounded-xl p-5 card-hover animate-fade-in">
                    <div className="flex items-center gap-2 mb-2">
                        <FaFire className="text-2xl text-orange-500" />
                    </div>
                    <div className="text-3xl font-bold text-gray-800">{stats.streak}</div>
                    <div className="text-sm text-gray-600">Day Streak 🔥</div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="grid lg:grid-cols-2 gap-6 mb-8">
                {/* Quiz Score Trend */}
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaChartLine className="text-indigo-500" />
                        Your Quiz Performance Trend
                    </h2>
                    {quizTrendData.length > 0 ? (
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={quizTrendData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                    <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <Tooltip />
                                    <Line
                                        type="monotone"
                                        dataKey="score"
                                        stroke="#6366f1"
                                        strokeWidth={3}
                                        dot={{ fill: '#6366f1', strokeWidth: 2, r: 5 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <NoDataMessage message="Take quizzes to see your progress" />
                    )}
                </div>

                {/* Subject Performance */}
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaBook className="text-orange-500" />
                        Performance by Subject
                    </h2>
                    {subjectPerformance.length > 0 ? (
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={subjectPerformance} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                    <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <YAxis dataKey="subject" type="category" width={80} tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
                                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                                        {subjectPerformance.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <NoDataMessage message="No subject data yet" />
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
                <Link to="/chat" className="glass rounded-xl p-6 card-hover flex items-center gap-4 group">
                    <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <FaComments className="text-2xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">Ask AI Tutor</h3>
                        <p className="text-gray-600">Get instant help with your doubts</p>
                    </div>
                </Link>

                <Link to="/quiz" className="glass rounded-xl p-6 card-hover flex items-center gap-4 group">
                    <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <FaBrain className="text-2xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">Take a Quiz</h3>
                        <p className="text-gray-600">Test your knowledge and improve</p>
                    </div>
                </Link>
            </div>

            {/* Recent Activity */}
            {quizHistory.length > 0 && (
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaClock className="text-gray-500" />
                        Recent Quiz History
                    </h2>
                    <div className="space-y-3">
                        {quizHistory.slice(0, 5).map((quiz, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${quiz.percentage >= 80 ? 'bg-green-100 text-green-600' :
                                            quiz.percentage >= 60 ? 'bg-yellow-100 text-yellow-600' : 'bg-red-100 text-red-600'
                                        }`}>
                                        {quiz.percentage >= 80 ? <FaStar /> : <FaBrain />}
                                    </div>
                                    <div>
                                        <p className="font-medium text-gray-800">{quiz.quiz_id || 'Quiz'}</p>
                                        <p className="text-sm text-gray-500">Score: {quiz.score}/{quiz.total}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className={`font-bold ${getScoreColor(quiz.percentage)}`}>{Math.round(quiz.percentage)}%</p>
                                    <p className="text-xs text-gray-500">{new Date(quiz.created_at).toLocaleDateString()}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default Dashboard
