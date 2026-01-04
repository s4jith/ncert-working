import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  ArrowRight,
  Bell,
  Mail,
  Search,
  Flame,
  BookOpen,
  BarChart3,
  Users,
  ChevronRight,
  ChevronLeft,
  Heart,
  Play,
  Award,
  Target,
  Clock,
  MessageCircle,
  User,
  TrendingUp,
  Plus,
  StickyNote,
  Calendar
} from "lucide-react";
import useUserStore from "../stores/userStore";
import useNotesStore from "../stores/notesStore";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import StickyNotesCard from "../components/dashboard/StickyNotesCard";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Sample course data
const courses = [
  { id: 1, title: "Social Studies", watched: 2, total: 8, icon: Target, color: "bg-amber-100 text-amber-600" },
  { id: 2, title: "Mathematics", watched: 3, total: 8, icon: BarChart3, color: "bg-blue-100 text-blue-600" },
  { id: 3, title: "Physics", watched: 6, total: 12, icon: BookOpen, color: "bg-green-100 text-green-600" },
];

// Quick action cards data
const quickActions = [
  {
    id: 1,
    title: "My Tests",
    description: "View and submit your assigned tests, track your progress",
    icon: FileText,
    color: "bg-blue-500",
    bgColor: "bg-blue-50",
    textColor: "text-blue-600",
    route: "/test"
  },
  {
    id: 2,
    title: "Book to Bot",
    description: "Upload any textbook and chat with AI to understand concepts",
    icon: BookOpen,
    color: "bg-emerald-500",
    bgColor: "bg-emerald-50",
    textColor: "text-emerald-600",
    route: "/book-to-bot"
  },
  {
    id: 3,
    title: "AI Helper",
    description: "Get instant answers and explanations from our AI assistant",
    icon: MessageCircle,
    color: "bg-amber-500",
    bgColor: "bg-amber-50",
    textColor: "text-amber-600",
    route: "/book-to-bot"
  },
];



