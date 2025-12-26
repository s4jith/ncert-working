import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    FaChartBar, FaBook, FaUsers, FaComments, FaBrain, FaDatabase,
    FaUpload, FaClock, FaGraduationCap, FaTrophy, FaSync, FaChartLine,
    FaExclamationCircle
} from 'react-icons/fa'
import {
    BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { adminApi } from '../services/api'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

function Admin() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [classAnalytics, setClassAnalytics] = useState([])
    const [subjectAnalytics, setSubjectAnalytics] = useState([])
    const [topPerformers, setTopPerformers] = useState([])

    useEffect(() => {
        loadDashboard()
    }, [])

    const loadDashboard = async () => {
        try {
            setLoading(true)
            const { data } = await adminApi.dashboard()
            setStats(data)

            // Use real data from API
            setClassAnalytics(data.class_analytics || [])
            setSubjectAnalytics(data.subject_analytics || [])
            setTopPerformers(data.top_performers || [])
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load dashboard')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto px-4">
                <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl">
                    <strong>Error:</strong> {error}
                </div>
            </div>
        )
    }

    const statCards = [
        { icon: <FaUsers className="text-blue-500" />, label: 'Total Students', value: stats?.users?.total || 0, gradient: 'from-blue-500 to-indigo-500' },
        { icon: <FaComments className="text-green-500" />, label: 'Questions Asked', value: stats?.chats?.total || 0, gradient: 'from-green-500 to-emerald-500' },
        { icon: <FaBrain className="text-purple-500" />, label: 'Quiz Attempts', value: stats?.quizzes?.total_attempts || 0, gradient: 'from-purple-500 to-violet-500' },
        { icon: <FaBook className="text-orange-500" />, label: 'Books Uploaded', value: stats?.books?.total || 0, gradient: 'from-orange-500 to-red-500' },
        { icon: <FaDatabase className="text-indigo-500" />, label: 'Vectors', value: stats?.vector_db?.total_vectors || 0, gradient: 'from-indigo-500 to-blue-500' },
    ]

    const totalStudents = classAnalytics.reduce((sum, c) => sum + c.students, 0)

    const NoDataMessage = ({ message }) => (
        <div className="flex flex-col items-center justify-center h-48 text-gray-400">
            <FaExclamationCircle className="text-3xl mb-2" />
            <p>{message}</p>
        </div>
    )

    return (
        <div className="max-w-7xl mx-auto px-4">
            {/* Header */}
            <div className="mb-6 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    <FaChartBar className="text-indigo-500" />
                    Admin Analytics Dashboard
                </h1>
                <p className="text-gray-600">Real-time overview of student performance</p>
            </div>

            {/* Quick Actions - Moved to Top */}
            <div className="grid md:grid-cols-3 gap-4 mb-8">
                <Link to="/admin/books" className="glass rounded-xl p-5 card-hover flex items-center gap-4 group">
                    <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <FaUpload className="text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">Manage Books</h3>
                        <p className="text-sm text-gray-600">Upload PDFs and content</p>
                    </div>
                </Link>

                <Link to="/admin/students" className="glass rounded-xl p-5 card-hover flex items-center gap-4 group">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <FaUsers className="text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">View Students</h3>
                        <p className="text-sm text-gray-600">Student analytics</p>
                    </div>
                </Link>

                <button onClick={loadDashboard} className="glass rounded-xl p-5 card-hover flex items-center gap-4 group text-left">
                    <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <FaSync className="text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">Refresh Data</h3>
                        <p className="text-sm text-gray-600">Update analytics</p>
                    </div>
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                {statCards.map((stat, idx) => (
                    <div key={idx} className="glass rounded-xl p-5 card-hover animate-fade-in relative overflow-hidden">
                        <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${stat.gradient} opacity-10 rounded-bl-full`}></div>
                        <div className="flex items-center gap-3 mb-2">{stat.icon}</div>
                        <div className="text-2xl font-bold text-gray-800">{stat.value.toLocaleString()}</div>
                        <div className="text-sm text-gray-600">{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Charts Row */}
            <div className="grid lg:grid-cols-2 gap-6 mb-8">
                {/* Students by Class */}
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaGraduationCap className="text-indigo-500" />
                        Students by Class
                    </h2>
                    {classAnalytics.length > 0 ? (
                        <>
                            <div className="h-72">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={classAnalytics}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ class: cls, students, percent }) => `${cls}: ${(percent * 100).toFixed(0)}%`}
                                            outerRadius={100}
                                            dataKey="students"
                                        >
                                            {classAnalytics.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip formatter={(value) => [`${value} students`]} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="text-center mt-2">
                                <span className="text-2xl font-bold text-indigo-600">{totalStudents}</span>
                                <span className="text-gray-600 ml-2">Total Students</span>
                            </div>
                        </>
                    ) : (
                        <NoDataMessage message="No student data yet" />
                    )}
                </div>

                {/* Subject Performance */}
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaChartBar className="text-orange-500" />
                        Average Score by Subject
                    </h2>
                    {subjectAnalytics.length > 0 ? (
                        <>
                            <div className="h-72">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={subjectAnalytics} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <YAxis dataKey="subject" type="category" width={100} tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <Tooltip formatter={(value) => [`${value}%`, 'Avg Score']} />
                                        <Bar dataKey="avgScore" radius={[0, 4, 4, 0]}>
                                            {subjectAnalytics.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.avgScore >= 80 ? '#22c55e' : entry.avgScore >= 70 ? '#f59e0b' : '#ef4444'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="flex justify-center gap-4 mt-2 text-xs">
                                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded"></span> ≥80%</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-500 rounded"></span> 70-79%</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded"></span> &lt;70%</span>
                            </div>
                        </>
                    ) : (
                        <NoDataMessage message="No quiz data yet. Students need to take quizzes." />
                    )}
                </div>
            </div>

            {/* Top Performers & Quiz Attempts */}
            <div className="grid lg:grid-cols-3 gap-6 mb-8">
                {/* Top Performers */}
                <div className="glass rounded-xl p-6 animate-fade-in">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaTrophy className="text-yellow-500" />
                        Top Performers
                    </h2>
                    {topPerformers.length > 0 ? (
                        <div className="space-y-3">
                            {topPerformers.map((student, idx) => (
                                <div key={idx} className={`flex items-center gap-3 p-3 rounded-lg ${idx === 0 ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200' : 'bg-gray-50'}`}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : 'bg-orange-400'}`}>
                                        {idx + 1}
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-medium text-gray-800">{student.name}</p>
                                        <p className="text-xs text-gray-500">Class {student.class} • {student.quizzes} quizzes</p>
                                    </div>
                                    <p className="font-bold text-green-600">{student.avgScore}%</p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <NoDataMessage message="No quiz results yet" />
                    )}
                </div>

                {/* Quiz Attempts Chart */}
                <div className="glass rounded-xl p-6 animate-fade-in lg:col-span-2">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <FaChartLine className="text-blue-500" />
                        Quiz Attempts by Subject
                    </h2>
                    {subjectAnalytics.length > 0 ? (
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={subjectAnalytics}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                    <XAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
                                    <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                                    <Tooltip />
                                    <Legend />
                                    <Bar dataKey="totalAttempts" name="Attempts" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <NoDataMessage message="No quiz attempts data" />
                    )}
                </div>
            </div>

            {/* Recent Activity */}
            <div className="glass rounded-xl p-6 animate-fade-in">
                <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <FaClock className="text-gray-500" />
                    Recent Activity
                </h2>
                {stats?.recent_activity?.length > 0 ? (
                    <div className="space-y-3">
                        {stats.recent_activity.map((activity, idx) => (
                            <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                                <FaComments className="text-blue-500" />
                                <div className="flex-1">
                                    <p className="text-gray-800 text-sm truncate">{activity.question}</p>
                                    <p className="text-xs text-gray-500">{new Date(activity.created_at).toLocaleString()}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500 text-center py-8">No recent activity</p>
                )}
            </div>
        </div>
    )
}

export default Admin
