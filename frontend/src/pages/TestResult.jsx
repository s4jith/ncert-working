import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import { 
  Trophy, 
  Target, 
  CheckCircle, 
  XCircle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  TrendingUp,
  AlertTriangle,
  Home,
  RotateCcw,
  Award
} from "lucide-react";
import { Button } from "../components/ui/button";

/**
 * TestResult Page
 * 
 * Shows the AI evaluation results after completing a test:
 * - Overall score
 * - Question-by-question evaluation
 * - Strengths and areas for improvement
 * - Topics to review
 */

export default function TestResult() {
  const navigate = useNavigate();
  const location = useLocation();
  const { result, topicConfig } = location.state || {};
  
  const [expandedQuestions, setExpandedQuestions] = useState({});

  if (!result) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
          <AlertTriangle className="w-12 h-12 text-amber-500" />
          <h2 className="text-xl font-semibold text-gray-800">No Results Found</h2>
          <p className="text-gray-500">Please complete a test first.</p>
          <Button onClick={() => navigate("/test-center")} className="gap-2">
            <Home className="w-4 h-4" />
            Go to Test Center
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  const toggleQuestion = (questionId) => {
    setExpandedQuestions(prev => ({
      ...prev,
      [questionId]: !prev[questionId]
    }));
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return "from-green-500 to-emerald-500";
    if (score >= 60) return "from-yellow-500 to-amber-500";
    return "from-red-500 to-orange-500";
  };

  const getScoreMessage = (score) => {
    if (score >= 90) return "Outstanding! 🌟";
    if (score >= 80) return "Excellent Work! 🎉";
    if (score >= 70) return "Good Job! 👍";
    if (score >= 60) return "Keep Practicing! 💪";
    if (score >= 50) return "Needs Improvement 📚";
    return "More Practice Required 📖";
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Score Card */}
        <div className={`bg-gradient-to-r ${getScoreBgColor(result.score)} rounded-2xl p-8 text-white`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Trophy className="w-8 h-8" />
                <h1 className="text-2xl font-bold">Test Complete!</h1>
              </div>
              <p className="text-white/80 mb-4">
                {topicConfig?.topic_name || result.topic_name || "Topic Test"}
              </p>
              <p className="text-xl font-medium">{getScoreMessage(result.score)}</p>
            </div>
            <div className="text-center">
              <div className="text-6xl font-bold">{Math.round(result.score)}%</div>
              <p className="text-white/80 mt-2">
                {result.correct_answers}/{result.total_questions} correct
              </p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 text-green-600 mb-2">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Correct</span>
            </div>
            <p className="text-2xl font-bold text-gray-800">{result.correct_answers}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 text-red-600 mb-2">
              <XCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Incorrect</span>
            </div>
            <p className="text-2xl font-bold text-gray-800">
              {result.total_questions - result.correct_answers}
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 text-purple-600 mb-2">
              <Target className="w-5 h-5" />
              <span className="text-sm font-medium">Questions</span>
            </div>
            <p className="text-2xl font-bold text-gray-800">{result.total_questions}</p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 text-blue-600 mb-2">
              <Award className="w-5 h-5" />
              <span className="text-sm font-medium">Score</span>
            </div>
            <p className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
              {Math.round(result.score)}%
            </p>
          </div>
        </div>

        {/* Feedback */}
        {result.feedback && (
          <div className="bg-white rounded-2xl p-6 border border-gray-100">
            <h3 className="font-semibold text-gray-800 mb-3">Overall Feedback</h3>
            <p className="text-gray-600">{result.feedback}</p>
          </div>
        )}

        {/* Strengths & Improvements */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.strengths?.length > 0 && (
            <div className="bg-green-50 rounded-2xl p-6 border border-green-100">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold text-green-800">Strengths</h3>
              </div>
              <ul className="space-y-2">
                {result.strengths.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-green-700">
                    <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {result.improvements?.length > 0 && (
            <div className="bg-amber-50 rounded-2xl p-6 border border-amber-100">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-amber-800">Areas to Improve</h3>
              </div>
              <ul className="space-y-2">
                {result.improvements.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-amber-700">
                    <Target className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Topics to Review */}
        {result.topics_to_review?.length > 0 && (
          <div className="bg-blue-50 rounded-2xl p-6 border border-blue-100">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-blue-800">Topics to Review</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {result.topics_to_review.map((topic, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Question-by-Question Evaluation */}
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-800">Question-by-Question Review</h3>
          </div>
          <div className="divide-y divide-gray-100">
            {result.evaluations?.map((evaluation, index) => (
              <div key={evaluation.question_id || index} className="p-4">
                <button
                  onClick={() => toggleQuestion(evaluation.question_id || index)}
                  className="w-full flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      evaluation.is_correct 
                        ? "bg-green-100 text-green-600" 
                        : "bg-red-100 text-red-600"
                    }`}>
                      {evaluation.is_correct ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <span className="font-medium text-gray-800">Question {index + 1}</span>
                      <span className="ml-2 text-sm text-gray-500">
                        ({evaluation.score}/{evaluation.max_score} marks)
                      </span>
                    </div>
                  </div>
                  {expandedQuestions[evaluation.question_id || index] ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </button>
                
                {expandedQuestions[evaluation.question_id || index] && (
                  <div className="mt-4 pl-11 space-y-4">
                    <div>
                      <p className="text-sm font-medium text-gray-500 mb-1">Question:</p>
                      <p className="text-gray-800">{evaluation.question_text}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500 mb-1">Your Answer:</p>
                      <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                        {evaluation.student_answer || "No answer provided"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500 mb-1">Correct Answer:</p>
                      <p className="text-green-700 bg-green-50 p-3 rounded-lg">
                        {evaluation.correct_answer}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500 mb-1">Feedback:</p>
                      <p className="text-gray-600 bg-blue-50 p-3 rounded-lg">
                        {evaluation.feedback}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between gap-4">
          <Button
            variant="outline"
            onClick={() => navigate("/test-center")}
            className="gap-2"
          >
            <Home className="w-4 h-4" />
            Back to Test Center
          </Button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate("/report-card")}
              className="gap-2"
            >
              <Award className="w-4 h-4" />
              View All Reports
            </Button>
            <Button
              onClick={() => navigate("/test-center")}
              className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Take Another Test
            </Button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
