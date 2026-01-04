import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import useUserStore from "../stores/userStore";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Target, 
  Award, 
  BookOpen,
  Brain,
  AlertTriangle,
  CheckCircle,
  Zap,
  BarChart3,
  Home,
  Calendar,
  Trophy,
  Flame
} from "lucide-react";
import { Button } from "../components/ui/button";
import { testService } from "../services/api";

export default function ReportCard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, [user.id, user.classLevel, user.preferredSubject]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await testService.getTestAnalytics(
        user.id,
        user.classLevel || 10,
        user.preferredSubject
      );
      
      if (data) {
        setAnalytics(data);
      } else {
        setError("No test data available");
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      setError("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score) => {
    if (score >= 80) return "bg-green-50 border-green-200";
    if (score >= 60) return "bg-yellow-50 border-yellow-200";
    return "bg-red-50 border-red-200";
  };

  const getTrendIcon = (trend) => {
    if (trend === "improving") return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === "declining") return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getPerformanceLevel = (score) => {
    if (score >= 80) return { label: "Excellent", color: "green", icon: Trophy };
    if (score >= 60) return { label: "Good", color: "yellow", icon: Target };
    return { label: "Needs Practice", color: "red", icon: AlertTriangle };
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto" />
            <p className="text-gray-500">Loading your performance data...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !analytics) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto" />
            <h2 className="text-2xl font-bold text-gray-800">No Test Data Yet</h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Complete some tests to see your performance analytics.
            </p>
            <div className="flex gap-3 justify-center mt-6">
              <Button onClick={() => navigate("/test")} className="bg-purple-600 hover:bg-purple-700 text-white gap-2">
                <Brain className="w-4 h-4" />
                Take Your First Test
              </Button>
              <Button variant="outline" onClick={() => navigate("/dashboard")} className="gap-2">
                <Home className="w-4 h-4" />
                Go to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const perfLevel = getPerformanceLevel(analytics.overall_average);
  const PerfIcon = perfLevel.icon;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <BarChart3 className="w-7 h-7 text-purple-600" />
              Performance Report
            </h1>
            <p className="text-gray-500 mt-1">
              {user.preferredSubject || "Mathematics"} - Class {user.classLevel || 10}
            </p>
          </div>
          <Button 
            onClick={() => navigate("/test")}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            <Brain className="w-4 h-4" />
            Take Test
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className={`rounded-2xl p-6 border-2 ${getScoreBg(analytics.overall_average)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Overall Average</span>
              <PerfIcon className="w-5 h-5" />
            </div>
            <div className={`text-4xl font-bold ${getScoreColor(analytics.overall_average)}`}>
              {analytics.overall_average.toFixed(1)}%
            </div>
            <p className="text-sm font-medium mt-1">
              {perfLevel.label}
            </p>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Tests Taken</span>
              <Calendar className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-4xl font-bold text-gray-800">
              {analytics.total_tests_taken}
            </div>
            <p className="text-sm text-gray-500 mt-1">This month</p>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Best Score</span>
              <Award className="w-5 h-5 text-amber-600" />
            </div>
            <div className="text-4xl font-bold text-amber-600">
              {analytics.best_score.toFixed(0)}%
            </div>
            <p className="text-sm text-gray-500 mt-1">Personal best</p>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-6 border border-orange-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Study Streak</span>
              <Flame className="w-5 h-5 text-orange-600" />
            </div>
            <div className="text-4xl font-bold text-orange-600">
              {Math.min(analytics.total_tests_taken, 7)}
            </div>
            <p className="text-sm text-gray-500 mt-1">days</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 rounded-2xl p-6 border border-green-200">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">{analytics.topics_strong}</div>
                <p className="text-sm text-gray-600">Strong Topics</p>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-2xl p-6 border border-yellow-200">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-100 rounded-xl">
                <Target className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <div className="text-3xl font-bold text-yellow-600">{analytics.topics_moderate}</div>
                <p className="text-sm text-gray-600">Moderate Topics</p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-2xl p-6 border border-red-200">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-red-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <div className="text-3xl font-bold text-red-600">{analytics.topics_weak}</div>
                <p className="text-sm text-gray-600">Needs Practice</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-2">Ready to Improve?</h3>
              <p className="text-purple-100">
                Take more tests to improve your scores and master new topics
              </p>
            </div>
            <Button 
              onClick={() => navigate("/test")}
              className="bg-white text-purple-600 hover:bg-gray-100 gap-2"
            >
              <Brain className="w-5 h-5" />
              Start Test
            </Button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
