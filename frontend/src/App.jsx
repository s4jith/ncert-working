import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './services/authStore'
import Layout from './components/Layout'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Quiz from './pages/Quiz'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import Admin from './pages/Admin'
import AdminBooks from './pages/AdminBooks'
import AdminStudents from './pages/AdminStudents'

function ProtectedRoute({ children }) {
    const { isAuthenticated } = useAuthStore()
    return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
    const { isAuthenticated, user } = useAuthStore()
    if (!isAuthenticated) return <Navigate to="/login" replace />
    if (user?.role !== 'super_admin') {
        return (
            <div className="max-w-lg mx-auto px-4 py-20 text-center">
                <div className="text-6xl mb-4">🔒</div>
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Access Denied</h1>
                <p className="text-gray-600">You need administrator privileges to access this page.</p>
            </div>
        )
    }
    return children
}

// Dashboard component that shows different content based on user role
function SmartDashboard() {
    const { user } = useAuthStore()
    // Show Admin dashboard for super_admin, student dashboard for others
    return user?.role === 'super_admin' ? <Admin /> : <Dashboard />
}

function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="login" element={<Login />} />
                <Route path="register" element={<Register />} />
                <Route path="chat" element={
                    <ProtectedRoute><Chat /></ProtectedRoute>
                } />
                <Route path="quiz" element={
                    <ProtectedRoute><Quiz /></ProtectedRoute>
                } />
                <Route path="dashboard" element={
                    <ProtectedRoute><SmartDashboard /></ProtectedRoute>
                } />
                {/* Admin Routes */}
                <Route path="admin" element={
                    <AdminRoute><Admin /></AdminRoute>
                } />
                <Route path="admin/books" element={
                    <AdminRoute><AdminBooks /></AdminRoute>
                } />
                <Route path="admin/students" element={
                    <AdminRoute><AdminStudents /></AdminRoute>
                } />
            </Route>
        </Routes>
    )
}

export default App
