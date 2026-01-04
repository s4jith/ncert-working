import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    fetchNotifications();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/api/admin/analytics`);
      if (!response.ok) throw new Error("Failed to fetch analytics");
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
      // Set empty state - NO mock data
      setAnalytics({
        user_stats: { total_users: 0, total_students: 0, total_teachers: 0, active_today: 0, active_this_week: 0, active_this_month: 0, inactive_users: 0, new_users_today: 0, new_users_this_week: 0, new_users_this_month: 0 },
        test_stats: { total_tests_created: 0, total_tests_taken: 0, tests_completed: 0, tests_in_progress: 0, average_score: 0, pass_rate: 0, tests_today: 0, tests_this_week: 0 },
        activity_trend: [],
        subject_stats: [],
        top_performers: [],
        weak_students: [],
        recent_activities: []
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await fetch(`${API_URL}/api/support-tickets/notifications/admin`);
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
      await fetch(`${API_URL}/api/support-tickets/notifications/${notificationId}/mark-read`, {
        method: "POST"
      });
      fetchNotifications();
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const handleLogout = () => { logout(); navigate("/"); };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics from database...</p>
        </div>
      </div>
    );
  }

  const { user_stats, test_stats, activity_trend, subject_stats, top_performers, weak_students } = analytics || {};

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Admin Dashboard</h1>
              <p className="text-blue-100 text-sm">NCERT Learning Platform - Live Data</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Notification Bell */}
              <div className="relative">
                <button 
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="p-2 bg-white/20 hover:bg-white/30 rounded-full relative"
                >
                  <span className="text-xl">🔔</span>
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>
                
                {/* Notifications Dropdown */}
                {showNotifications && (
                  <div className="absolute right-0 top-12 w-80 bg-white rounded-lg shadow-xl z-50 max-h-96 overflow-hidden">
                    <div className="p-3 border-b bg-gray-50">
                      <div className="flex justify-between items-center">
                        <h3 className="font-semibold text-gray-800">Notifications</h3>
                        <button 
                          onClick={() => navigate("/support-tickets")}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          View All Tickets
                        </button>
                      </div>
                    </div>
                    <div className="max-h-72 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-4 text-center text-gray-500">
                          No notifications
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
                            className={`p-3 border-b hover:bg-gray-50 cursor-pointer ${!n.is_read ? 'bg-blue-50' : ''}`}
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
              
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Admin"}</span>
              <button onClick={handleLogout} className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition">Logout</button>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-4">
            {[{ id: "overview", label: "Overview" }, { id: "students", label: "Students" }, { id: "tests", label: "Tests" }, { id: "books", label: "Books" }, { id: "support", label: "Support Tickets" }].map(tab => (
              <button key={tab.id} onClick={() => { if (tab.id === "students") navigate("/student-management"); else if (tab.id === "tests") navigate("/test-management"); else if (tab.id === "books") navigate("/book-management"); else if (tab.id === "support") navigate("/support-tickets"); else setActiveTab(tab.id); }}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition ${activeTab === tab.id ? "border-white text-white" : "border-transparent text-blue-100 hover:text-white"}`}>
                {tab.label}
                {tab.id === "support" && unreadCount > 0 && (
                  <span className="ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{unreadCount}</span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-red-700 text-sm"> Could not connect to backend. Please start the backend server.</p>
            <p className="text-red-600 text-xs mt-1">Error: {error}</p>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <StatCard label="Total Users" value={user_stats?.total_users || 0} icon="" color="blue" />
          <StatCard label="Students" value={user_stats?.total_students || 0} icon="" color="green" />
          <StatCard label="Teachers" value={user_stats?.total_teachers || 0} icon="" color="purple" />
          <StatCard label="Active Today" value={user_stats?.active_today || 0} icon="" color="emerald" />
          <StatCard label="Tests Today" value={test_stats?.tests_today || 0} icon="" color="orange" />
          <StatCard label="Avg Score" value={`${test_stats?.average_score || 0}%`} icon="" color="pink" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Activity Chart */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">User Activity (Last 14 Days)</h2>
            {activity_trend?.length > 0 ? (
              <div className="h-64 flex items-end justify-between gap-1">
                {activity_trend.map((day, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div className="w-full flex flex-col items-center gap-1">
                      <div className="w-full bg-blue-500 rounded-t" style={{ height: `${Math.max(day.active_users * 3, 2)}px` }} title={`${day.active_users} users`}></div>
                      <div className="w-full bg-green-500 rounded-t" style={{ height: `${Math.max(day.tests_taken * 4, 2)}px` }} title={`${day.tests_taken} tests`}></div>
                    </div>
                    <span className="text-xs text-gray-500 mt-2">{day.date?.slice(5)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                <p>No activity data yet. Data will appear as users interact with the platform.</p>
              </div>
            )}
            <div className="flex justify-center gap-6 mt-4">
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-blue-500 rounded"></div><span className="text-sm text-gray-600">Active Users</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-green-500 rounded"></div><span className="text-sm text-gray-600">Tests Taken</span></div>
            </div>
          </div>

          {/* Test Performance */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Performance</h2>
            <div className="space-y-4">
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
                <p className="text-4xl font-bold text-green-600">{test_stats?.pass_rate || 0}%</p>
                <p className="text-sm text-gray-600">Pass Rate</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{test_stats?.tests_completed || 0}</p>
                  <p className="text-xs text-gray-600">Completed</p>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <p className="text-2xl font-bold text-yellow-600">{test_stats?.tests_in_progress || 0}</p>
                  <p className="text-xs text-gray-600">In Progress</p>
                </div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{test_stats?.total_tests_created || 0}</p>
                <p className="text-xs text-gray-600">Total Tests Created</p>
              </div>
            </div>
          </div>
        </div>

        {/* Subject Performance */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Subject-wise Performance</h2>
          {subject_stats?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {subject_stats.map((subject, i) => (
                <div key={i} className="p-4 border rounded-lg hover:shadow-md transition">
                  <h3 className="font-medium text-gray-900 mb-2">{subject.subject}</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Avg Score</span>
                      <span className={`font-medium ${subject.avg_score >= 70 ? "text-green-600" : subject.avg_score >= 50 ? "text-yellow-600" : "text-red-600"}`}>{subject.avg_score}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${subject.avg_score >= 70 ? "bg-green-500" : subject.avg_score >= 50 ? "bg-yellow-500" : "bg-red-500"}`} style={{ width: `${subject.avg_score}%` }}></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{subject.total_tests} tests</span>
                      <span>{subject.total_students} students</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No subject data yet. Create tests and have students take them to see performance data.</p>
          )}
        </div>

        {/* Top Performers & Weak Students */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4"> Top Performers</h2>
            {top_performers?.length > 0 ? (
              <div className="space-y-3">
                {top_performers.map((student, i) => (
                  <div key={student.student_id} className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{i === 0 ? "" : i === 1 ? "" : i === 2 ? "" : ""}</span>
                      <div>
                        <p className="font-medium text-gray-900">{student.name}</p>
                        <p className="text-xs text-gray-500">{student.tests_completed} tests</p>
                      </div>
                    </div>
                    <p className="text-lg font-bold text-green-600">{student.avg_score}%</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">No top performers yet. Students will appear here after completing tests.</p>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4"> Needs Attention</h2>
            {weak_students?.length > 0 ? (
              <div className="space-y-3">
                {weak_students.map((student) => (
                  <div key={student.student_id} className="flex items-center justify-between p-3 bg-gradient-to-r from-red-50 to-orange-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl"></span>
                      <div>
                        <p className="font-medium text-gray-900">{student.name}</p>
                        <p className="text-xs text-gray-500">{student.days_inactive} days inactive</p>
                      </div>
                    </div>
                    <p className="text-lg font-bold text-red-600">{student.avg_score}%</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">No struggling students identified yet.</p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <ActionButton icon="" label="Add Student" onClick={() => navigate("/student-management")} color="blue" />
            <ActionButton icon="" label="Create Test" onClick={() => navigate("/create-test")} color="green" />
            <ActionButton icon="" label="View Tests" onClick={() => navigate("/test-management")} color="purple" />
            <ActionButton icon="🎫" label="Support Tickets" onClick={() => navigate("/support-tickets")} color="orange" badge={unreadCount > 0 ? unreadCount : null} />
            <ActionButton icon="" label="Refresh Data" onClick={fetchAnalytics} color="blue" />
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value, icon, color }) {
  const colors = { blue: "from-blue-500 to-blue-600", green: "from-green-500 to-green-600", purple: "from-purple-500 to-purple-600", emerald: "from-emerald-500 to-emerald-600", orange: "from-orange-500 to-orange-600", pink: "from-pink-500 to-pink-600" };
  return (
    <div className={`bg-gradient-to-br ${colors[color]} text-white rounded-xl p-4 shadow-sm`}>
      <div className="flex items-center justify-between mb-2"><span className="text-2xl">{icon}</span></div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs opacity-80">{label}</p>
    </div>
  );
}

function ActionButton({ icon, label, onClick, color, badge }) {
  const colors = { blue: "bg-blue-600 hover:bg-blue-700", green: "bg-green-600 hover:bg-green-700", purple: "bg-purple-600 hover:bg-purple-700", orange: "bg-orange-600 hover:bg-orange-700" };
  return (
    <button onClick={onClick} className={`${colors[color]} text-white p-4 rounded-xl flex flex-col items-center gap-2 transition shadow-sm hover:shadow-md relative`}>
      <span className="text-2xl">{icon}</span>
      <span className="text-sm font-medium">{label}</span>
      {badge && (
        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
          {badge > 9 ? '9+' : badge}
        </span>
      )}
    </button>
  );
}
