import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { userStatsService } from "../../services/api";
import useUserStore from "../../stores/userStore";

/**
 * ProgressCard Component
 * 
 * Displays test progress with circular progress chart.
 * Fetches real data from MongoDB via backend API.
 */

export default function ProgressCard() {
  const { user } = useUserStore();
  const [progressData, setProgressData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProgressData = async () => {
      const studentId = user.id || "guest";

      try {
        setLoading(true);
        const data = await userStatsService.getProgressData(studentId, user.preferredSubject);
        setProgressData(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch progress data:", err);
        setError(err.message);
        // Use fallback data on error
        setProgressData({
          overall_progress: 0,
          total_tests: 10,
          completed_tests: 0,
          average_score: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchProgressData();
  }, [user.id, user.preferredSubject]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  const progress = progressData?.overall_progress || 0;
  const totalTests = progressData?.total_tests || 10;
  const completedTests = progressData?.completed_tests || 0;
  const averageScore = progressData?.average_score || 0;

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Progress</h3>
      
      <div className="flex items-center gap-6">
        {/* Circular Progress */}
        <div className="relative">
          <svg className="w-28 h-28 transform -rotate-90">
            <circle
              cx="56"
              cy="56"
              r="45"
              stroke="#f3f4f6"
              strokeWidth="10"
              fill="none"
            />
            <circle
              cx="56"
              cy="56"
              r="45"
              stroke="#f928a9"
              strokeWidth="10"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-gray-800">{progress}%</span>
          </div>
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Tests Completed</span>
            <span className="font-semibold text-gray-800">{completedTests}/{totalTests}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div 
              className="bg-pink-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(completedTests / totalTests) * 100}%` }}
            />
          </div>
          {averageScore > 0 && (
            <div className="flex justify-between text-sm mt-2">
              <span className="text-gray-500">Average Score</span>
              <span className="font-semibold text-gray-800">{averageScore}%</span>
            </div>
          )}
          <p className="text-xs text-gray-400 mt-2">
            {progress > 50 ? "Great work! Keep it up!" : "Keep going! You're making progress."}
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-amber-500 mt-2 text-center">
          Using offline data
        </p>
      )}
    </div>
  );
}
