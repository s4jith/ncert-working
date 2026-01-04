import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import useUserStore from "../stores/userStore";
import {
  Clock,
  ChevronLeft,
  ChevronRight,
  Send,
  Mic,
  MicOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  BookOpen,
  Target
} from "lucide-react";
import { Button } from "../components/ui/button";
import { testService } from "../services/api";

/**
 * TestSession Page
 * 
 * Handles the actual test-taking experience:
 * - Display questions one at a time
 * - Voice/text input for answers
 * - Submit answers
 * - Complete test and get evaluation
 */

export default function TestSession() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useUserStore();

  // Get session data from navigation state
  const { session: initialSession, testConfig } = location.state || {};

  const [session, setSession] = useState(initialSession);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [isLoading, setIsLoading] = useState(!initialSession);
  const [error, setError] = useState(null);

  // Voice recognition
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    const initSession = async () => {
      if (session) return;

      if (!testConfig) {
        navigate("/test-center");
        return;
      }

      try {
        setIsLoading(true);
        const newSession = await testService.startTestV2({
          ...testConfig,
          studentId: user?.id || user?.sub || "guest",
          auto_generate: true
        });
        setSession(newSession);
        setTimeRemaining(newSession.time_limit_minutes * 60);
      } catch (err) {
        console.error("Failed to start test:", err);
        setError("Failed to start test session. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    initSession();
  }, [initialSession, testConfig, navigate]);

  useEffect(() => {
    if (!session) return;

    // Set initial time if not set
    if (timeRemaining === 0 && session.time_limit_minutes) {
      setTimeRemaining(session.time_limit_minutes * 60);
    }

    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-IN';

      rec.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setCurrentAnswer(prev => prev + ' ' + transcript);
      };

      rec.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      rec.onend = () => {
        setIsRecording(false);
      };

      setRecognition(rec);
    }
  }, [session]);

  // Timer
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Auto-submit when time runs out
          handleCompleteTest();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const currentQuestion = session?.questions?.[currentQuestionIndex];

  const toggleRecording = () => {
    if (!recognition) return;

    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
      setIsRecording(true);
    }
  };

  const handleSaveAnswer = async () => {
    if (!currentAnswer.trim() || !currentQuestion) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await testService.submitAnswer(
        session.session_id,
        currentQuestion.question_id,
        currentQuestion.question_number,
        currentAnswer.trim()
      );

      // Save locally
      setAnswers(prev => ({
        ...prev,
        [currentQuestion.question_id]: currentAnswer.trim()
      }));

      // Move to next question if not last
      if (currentQuestionIndex < session.questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setCurrentAnswer(answers[session.questions[currentQuestionIndex + 1]?.question_id] || "");
      }
    } catch (err) {
      console.error("Failed to save answer:", err);
      setError("Failed to save answer. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNavigate = (direction) => {
    // Save current answer before navigating
    if (currentAnswer.trim() && currentQuestion) {
      setAnswers(prev => ({
        ...prev,
        [currentQuestion.question_id]: currentAnswer.trim()
      }));
    }

    const newIndex = direction === 'next'
      ? Math.min(currentQuestionIndex + 1, session.questions.length - 1)
      : Math.max(currentQuestionIndex - 1, 0);

    setCurrentQuestionIndex(newIndex);
    setCurrentAnswer(answers[session.questions[newIndex]?.question_id] || "");
  };

  const handleCompleteTest = async () => {
    // Save current answer first
    if (currentAnswer.trim() && currentQuestion) {
      try {
        await testService.submitAnswer(
          session.session_id,
          currentQuestion.question_id,
          currentQuestion.question_number,
          currentAnswer.trim()
        );
      } catch (err) {
        console.error("Failed to save final answer:", err);
      }
    }

    setIsCompleting(true);
    setError(null);

    try {
      const result = await testService.completeTest(session.session_id, user.id);

      // Navigate to results page
      navigate("/test-result", {
        state: {
          result,
          topicConfig
        }
      });
    } catch (err) {
      console.error("Failed to complete test:", err);
      setError("Failed to complete test. Please try again.");
      setIsCompleting(false);
    }
  };

  const answeredCount = Object.keys(answers).length + (currentAnswer.trim() ? 1 : 0);

  if (!session) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[50vh]">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Target className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h2 className="font-semibold text-gray-800">{session.topic_name}</h2>
                <p className="text-sm text-gray-500">
                  {testConfig?.subject} • Chapter {testConfig?.chapter_number}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Timer */}
              <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${timeRemaining < 60 ? "bg-red-100 text-red-600" : "bg-gray-100 text-gray-700"
                }`}>
                <Clock className="w-4 h-4" />
                <span className="font-mono font-semibold">{formatTime(timeRemaining)}</span>
              </div>

              {/* Progress */}
              <div className="text-sm text-gray-500">
                <span className="font-semibold text-gray-800">{answeredCount}</span>
                /{session.questions.length} answered
              </div>
            </div>
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          {/* Question Header */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-purple-600">
                Question {currentQuestionIndex + 1} of {session.questions.length}
              </span>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${currentQuestion?.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                  currentQuestion?.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                  {currentQuestion?.difficulty}
                </span>
                <span className="text-sm text-gray-500">
                  {currentQuestion?.marks} marks
                </span>
              </div>
            </div>
          </div>

          {/* Question Text */}
          <div className="p-6">
            <p className="text-lg text-gray-800 leading-relaxed">
              {currentQuestion?.question_text}
            </p>
          </div>

          {/* Answer Input */}
          <div className="p-6 pt-0">
            <div className="space-y-4">
              <label className="text-sm font-medium text-gray-700">Your Answer:</label>
              <div className="relative">
                <textarea
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  placeholder="Type your answer here or use voice input..."
                  className="w-full h-40 p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />

                {/* Voice Input Button */}
                {recognition && (
                  <button
                    onClick={toggleRecording}
                    className={`absolute bottom-4 right-4 p-3 rounded-full transition-all ${isRecording
                      ? "bg-red-500 text-white animate-pulse"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    title={isRecording ? "Stop recording" : "Start voice input"}
                  >
                    {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  </button>
                )}
              </div>

              {isRecording && (
                <p className="text-sm text-red-600 flex items-center gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  Recording... Speak now
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-6 pb-4">
              <div className="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-2 rounded-lg">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
            <Button
              variant="outline"
              onClick={() => handleNavigate('prev')}
              disabled={currentQuestionIndex === 0}
              className="gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>

            <div className="flex items-center gap-2">
              <Button
                onClick={handleSaveAnswer}
                disabled={!currentAnswer.trim() || isSubmitting}
                className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                Save Answer
              </Button>

              {currentQuestionIndex === session.questions.length - 1 ? (
                <Button
                  onClick={handleCompleteTest}
                  disabled={isCompleting}
                  className="bg-green-600 hover:bg-green-700 text-white gap-2"
                >
                  {isCompleting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  Complete Test
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => handleNavigate('next')}
                  className="gap-2"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Question Navigator */}
        <div className="mt-6 bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Questions Overview</h4>
          <div className="flex flex-wrap gap-2">
            {session.questions.map((q, index) => {
              const isAnswered = !!answers[q.question_id] || (index === currentQuestionIndex && currentAnswer.trim());
              const isCurrent = index === currentQuestionIndex;

              return (
                <button
                  key={q.question_id}
                  onClick={() => {
                    if (currentAnswer.trim() && currentQuestion) {
                      setAnswers(prev => ({
                        ...prev,
                        [currentQuestion.question_id]: currentAnswer.trim()
                      }));
                    }
                    setCurrentQuestionIndex(index);
                    setCurrentAnswer(answers[q.question_id] || "");
                  }}
                  className={`w-10 h-10 rounded-lg font-medium transition-all ${isCurrent
                    ? "bg-purple-600 text-white"
                    : isAnswered
                      ? "bg-green-100 text-green-700 border border-green-200"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
