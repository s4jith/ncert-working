import { Link } from 'react-router-dom'
import { FaRobot, FaBrain, FaBook, FaGlobe, FaMicrophone, FaChartLine } from 'react-icons/fa'

function Home() {
    const features = [
        {
            icon: <FaRobot className="text-4xl text-indigo-500" />,
            title: 'AI Tutor',
            description: 'Ask any question about your NCERT curriculum and get instant, accurate answers with citations.',
        },
        {
            icon: <FaGlobe className="text-4xl text-green-500" />,
            title: 'Multilingual Support',
            description: 'Learn in Hindi, English, Urdu, and other regional languages.',
        },
        {
            icon: <FaBrain className="text-4xl text-purple-500" />,
            title: 'Smart Quizzes',
            description: 'Test your knowledge with AI-generated quizzes that adapt to your level.',
        },
        {
            icon: <FaMicrophone className="text-4xl text-rose-500" />,
            title: 'Voice Interaction',
            description: 'Speak your questions and hear the answers - perfect for hands-free learning.',
        },
    ]

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Hero Section */}
            <div className="text-center py-16 animate-fade-in">
                <div className="flex justify-center mb-6">
                    <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-2xl">
                        <FaBook className="text-4xl text-white" />
                    </div>
                </div>
                <h1 className="text-5xl font-bold text-gray-900 mb-4">
                    NCERT <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">Doubt-Solver</span>
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
                    Your AI-powered tutor for NCERT textbooks. Get instant answers, practice with quizzes,
                    and learn in multiple languages.
                </p>
                <div className="flex justify-center gap-4">
                    <Link
                        to="/register"
                        className="px-8 py-4 gradient-primary text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1"
                    >
                        Get Started Free
                    </Link>
                    <Link
                        to="/chat"
                        className="px-8 py-4 bg-white text-indigo-600 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all border-2 border-indigo-200 hover:border-indigo-300"
                    >
                        Try AI Tutor
                    </Link>
                </div>
            </div>

            {/* Features */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 py-16">
                {features.map((feature, idx) => (
                    <div
                        key={idx}
                        className="glass rounded-2xl p-6 card-hover animate-fade-in"
                        style={{ animationDelay: `${idx * 0.1}s` }}
                    >
                        <div className="mb-4">{feature.icon}</div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                        <p className="text-gray-600">{feature.description}</p>
                    </div>
                ))}
            </div>

            {/* Stats */}
            <div className="py-16 text-center">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                    {[
                        { value: '5-12', label: 'Grades Covered' },
                        { value: '8+', label: 'Subjects' },
                        { value: '5+', label: 'Languages' },
                        { value: '<5s', label: 'Response Time' },
                    ].map((stat, idx) => (
                        <div key={idx} className="animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
                            <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                                {stat.value}
                            </div>
                            <div className="text-gray-600">{stat.label}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Home
