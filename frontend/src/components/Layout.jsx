import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../services/authStore'
import { FaBook, FaRobot, FaBrain, FaChartBar, FaSignOutAlt, FaUser } from 'react-icons/fa'

function Layout() {
    const { user, isAuthenticated, logout } = useAuthStore()
    const location = useLocation()

    const navLinks = isAuthenticated ? [
        { to: '/dashboard', icon: <FaChartBar />, label: 'Dashboard' },
        { to: '/chat', icon: <FaRobot />, label: 'AI Tutor' },
        { to: '/quiz', icon: <FaBrain />, label: 'Quizzes' },
    ] : []

    return (
        <div className="min-h-screen flex flex-col">
            {/* Navigation */}
            <nav className="gradient-dark shadow-2xl sticky top-0 z-50 border-b border-slate-700/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo */}
                        <Link to="/" className="flex items-center space-x-3 group">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform">
                                <FaBook className="text-white" />
                            </div>
                            <span className="text-white text-xl font-bold group-hover:text-blue-300 transition-colors">
                                NCERT Learning
                            </span>
                        </Link>

                        {/* Nav Links */}
                        <div className="flex items-center space-x-2">
                            {navLinks.map(link => (
                                <Link
                                    key={link.to}
                                    to={link.to}
                                    className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2
                    ${location.pathname === link.to
                                            ? 'bg-white/20 text-white'
                                            : 'text-white/80 hover:bg-white/10 hover:text-white'
                                        }`}
                                >
                                    {link.icon}
                                    <span className="hidden sm:inline">{link.label}</span>
                                </Link>
                            ))}

                            {isAuthenticated ? (
                                <>
                                    {/* Only show username for non-admin users */}
                                    {user?.role !== 'super_admin' && (
                                        <div className="flex items-center px-4 py-2 bg-white/10 rounded-lg border border-white/20">
                                            <FaUser className="text-blue-300 mr-2" />
                                            <span className="text-white text-sm font-medium">{user?.full_name || user?.username || 'User'}</span>
                                        </div>
                                    )}
                                    <button
                                        onClick={logout}
                                        className="px-4 py-2 bg-gradient-to-r from-rose-500 to-red-600 hover:from-rose-600 hover:to-red-700 text-white rounded-lg transition-all shadow-lg flex items-center gap-2"
                                    >
                                        <FaSignOutAlt />
                                        <span className="hidden sm:inline">Logout</span>
                                    </button>
                                </>
                            ) : (
                                <>
                                    <Link
                                        to="/login"
                                        className="px-4 py-2 text-white hover:bg-white/10 rounded-lg transition-all"
                                    >
                                        Login
                                    </Link>
                                    <Link
                                        to="/register"
                                        className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white rounded-lg transition-all shadow-lg"
                                    >
                                        Register
                                    </Link>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="flex-1 py-8">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="gradient-dark text-white mt-16 border-t border-slate-700/50">
                <div className="max-w-7xl mx-auto px-4 py-8 text-center">
                    <div className="flex items-center justify-center space-x-2 mb-4">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-lg flex items-center justify-center">
                            <FaBook className="text-sm" />
                        </div>
                        <span className="text-lg font-bold">NCERT Learning</span>
                    </div>
                    <p className="text-slate-300 text-sm">
                        © 2024 NCERT Learning Platform. Empowering Education with AI.
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default Layout