// Stats data
const statsData = [
  { label: "1-10 Jan", value: 45 },
  { label: "11-20 Jan", value: 50 },
  { label: "21-30 Jan", value: 35 },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { getRecentNotes } = useNotesStore();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [streakDays, setStreakDays] = useState(5);
  const [pendingTests, setPendingTests] = useState([]);
  const [loadingTests, setLoadingTests] = useState(true);

  useEffect(() => {
    fetchNotifications();
    fetchPendingTests();
  }, [user.id]);

  const fetchPendingTests = async () => {
    try {
      setLoadingTests(true);
      const response = await fetch(`${API_BASE}/api/tests/student/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        // Filter for pending tests (not submitted)
        const pending = (data.tests || []).filter(test => test.status !== 'submitted');
        setPendingTests(pending.slice(0, 3)); // Show max 3
      }
    } catch (err) {
      console.error("Failed to fetch tests:", err);
    } finally {
      setLoadingTests(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/support-tickets/notifications/user/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  };

  const markNotificationRead = async (notificationId) => {
    try {
      await fetch(`${API_BASE}/api/support-tickets/notifications/${notificationId}/mark-read`, {
        method: "POST"
      });
      fetchNotifications();
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good Morning";
    if (hour < 17) return "Good Afternoon";
    return "Good Evening";
  };

  const progressPercentage = 32;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Top Bar */}
        <div className="flex items-center justify-between mb-6">
          {/* Search Bar */}
          <div className="flex-1 max-w-xl">
            <div className="relative">
              <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search your course...."
                className="w-full pl-12 pr-4 py-3 bg-white rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4 ml-6">
            {/* Mail */}
            <button className="p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50">
              <Mail className="w-5 h-5 text-gray-600" />
            </button>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50 relative"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notifications Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 top-14 w-80 bg-white rounded-2xl shadow-xl z-50 max-h-96 overflow-hidden border border-gray-100">
                  <div className="p-4 border-b bg-gray-50">
                    <div className="flex justify-between items-center">
                      <h3 className="font-semibold text-gray-800">Notifications</h3>
                      <button
                        onClick={() => { navigate("/support-tickets"); setShowNotifications(false); }}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        View All
                      </button>
                    </div>
                  </div>
                  <div className="max-h-72 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-gray-500">
                        <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                        No notifications yet
                      </div>
                    ) : (
                      notifications.slice(0, 5).map(n => (
                        <div
                          key={n.id}
                          onClick={() => {
                            markNotificationRead(n.id);
                            navigate("/support-tickets");
                            setShowNotifications(false);
                          }}
                          className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${!n.is_read ? 'bg-blue-50' : ''}`}
                        >
                          <p className="text-sm font-medium text-gray-800">{n.title}</p>
                          <p className="text-xs text-gray-500 mt-1">{n.message}</p>
                          <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Profile */}
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
              <img
                src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name || 'User'}`}
                alt="Profile"
                className="w-10 h-10 rounded-full bg-gray-100"
              />
              <span className="font-medium text-gray-800">{user.name || 'Student'}</span>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">

            {/* Hero Banner */}
            <div className="bg-gradient-to-r from-sky-400 to-cyan-400 rounded-3xl p-8 text-white relative overflow-hidden">
              <div className="absolute right-0 top-0 w-64 h-64 opacity-20">
                <div className="w-full h-full bg-white/20 rounded-full blur-3xl"></div>
              </div>
              <span className="text-xs uppercase tracking-wider opacity-80">Free tier</span>
              <h2 className="text-3xl font-bold mt-2 max-w-md">
                Bringing AI to the place to where you are and everywhere❤️
              </h2>


              {/* Course Pills */}
              <div className="flex gap-4 mt-8">
                {courses.map(course => (
                  <div key={course.id} className="flex items-center gap-3 bg-white/20 backdrop-blur rounded-2xl px-4 py-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${course.color}`}>
                      <course.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs opacity-80">{course.watched}/{course.total} watched</p>
                      <p className="font-medium text-sm">{course.title}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Quick Actions</h3>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {quickActions.map(item => (
                  <div
                    key={item.id}
                    onClick={() => navigate(item.route)}
                    className="bg-white rounded-2xl p-6 border border-gray-100 cursor-pointer hover:shadow-lg hover:border-gray-200 group"
                  >
                    <div className={`w-14 h-14 ${item.bgColor} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110`}>
                      <item.icon className={`w-7 h-7 ${item.textColor}`} />
                    </div>
                    <h4 className="font-semibold text-gray-800 text-lg mb-2">{item.title}</h4>
                    <p className="text-sm text-gray-500 mb-4">{item.description}</p>
                    <div className={`inline-flex items-center gap-2 px-4 py-2 ${item.color} text-white rounded-full text-sm font-medium`}>
                      Go to {item.title} <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Your Tests */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Your Pending Tests</h3>
                <button onClick={() => navigate('/test')} className="text-sm text-blue-600 hover:underline">See all</button>
              </div>

              {loadingTests ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : pendingTests.length === 0 ? (
                <div className="text-center py-8">
                  <Award className="w-12 h-12 mx-auto text-green-500 mb-3" />
                  <h4 className="font-semibold text-gray-800 mb-1">All Caught Up!</h4>
                  <p className="text-sm text-gray-500">You have no pending tests. Great job!</p>
                </div>
              ) : (
                <>
                  {/* Table Header */}
                  <div className="grid grid-cols-4 gap-4 text-xs text-gray-500 uppercase tracking-wider pb-3 border-b border-gray-100">
                    <span>Test Name</span>
                    <span>Subject</span>
                    <span>Due Date</span>
                    <span>Action</span>
                  </div>

                  {/* Table Rows */}
                  {pendingTests.map(test => (
                    <div key={test.id} className="grid grid-cols-4 gap-4 items-center py-4 border-b border-gray-50">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
                          <FileText className="w-5 h-5 text-blue-600" />
                        </div>
                        <p className="font-medium text-sm text-gray-800 line-clamp-1">{test.title}</p>
                      </div>
                      <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full inline-block w-fit">
                        <BookOpen className="w-3 h-3 inline mr-1" />
                        {test.subject || 'General'}
                      </span>
                      <span className="text-sm text-gray-600">
                        {test.deadline ? new Date(test.deadline).toLocaleDateString() : 'No deadline'}
                      </span>
                      <button
                        onClick={() => navigate('/test')}
                        className="p-2 bg-blue-500 text-white rounded-full w-fit hover:bg-blue-600"
                      >
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">

            {/* Statistics Card */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Statistics</h3>
                <button className="text-gray-400 hover:text-gray-600">
                  <BarChart3 className="w-5 h-5" />
                </button>
              </div>

              {/* Profile Progress Ring */}
              <div className="flex flex-col items-center mb-6">
                <div className="relative w-24 h-24">
                  <svg className="w-24 h-24 -rotate-90">
                    <circle cx="48" cy="48" r="40" stroke="#e5e7eb" strokeWidth="8" fill="none" />
                    <circle
                      cx="48"
                      cy="48"
                      r="40"
                      stroke="#3b82f6"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 40 * progressPercentage / 100} ${2 * Math.PI * 40}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <img
                      src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name || 'User'}`}
                      alt="Profile"
                      className="w-16 h-16 rounded-full"
                    />
                  </div>
                  <div className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                    {progressPercentage}%
                  </div>
                </div>
              </div>

              {/* Greeting */}
              <div className="text-center mb-6">
                <h4 className="font-semibold text-gray-800 flex items-center justify-center gap-1">
                  {getGreeting()} {user.name || 'Student'} <Flame className="w-4 h-4 text-orange-500" />
                </h4>
                <p className="text-sm text-gray-500">Continue your learning to achieve your target!</p>
              </div>

              {/* Bar Chart */}
              <div className="flex items-end justify-between h-24 px-4">
                {statsData.map((stat, i) => (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <div
                      className={`w-12 rounded-t-lg ${i === 1 ? 'bg-blue-500' : 'bg-blue-200'}`}
                      style={{ height: `${stat.value}px` }}
                    />
                    <span className="text-xs text-gray-500">{stat.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Sticky Notes - Funky colorful component */}
            <StickyNotesCard />

            {/* Streak Card */}
            <div className="bg-gradient-to-r from-orange-400 to-amber-400 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Flame className="w-5 h-5" />
                    <h3 className="font-semibold">{streakDays} Day Streak</h3>
                  </div>
                  <p className="text-sm opacity-80">Keep learning daily!</p>
                </div>
                <div className="text-4xl font-bold">{streakDays}</div>
              </div>
            </div>



            {/* Message Staff */}
            <div
              onClick={() => navigate("/support-tickets")}
              className="bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl p-6 cursor-pointer hover:shadow-lg"
            >
              <div className="flex items-center justify-between text-white">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <MessageCircle className="w-5 h-5" />
                    <h3 className="font-semibold">Message Staff</h3>
                  </div>
                  <p className="text-sm opacity-80">Get help from our team</p>
                </div>
                <ArrowRight className="w-6 h-6" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
