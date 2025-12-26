import { useState, useEffect, useRef } from 'react'
import {
    FaBook, FaUpload, FaTrash, FaSync, FaCheckCircle,
    FaSpinner, FaExclamationTriangle, FaClock, FaSearch
} from 'react-icons/fa'
import { adminApi } from '../services/api'

const SUBJECTS = [
    'Mathematics', 'Science', 'Physics', 'Chemistry', 'Biology',
    'English', 'Hindi', 'Social Science', 'History', 'Geography',
    'Political Science', 'Economics', 'Sanskrit', 'Urdu'
]

const CLASSES = [5, 6, 7, 8, 9, 10, 11, 12]

function AdminBooks() {
    const [books, setBooks] = useState([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(null)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)
    const fileInputRef = useRef(null)

    // Form state
    const [formData, setFormData] = useState({
        classNum: '',
        subject: '',
        chapter: '',
        file: null
    })

    useEffect(() => {
        loadBooks()
    }, [])

    const loadBooks = async () => {
        try {
            setLoading(true)
            const { data } = await adminApi.books()
            setBooks(data.books || [])
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load books')
        } finally {
            setLoading(false)
        }
    }

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleFileChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            setFormData(prev => ({ ...prev, file }))
        }
    }

    const handleUpload = async (e) => {
        e.preventDefault()

        if (!formData.file || !formData.classNum || !formData.subject) {
            setError('Please fill all required fields')
            return
        }

        setUploading(true)
        setError(null)
        setSuccess(null)

        try {
            const form = new FormData()
            form.append('file', formData.file)
            form.append('class_num', formData.classNum)
            form.append('subject', formData.subject)
            if (formData.chapter) {
                form.append('chapter', formData.chapter)
            }

            const { data } = await adminApi.uploadBook(form)

            setSuccess(`Upload started! Processing ${formData.file.name}...`)
            setFormData({ classNum: '', subject: '', chapter: '', file: null })
            if (fileInputRef.current) fileInputRef.current.value = ''

            // Poll for status updates
            pollUploadStatus(data.upload_id)

            // Refresh book list
            setTimeout(loadBooks, 2000)

        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed')
        } finally {
            setUploading(false)
        }
    }

    const pollUploadStatus = async (uploadId) => {
        const checkStatus = async () => {
            try {
                const { data } = await adminApi.uploadStatus(uploadId)
                setUploadProgress(data)

                if (data.status === 'completed') {
                    setSuccess('Book processed successfully! Embeddings stored in Pinecone.')
                    setUploadProgress(null)
                    loadBooks()
                } else if (data.status === 'failed') {
                    setError(`Processing failed: ${data.error_message}`)
                    setUploadProgress(null)
                } else {
                    // Continue polling
                    setTimeout(checkStatus, 2000)
                }
            } catch (err) {
                console.error('Failed to check status:', err)
            }
        }

        checkStatus()
    }

    const handleDelete = async (bookId, filename) => {
        if (!window.confirm(`Delete "${filename}"? This will also remove all embeddings from Pinecone.`)) {
            return
        }

        try {
            await adminApi.deleteBook(bookId)
            setSuccess(`Deleted: ${filename}`)
            loadBooks()
        } catch (err) {
            setError(err.response?.data?.detail || 'Delete failed')
        }
    }

    const getStatusBadge = (status) => {
        const badges = {
            pending: { icon: <FaClock />, class: 'bg-yellow-100 text-yellow-800', text: 'Pending' },
            processing: { icon: <FaSpinner className="animate-spin" />, class: 'bg-blue-100 text-blue-800', text: 'Processing' },
            completed: { icon: <FaCheckCircle />, class: 'bg-green-100 text-green-800', text: 'Completed' },
            failed: { icon: <FaExclamationTriangle />, class: 'bg-red-100 text-red-800', text: 'Failed' }
        }
        const badge = badges[status] || badges.pending
        return (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.class}`}>
                {badge.icon} {badge.text}
            </span>
        )
    }

    return (
        <div className="max-w-6xl mx-auto px-4">
            {/* Header */}
            <div className="mb-6 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    <FaBook className="text-orange-500" />
                    Book Management
                </h1>
                <p className="text-gray-600">Upload NCERT PDFs and manage content embeddings</p>
            </div>

            {/* Alerts */}
            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl animate-fade-in flex items-center gap-2">
                    <FaExclamationTriangle />
                    {error}
                    <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">×</button>
                </div>
            )}

            {success && (
                <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl animate-fade-in flex items-center gap-2">
                    <FaCheckCircle />
                    {success}
                    <button onClick={() => setSuccess(null)} className="ml-auto text-green-500 hover:text-green-700">×</button>
                </div>
            )}

            {/* Upload Progress */}
            {uploadProgress && (
                <div className="mb-4 bg-blue-50 border border-blue-200 px-4 py-3 rounded-xl animate-fade-in">
                    <div className="flex items-center gap-2 text-blue-700 mb-2">
                        <FaSpinner className="animate-spin" />
                        Processing: {uploadProgress.progress_percent}%
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${uploadProgress.progress_percent}%` }}
                        ></div>
                    </div>
                    <p className="text-sm text-blue-600 mt-1">
                        Chunks: {uploadProgress.chunks_processed} / {uploadProgress.total_chunks || '?'}
                    </p>
                </div>
            )}

            {/* Upload Form */}
            <div className="glass rounded-xl p-6 mb-8 animate-fade-in">
                <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <FaUpload className="text-indigo-500" />
                    Upload New Book
                </h2>

                <form onSubmit={handleUpload} className="space-y-4">
                    <div className="grid md:grid-cols-3 gap-4">
                        {/* Class Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Class *</label>
                            <select
                                name="classNum"
                                value={formData.classNum}
                                onChange={handleInputChange}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                                required
                            >
                                <option value="">Select Class</option>
                                {CLASSES.map(c => (
                                    <option key={c} value={c}>Class {c}</option>
                                ))}
                            </select>
                        </div>

                        {/* Subject Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
                            <select
                                name="subject"
                                value={formData.subject}
                                onChange={handleInputChange}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                                required
                            >
                                <option value="">Select Subject</option>
                                {SUBJECTS.map(s => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </select>
                        </div>

                        {/* Chapter Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Chapter (Optional)</label>
                            <input
                                type="text"
                                name="chapter"
                                value={formData.chapter}
                                onChange={handleInputChange}
                                placeholder="e.g., Chapter 1 - Introduction"
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                    </div>

                    {/* File Input */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">PDF File *</label>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                            required
                        />
                        <p className="text-xs text-gray-500 mt-1">Maximum file size: 50MB</p>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={uploading}
                        className="w-full md:w-auto px-6 py-3 gradient-primary text-white font-semibold rounded-xl hover:opacity-90 transition disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {uploading ? (
                            <>
                                <FaSpinner className="animate-spin" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <FaUpload />
                                Upload & Process
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Books List */}
            <div className="glass rounded-xl p-6 animate-fade-in">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <FaBook className="text-orange-500" />
                        Uploaded Books ({books.length})
                    </h2>
                    <button
                        onClick={loadBooks}
                        className="p-2 text-gray-500 hover:text-indigo-600 transition"
                        title="Refresh"
                    >
                        <FaSync className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>

                {loading ? (
                    <div className="flex justify-center py-12">
                        <FaSpinner className="animate-spin text-3xl text-indigo-500" />
                    </div>
                ) : books.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Filename</th>
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Class</th>
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Subject</th>
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Status</th>
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Chunks</th>
                                    <th className="text-left py-3 px-2 text-sm font-medium text-gray-600">Date</th>
                                    <th className="text-center py-3 px-2 text-sm font-medium text-gray-600">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {books.map((book, idx) => (
                                    <tr key={book.id} className="border-b hover:bg-gray-50 animate-fade-in" style={{ animationDelay: `${idx * 0.05}s` }}>
                                        <td className="py-3 px-2">
                                            <span className="font-medium text-gray-800 truncate block max-w-[200px]" title={book.filename}>
                                                {book.filename}
                                            </span>
                                        </td>
                                        <td className="py-3 px-2 text-gray-600">Class {book.class_num}</td>
                                        <td className="py-3 px-2 text-gray-600">{book.subject}</td>
                                        <td className="py-3 px-2">{getStatusBadge(book.status)}</td>
                                        <td className="py-3 px-2 text-gray-600">{book.chunks_count || 0}</td>
                                        <td className="py-3 px-2 text-gray-500 text-sm">
                                            {new Date(book.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="py-3 px-2 text-center">
                                            <button
                                                onClick={() => handleDelete(book.id, book.filename)}
                                                className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition"
                                                title="Delete book and embeddings"
                                            >
                                                <FaTrash />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <FaBook className="text-4xl mx-auto mb-3 opacity-50" />
                        <p>No books uploaded yet</p>
                        <p className="text-sm">Upload your first NCERT PDF to get started</p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default AdminBooks
