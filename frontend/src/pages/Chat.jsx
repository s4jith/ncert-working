import { useState, useRef, useEffect } from 'react'
import { FaPaperPlane, FaRobot, FaUser, FaBook, FaGraduationCap } from 'react-icons/fa'
import ReactMarkdown from 'react-markdown'
import { chatApi } from '../services/api'
import { useAuthStore } from '../services/authStore'

function Chat() {
    const { user } = useAuthStore()
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: `Hello${user?.full_name ? `, ${user.full_name}` : ''}! I'm your AI tutor. Ask me anything about your NCERT subjects like Mathematics, Science, Social Studies, and more. I'm here to help you learn!`,
            sources: [],
        }
    ])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setIsLoading(true)

        try {
            const { data } = await chatApi.send({
                message: input,
                model: 'gemini',  // Default to Gemini
                grade: user?.grade ? parseInt(user.grade) : null,  // Use user's grade from login
            })

            const assistantMessage = {
                role: 'assistant',
                content: data.message,
                sources: data.sources || [],
                responseTime: data.response_time_ms,
            }
            setMessages(prev => [...prev, assistantMessage])
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                error: true,
            }])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="max-w-4xl mx-auto px-4">
            {/* Header */}
            <div className="mb-6 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    <FaRobot className="text-indigo-500" />
                    AI Tutor
                </h1>
                <p className="text-gray-600 flex items-center gap-2">
                    Ask any question about your NCERT curriculum
                    {user?.grade && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                            <FaGraduationCap /> Class {user.grade}
                        </span>
                    )}
                </p>
            </div>

            {/* Chat Container */}
            <div className="glass rounded-xl overflow-hidden animate-fade-in">
                {/* Messages */}
                <div className="h-[500px] overflow-y-auto p-6 space-y-4 bg-slate-50/50">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex gap-3 animate-fade-in ${msg.role === 'user' ? 'justify-end' : ''}`}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-white flex-shrink-0">
                                    <FaRobot />
                                </div>
                            )}
                            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                                <div className={`rounded-xl shadow p-4 ${msg.role === 'user'
                                    ? 'bg-indigo-100'
                                    : msg.error ? 'bg-red-50' : 'bg-white'
                                    }`}>
                                    <ReactMarkdown className="prose prose-sm max-w-none">
                                        {msg.content}
                                    </ReactMarkdown>

                                    {/* Sources */}
                                    {msg.sources?.length > 0 && (
                                        <div className="mt-4 pt-3 border-t">
                                            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                                                <FaBook className="text-green-500" />
                                                Sources
                                            </div>
                                            <div className="space-y-2">
                                                {msg.sources.map((src, i) => (
                                                    <div key={i} className="bg-gray-50 rounded-lg p-2 text-sm">
                                                        <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded mr-2">
                                                            📚 NCERT
                                                        </span>
                                                        <span className="font-medium">{src.name}</span>
                                                        <span className="text-gray-500 ml-2">
                                                            {src.class} • {src.relevance}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <p className="text-xs text-gray-500 mt-1">
                                    {msg.role === 'user' ? 'You' : 'AI Tutor'}
                                    {msg.responseTime && ` • ${msg.responseTime}ms`}
                                </p>
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center text-white flex-shrink-0">
                                    <FaUser />
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Typing Indicator */}
                    {isLoading && (
                        <div className="flex gap-3 animate-fade-in">
                            <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-white">
                                <FaRobot />
                            </div>
                            <div className="bg-white rounded-xl shadow p-4">
                                <div className="animate-typing flex gap-1">
                                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t bg-white">
                    <form onSubmit={sendMessage} className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask your question here..."
                            className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="px-6 py-3 gradient-primary text-white rounded-xl font-semibold hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
                        >
                            <FaPaperPlane />
                            Send
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}

export default Chat
