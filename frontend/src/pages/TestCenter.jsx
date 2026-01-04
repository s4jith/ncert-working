import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import useUserStore from "../stores/userStore";
import {
  FileText,
  Brain,
  Award,
  BookOpen,
  Target,
  TrendingUp,
  Clock,
  CheckCircle2,
  ArrowRight,
  ChevronRight,
  Play
} from "lucide-react";
import StaffTestCard from "../components/test/StaffTestCard";
import TopicSelector from "../components/test/TopicSelector";
import { testService } from "../services/api";

/**
 * TestCenter Page
 * 
 * Minimal, clean design with white/light theme.
 * Two types of tests: AI Tests and Staff Tests
 */

export default function TestCenter() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const [activeTab, setActiveTab] = useState("ai");
  const [staffTests, setStaffTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTopicSelector, setShowTopicSelector] = useState(false);

  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchTests();
  }, [user.id, user.preferredSubject]);

  const fetchTests = async () => {
    setLoading(true);
    try {
      const [staffData, analyticsData] = await Promise.all([
        testService.getStaffTests(user.preferredSubject, null, user.id),
        testService.getStudentAnalytics(user.id, user.classLevel || 10, user.preferredSubject)
      ]);
      setStaffTests(Array.isArray(staffData) ? staffData : []);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error("Failed to fetch tests:", error);
      setStaffTests([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTopicSelected = async (config) => {
    setShowTopicSelector(false);
    navigate("/test-session", {
      state: {
        testConfig: {
          student_id: user.id,
          class_level: user.classLevel || 10,
          ...config
        }
      }
    });
  };

  const tabs = [
    { id: "ai", label: "AI Tests", icon: Brain },
    { id: "staff", label: "Staff Tests", icon: FileText },
  ];

  // Quick stats
  const stats = [
    { label: "Tests Taken", value: analytics?.total_tests_taken || "0", icon: CheckCircle2 },
    { label: "Avg. Score", value: `${analytics?.overall_average || 0}%`, icon: TrendingUp },
    { label: "This Week", value: analytics?.tests_this_week || "0", icon: Clock },
  ];

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Test Center</h1>
            <p className="text-gray-500 mt-1">
              Take tests and track your learning progress
            </p>
          </div>
          <button
            onClick={() => navigate("/report-card")}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium"
          >
            <Award className="w-4 h-4" />
            View Reports
          </button>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-5 border border-gray-100"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                </div>
                <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-gray-400" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all ${activeTab === tab.id
                ? "bg-gray-900 text-white"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-gray-800" />
          </div>
        ) : (
          <>
            {/* AI Tests Tab */}
            {activeTab === "ai" && (
              <div className="space-y-6">
                {/* Main CTA Card */}
                <div className="bg-white rounded-3xl p-8 border border-gray-100">
                  <div className="flex items-center gap-6">
                    <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center flex-shrink-0">
                      <Brain className="w-10 h-10 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <h2 className="text-xl font-bold text-gray-900 mb-2">
                        Take an AI-Powered Test
                      </h2>
                      <p className="text-gray-500 mb-4">
                        Select a topic from your syllabus. Get instant evaluation with detailed feedback.
                      </p>
                      <button
                        onClick={() => setShowTopicSelector(true)}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-medium"
                      >
                        <Play className="w-5 h-5" />
                        Start Test
                      </button>
                    </div>
                  </div>
                </div>

                {/* Features */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white rounded-2xl p-6 border border-gray-100">
                    <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center mb-4">
                      <Target className="w-6 h-6 text-gray-600" />
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">Topic-Focused</h4>
                    <p className="text-sm text-gray-500">
                      Pre-generated questions for every topic in your syllabus.
                    </p>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border border-gray-100">
                    <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center mb-4">
                      <TrendingUp className="w-6 h-6 text-gray-600" />
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">Smart Recommendations</h4>
                    <p className="text-sm text-gray-500">
                      Get topic suggestions based on your weak areas.
                    </p>
                  </div>

                  <div className="bg-white rounded-2xl p-6 border border-gray-100">
                    <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center mb-4">
                      <Brain className="w-6 h-6 text-gray-600" />
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-2">AI Evaluation</h4>
                    <p className="text-sm text-gray-500">
                      RAG-based answer evaluation for accurate assessment.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Staff Tests Tab */}
            {activeTab === "staff" && (
              <div className="space-y-6">
                {/* Info Card */}
                <div className="bg-white rounded-2xl p-6 border border-gray-100">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center">
                      <FileText className="w-7 h-7 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">Staff Assigned Tests</h3>
                      <p className="text-sm text-gray-500">
                        Download question papers, write answers, and upload your answer sheets for evaluation.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Tests List */}
                {staffTests.length === 0 ? (
                  <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                    <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <FileText className="w-8 h-8 text-gray-300" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Tests Available</h3>
                    <p className="text-gray-500">
                      Your teacher hasn't uploaded any tests yet.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {staffTests.map((test) => (
                      <StaffTestCard
                        key={test.id}
                        test={test}
                        studentId={user.id}
                        onRefresh={fetchTests}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Topic Selector Modal */}
      {showTopicSelector && (
        <TopicSelector
          studentId={user.id}
          classLevel={user.classLevel || 10}
          onSelectTopic={handleTopicSelected}
          onCancel={() => setShowTopicSelector(false)}
        />
      )}
    </DashboardLayout>
  );
}
