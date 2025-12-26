import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    FaUsers, FaArrowLeft, FaSearch, FaGraduationCap, FaChartBar,
    FaBrain, FaComments, FaCalendar
} from 'react-icons/fa'
import { adminApi } from '../services/api'

function AdminStudents() {
    const [students, setStudents] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [search, setSearch] = useState('')
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)

    useEffect(() => {
        loadStudents()
    }, [page, search])

    const loadStudents = async () => {
        try {
            setLoading(true)
            const { data } = await adminApi.students(page, search)
            setStudents(data.students || [])
            setTotalPages(data.pages || 1)
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load students')
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = (e) => {
        e.preventDefault()
        setPage(1)
        loadStudents()
    }

    return (
        <div className="max-w-7xl mx-auto px-4">
            {/* Header */}
            <div className="mb-8 animate-fade-in">
                <Link to="/admin" className="text-indigo-600 hover:text-indigo-800 flex items-center gap-2 mb-4">
                    <FaArrowLeft /> Back to Dashboard
                </Link>
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    <FaUsers className="text-blue-500" />
                    Student Management
                </h1>
                <p className="text-gray-600">View and manage all registered students</p>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="mb-6">
                <div className="flex gap-2">
                    <div className="relative flex-1">
                        <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search by name, username, or email..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                    </div>
                    <button
                        type="submit"
                        className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
                    >
                        Search
                    </button>
                </div>
            </form>

            {/* Error State */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl mb-6">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {/* Loading State */}
            {loading ? (
                <div className="flex items-center justify-center min-h-[200px]">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-500 border-t-transparent"></div>
                </div>
            ) : students.length === 0 ? (
                /* Empty State */
                <div className="glass rounded-xl p-12 text-center">
                    <FaUsers className="text-6xl text-gray-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-600 mb-2">No Students Found</h3>
                    <p className="text-gray-500">
                        {search ? 'Try a different search term' : 'No students have registered yet'}
                    </p>
                </div>
            ) : (
                /* Students List */
                <div className="glass rounded-xl overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-600">Student</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-600">Class</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-600">Joined</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-600">Stats</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {students.map((student) => (
                                <tr key={student.id} className="hover:bg-gray-50 transition">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                                                {(student.full_name || student.username || 'S').charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-800">{student.full_name || student.username}</p>
                                                <p className="text-sm text-gray-500">{student.email || student.username}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                                            <FaGraduationCap />
                                            Class {student.grade || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="text-gray-600 flex items-center gap-2">
                                            <FaCalendar className="text-gray-400" />
                                            {student.created_at ? new Date(student.created_at).toLocaleDateString() : 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-4 text-sm text-gray-600">
                                            <span className="flex items-center gap-1">
                                                <FaBrain className="text-purple-500" />
                                                {student.quiz_count || 0} quizzes
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <FaComments className="text-blue-500" />
                                                {student.chat_count || 0} chats
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-6">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Previous
                    </button>
                    <span className="px-4 py-2 text-gray-600">
                        Page {page} of {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    )
}

export default AdminStudents
