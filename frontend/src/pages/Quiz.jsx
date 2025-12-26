import { useState, useEffect } from 'react'
import { FaBrain, FaCheck, FaTimes, FaClock, FaTrophy } from 'react-icons/fa'
import { quizApi } from '../services/api'

function Quiz() {
    const [chapters, setChapters] = useState([])
    const [selectedChapter, setSelectedChapter] = useState(null)
    const [questions, setQuestions] = useState([])
    const [currentQ, setCurrentQ] = useState(0)
    const [answers, setAnswers] = useState({})
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [grade, setGrade] = useState('')

    useEffect(() => {
        loadChapters()
    }, [grade])

    const loadChapters = async () => {
        try {
            const { data } = await quizApi.chapters(grade || null)
            setChapters(data.chapters || [])
        } catch (err) {
            console.error('Failed to load chapters')
        }
    }

    const startQuiz = async (chapter) => {
        setLoading(true)
        try {
            const { data } = await quizApi.questions(chapter.chapter_id)
            setQuestions(data.questions || [])
            setSelectedChapter(chapter)
            setCurrentQ(0)
            setAnswers({})
            setResult(null)
        } catch (err) {
            console.error('Failed to load questions')
        } finally {
            setLoading(false)
        }
    }

    const selectAnswer = (questionId, answerIdx) => {
        setAnswers(prev => ({ ...prev, [questionId]: answerIdx }))
    }

    const submitQuiz = async () => {
        setLoading(true)
        try {
            const submission = {
                quiz_id: selectedChapter.chapter_id,
                answers: questions.map(q => ({
                    question_id: q.id,
                    selected_answer: answers[q.id] ?? -1,
                    time_taken_seconds: 30,
                }))
            }
            const { data } = await quizApi.submit(submission)
            setResult(data)
        } catch (err) {
            console.error('Failed to submit quiz')
        } finally {
            setLoading(false)
        }
    }

    // Result view
    if (result) {
        return (
            <div className="max-w-2xl mx-auto px-4">
                <div className="glass rounded-2xl p-8 text-center animate-fade-in">
                    <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-4 ${result.passed ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                        <FaTrophy className={`text-4xl ${result.passed ? 'text-green-500' : 'text-red-500'}`} />
                    </div>
                    <h2 className="text-3xl font-bold mb-2">
                        {result.passed ? 'Congratulations!' : 'Keep Practicing!'}
                    </h2>
                    <p className="text-gray-600 mb-6">You scored {result.score} out of {result.total_questions}</p>

                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-indigo-50 rounded-xl p-4">
                            <div className="text-2xl font-bold text-indigo-600">{result.percentage.toFixed(0)}%</div>
                            <div className="text-sm text-gray-600">Score</div>
                        </div>
                        <div className="bg-green-50 rounded-xl p-4">
                            <div className="text-2xl font-bold text-green-600">{result.score}</div>
                            <div className="text-sm text-gray-600">Correct</div>
                        </div>
                        <div className="bg-orange-50 rounded-xl p-4">
                            <div className="text-2xl font-bold text-orange-600">{Math.floor(result.time_taken_seconds / 60)}m</div>
                            <div className="text-sm text-gray-600">Time</div>
                        </div>
                    </div>

                    <button
                        onClick={() => { setResult(null); setSelectedChapter(null); }}
                        className="px-6 py-3 gradient-primary text-white rounded-xl font-semibold"
                    >
                        Try Another Quiz
                    </button>
                </div>
            </div>
        )
    }

    // Quiz in progress
    if (selectedChapter && questions.length > 0) {
        const question = questions[currentQ]
        return (
            <div className="max-w-3xl mx-auto px-4">
                <div className="glass rounded-2xl p-6 animate-fade-in">
                    {/* Progress */}
                    <div className="flex justify-between items-center mb-6">
                        <span className="text-sm font-medium text-gray-600">
                            Question {currentQ + 1} of {questions.length}
                        </span>
                        <div className="flex gap-1">
                            {questions.map((_, i) => (
                                <div
                                    key={i}
                                    className={`w-3 h-3 rounded-full ${i === currentQ ? 'bg-indigo-500' :
                                            answers[questions[i]?.id] !== undefined ? 'bg-green-400' : 'bg-gray-200'
                                        }`}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Question */}
                    <h2 className="text-xl font-semibold text-gray-800 mb-6">{question.question}</h2>

                    {/* Options */}
                    <div className="space-y-3 mb-6">
                        {question.options.map((opt, i) => (
                            <button
                                key={i}
                                onClick={() => selectAnswer(question.id, i)}
                                className={`w-full text-left p-4 rounded-xl border-2 transition-all ${answers[question.id] === i
                                        ? 'border-indigo-500 bg-indigo-50'
                                        : 'border-gray-200 hover:border-indigo-300'
                                    }`}
                            >
                                <span className="font-medium mr-3">{String.fromCharCode(65 + i)}.</span>
                                {opt}
                            </button>
                        ))}
                    </div>

                    {/* Navigation */}
                    <div className="flex justify-between">
                        <button
                            onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
                            disabled={currentQ === 0}
                            className="px-4 py-2 border rounded-lg disabled:opacity-50"
                        >
                            Previous
                        </button>
                        {currentQ === questions.length - 1 ? (
                            <button
                                onClick={submitQuiz}
                                disabled={loading}
                                className="px-6 py-2 gradient-primary text-white rounded-lg font-semibold"
                            >
                                Submit Quiz
                            </button>
                        ) : (
                            <button
                                onClick={() => setCurrentQ(currentQ + 1)}
                                className="px-4 py-2 gradient-primary text-white rounded-lg"
                            >
                                Next
                            </button>
                        )}
                    </div>
                </div>
            </div>
        )
    }

    // Chapter selection
    return (
        <div className="max-w-4xl mx-auto px-4">
            <div className="mb-6 animate-fade-in">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    <FaBrain className="text-purple-500" />
                    Quiz Practice
                </h1>
                <p className="text-gray-600">Select a chapter to start practicing</p>
            </div>

            <div className="glass rounded-xl p-4 mb-6">
                <label className="text-sm font-medium text-gray-700 mr-4">Filter by Grade:</label>
                <select
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                    className="px-3 py-2 border rounded-lg"
                >
                    <option value="">All Grades</option>
                    {[5, 6, 7, 8, 9, 10, 11, 12].map(g => (
                        <option key={g} value={g}>Class {g}</option>
                    ))}
                </select>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
                {chapters.map((ch, idx) => (
                    <div
                        key={ch.id}
                        className="glass rounded-xl p-6 card-hover cursor-pointer animate-fade-in"
                        style={{ animationDelay: `${idx * 0.05}s` }}
                        onClick={() => startQuiz(ch)}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="font-semibold text-gray-800">{ch.chapter_name}</h3>
                            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                                {ch.total_questions} Qs
                            </span>
                        </div>
                        <p className="text-sm text-gray-600">
                            Class {ch.class_num} • {ch.subject}
                        </p>
                    </div>
                ))}
                {chapters.length === 0 && (
                    <div className="col-span-2 text-center py-12 text-gray-500">
                        No quiz chapters available. Upload NCERT books first.
                    </div>
                )}
            </div>
        </div>
    )
}

export default Quiz
