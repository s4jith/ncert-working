import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import {
  ArrowLeft,
  Bell,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  Upload,
  Eye,
  MessageSquare,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  BookOpen,
  Target,
  TrendingUp,
  Award,
  Calendar,
  User,
  Flag,
  X,
  Loader2
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function StudentTests() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("all"); // all, available, submitted, closed

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const testsPerPage = 6;

  // Upload state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // View feedback modal
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState(null);

  // Notifications
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // Detail view
  const [viewingTest, setViewingTest] = useState(null);

  useEffect(() => {
    if (user?.id) {
      fetchTests();
      fetchSubmissions();
      fetchNotifications();
    }
  }, [user]);

  const fetchTests = async () => {
    try {
      setLoading(true);
      const studentId = user?.id || user?.user_id;
      const response = await fetch(`${API_URL}/api/tests/student/${studentId}`);
      if (!response.ok) throw new Error("Failed to fetch tests");
      const data = await response.json();
      setTests(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSubmissions = async () => {
    try {
      const studentId = user?.id || user?.user_id;
      const response = await fetch(`${API_URL}/api/tests/my-submissions/${studentId}`);
      if (response.ok) {
        const data = await response.json();
        setSubmissions(data);
      }
    } catch (err) {
      console.error("Failed to fetch submissions:", err);
    }
  };

  const fetchNotifications = async () => {
    try {
      const studentId = user?.id || user?.user_id;
      const response = await fetch(`${API_URL}/api/tests/notifications/${studentId}?unread_only=true`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  };

  const markNotificationRead = async (notificationId) => {
    try {
      await fetch(`${API_URL}/api/tests/notifications/${notificationId}/read`, { method: "PUT" });
      setNotifications(notifications.filter(n => n.id !== notificationId));
    } catch (err) {
      console.error("Failed to mark notification read:", err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== "application/pdf") {
        alert("Please select a PDF file");
        return;
      }
      setUploadFile(file);
    }
  };

  const handleSubmitTest = async () => {
    if (!uploadFile || !selectedTest) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("test_id", selectedTest.id);
      formData.append("student_id", user?.id || user?.user_id);
      formData.append("pdf_file", uploadFile);

      const response = await fetch(`${API_URL}/api/tests/submit`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to submit test");
      }

      setShowUploadModal(false);
      setUploadFile(null);
      setSelectedTest(null);

      fetchTests();
      fetchSubmissions();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const openSubmitModal = (test) => {
    setSelectedTest(test);
    setShowUploadModal(true);
  };

  const viewFeedback = (submission) => {
    setSelectedSubmission(submission);
    setShowFeedbackModal(true);
  };

  // Filter tests based on active tab
  const getFilteredTests = () => {
    switch (activeTab) {
      case "available":
        return tests.filter(t => !t.has_submitted && t.status !== "closed");
      case "submitted":
        return tests.filter(t => t.has_submitted);
      case "closed":
        return tests.filter(t => t.status === "closed" && !t.has_submitted);
      default:
        return tests;
    }
  };

  const filteredTests = getFilteredTests();
  const totalPages = Math.ceil(filteredTests.length / testsPerPage);
  const paginatedTests = filteredTests.slice(
    (currentPage - 1) * testsPerPage,
    currentPage * testsPerPage
  );

  // Get test statistics
  const getTestStats = (test) => {
    const submission = submissions.find(s => s.test_id === test.id);
    return {
      status: test.has_submitted ? "Submitted" : test.status === "closed" ? "Closed" : "Available",
      dueDate: test.end_datetime ? new Date(test.end_datetime).toLocaleDateString() : "No deadline",
      hasFeedback: test.has_feedback || false,
      score: submission?.score || null
    };
  };

  // Detail View Component
  const TestDetailView = ({ test }) => {
    const submission = submissions.find(s => s.test_id === test.id);
    const stats = getTestStats(test);

    return (
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => setViewingTest(null)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm font-medium">Back to Tests</span>
        </button>

        {/* Test Header */}
        <div className="bg-white rounded-2xl p-8 border border-gray-100">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{test.title}</h1>
              <p className="text-gray-500">{test.description || "No description available"}</p>
            </div>
            <div className={`px-4 py-2 rounded-full text-sm font-medium ${test.has_submitted
                ? "bg-green-100 text-green-700"
                : test.status === "closed"
                  ? "bg-gray-100 text-gray-600"
                  : "bg-blue-100 text-blue-700"
              }`}>
              {stats.status}
            </div>
          </div>

          {/* Big Stats Grid - Like Image 2 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div>
              <p className="text-4xl font-bold text-gray-900">{test.subject || "General"}</p>
              <p className="text-sm text-gray-500 mt-1">Subject</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900">Class {test.class_level}</p>
              <p className="text-sm text-gray-500 mt-1">Level</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900">{stats.dueDate}</p>
              <p className="text-sm text-gray-500 mt-1">Due Date</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900">
                {submission?.score ? `${submission.score}%` : "--"}
              </p>
              <p className="text-sm text-gray-500 mt-1">Score</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <a
              href={`${API_URL}${test.pdf_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm font-medium"
            >
              <Eye className="w-4 h-4" />
              View Questions
            </a>

            {!test.has_submitted && test.status !== "closed" && (
              <button
                onClick={() => openSubmitModal(test)}
                className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition text-sm font-medium"
              >
                <Upload className="w-4 h-4" />
                Submit Answer
              </button>
            )}

            {test.has_submitted && submission && (
              <>
                {submission.pdf_url && (
                  <a
                    href={`${API_URL}${submission.pdf_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-5 py-2.5 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition text-sm font-medium"
                  >
                    <FileText className="w-4 h-4" />
                    View Submission
                  </a>
                )}
                {test.has_feedback && (
                  <button
                    onClick={() => viewFeedback(submission)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition text-sm font-medium"
                  >
                    <MessageSquare className="w-4 h-4" />
                    View Feedback
                  </button>
                )}
              </>
            )}

            <button
              onClick={() => navigate("/support-tickets")}
              className="flex items-center gap-2 px-5 py-2.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition text-sm font-medium ml-auto"
            >
              <Flag className="w-4 h-4" />
              Report Issue
            </button>
          </div>
        </div>

        {/* Additional Stats Cards */}
        {test.has_submitted && submission && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-2xl p-6 border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Submission Details</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Submitted On</span>
                  <span className="font-medium text-gray-900">
                    {submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span className="font-medium text-green-600">Completed</span>
                </div>
              </div>
            </div>

            {test.has_feedback && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">Teacher Feedback</h3>
                </div>
                <p className="text-gray-600 text-sm">
                  {submission?.admin_comment || "Feedback available - click 'View Feedback' to see details."}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // If viewing a specific test, show detail view
  if (viewingTest) {
    return (
      <DashboardLayout>
        <TestDetailView test={viewingTest} />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/student")}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {tests.length} {tests.length === 1 ? "Test" : "Tests"}
              </h1>
              <p className="text-sm text-gray-500">Class {user?.classLevel} • Manage your tests</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2.5 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 relative transition"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                    {notifications.length}
                  </span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg z-50 border border-gray-100 max-h-96 overflow-hidden">
                  <div className="p-4 border-b border-gray-100">
                    <h3 className="font-semibold text-gray-900">Notifications</h3>
                  </div>
                  <div className="max-h-72 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center">
                        <Bell className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                        <p className="text-gray-500 text-sm">No new notifications</p>
                      </div>
                    ) : (
                      notifications.map(n => (
                        <div key={n.id} className="p-4 border-b border-gray-50 hover:bg-gray-50">
                          <p className="font-medium text-gray-900 text-sm">{n.title}</p>
                          <p className="text-gray-500 text-sm mt-1">{n.message}</p>
                          <div className="flex justify-between items-center mt-2">
                            <span className="text-xs text-gray-400">
                              {new Date(n.created_at).toLocaleString()}
                            </span>
                            <button
                              onClick={() => markNotificationRead(n.id)}
                              className="text-xs text-blue-600 hover:underline"
                            >
                              Mark as read
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filter Tabs - Like Image 1 */}
        <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg w-fit">
          {[
            { id: "all", label: "All Tests" },
            { id: "available", label: "Available" },
            { id: "submitted", label: "Submitted" },
            { id: "closed", label: "Closed" }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setCurrentPage(1); }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${activeTab === tab.id
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-100 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : filteredTests.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No tests found</h3>
            <p className="text-gray-500">Check back later for new tests from your teachers</p>
          </div>
        ) : (
          <>
            {/* Tests List - Like Image 1 */}
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-gray-100 bg-gray-50">
                <div className="col-span-5 text-xs font-medium text-gray-500 uppercase tracking-wider">Test</div>
                <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Subject</div>
                <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Due Date</div>
                <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-center">Status</div>
                <div className="col-span-1"></div>
              </div>

              {/* Test Rows */}
              {paginatedTests.map(test => {
                const stats = getTestStats(test);
                const submission = submissions.find(s => s.test_id === test.id);

                return (
                  <div
                    key={test.id}
                    className="grid grid-cols-12 gap-4 px-6 py-5 border-b border-gray-50 hover:bg-gray-50 transition cursor-pointer"
                    onClick={() => setViewingTest(test)}
                  >
                    {/* Test Info */}
                    <div className="col-span-5 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${test.has_submitted
                          ? "bg-green-100"
                          : test.status === "closed"
                            ? "bg-gray-100"
                            : "bg-blue-100"
                        }`}>
                        <FileText className={`w-5 h-5 ${test.has_submitted
                            ? "text-green-600"
                            : test.status === "closed"
                              ? "text-gray-500"
                              : "text-blue-600"
                          }`} />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">{test.title}</h3>
                        <p className="text-sm text-gray-500">Class {test.class_level}</p>
                      </div>
                    </div>

                    {/* Subject */}
                    <div className="col-span-2 flex items-center justify-center">
                      <span className="text-sm text-gray-600">{test.subject || "General"}</span>
                    </div>

                    {/* Due Date */}
                    <div className="col-span-2 flex items-center justify-center">
                      <span className="text-sm text-gray-600">{stats.dueDate}</span>
                    </div>

                    {/* Status */}
                    <div className="col-span-2 flex items-center justify-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${test.has_submitted
                          ? "bg-green-100 text-green-700"
                          : test.status === "closed"
                            ? "bg-gray-100 text-gray-600"
                            : "bg-blue-100 text-blue-700"
                        }`}>
                        {stats.status}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="col-span-1 flex items-center justify-end">
                      <button
                        onClick={(e) => { e.stopPropagation(); }}
                        className="p-1.5 hover:bg-gray-100 rounded-lg transition"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-end gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-8 h-8 rounded-lg text-sm font-medium transition ${currentPage === page
                          ? "bg-gray-900 text-white"
                          : "text-gray-600 hover:bg-gray-100"
                        }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && selectedTest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Submit Test</h2>
              <button
                onClick={() => { setShowUploadModal(false); setUploadFile(null); }}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <p className="text-gray-600 mb-4">{selectedTest.title}</p>

            <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-gray-400 transition mb-4">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="submission-upload"
              />
              <label htmlFor="submission-upload" className="cursor-pointer">
                {uploadFile ? (
                  <div className="flex flex-col items-center">
                    <FileText className="w-10 h-10 text-green-500 mb-3" />
                    <p className="text-green-600 font-medium">{uploadFile.name}</p>
                    <p className="text-sm text-gray-500 mt-1">Click to change file</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <Upload className="w-10 h-10 text-gray-400 mb-3" />
                    <p className="text-gray-600 font-medium">Upload your answer PDF</p>
                    <p className="text-sm text-gray-400 mt-1">Only PDF files are accepted</p>
                  </div>
                )}
              </label>
            </div>

            <div className="flex items-start gap-2 mb-6 p-3 bg-amber-50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-amber-700">
                You can only submit once. Make sure your answers are complete before submitting.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => { setShowUploadModal(false); setUploadFile(null); }}
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 font-medium text-gray-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitTest}
                disabled={uploading || !uploadFile}
                className="flex-1 px-4 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 font-medium transition flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Test"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && selectedSubmission && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Test Feedback</h2>
              <button
                onClick={() => { setShowFeedbackModal(false); setSelectedSubmission(null); }}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-500">Test: {selectedSubmission.test_title}</p>
              <p className="text-sm text-gray-500">
                Submitted: {new Date(selectedSubmission.submitted_at).toLocaleString()}
              </p>
            </div>

            {selectedSubmission.pdf_url && (
              <a
                href={`${API_URL}${selectedSubmission.pdf_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-blue-600 hover:underline text-sm mb-4"
              >
                <FileText className="w-4 h-4" />
                View Your Submission
              </a>
            )}

            <div className="bg-purple-50 p-4 rounded-xl mb-6">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-4 h-4 text-purple-600" />
                <h3 className="font-medium text-purple-900">Teacher's Feedback</h3>
              </div>
              <p className="text-purple-800">{selectedSubmission.admin_comment || "No comment yet"}</p>
              {selectedSubmission.comment_at && (
                <p className="text-xs text-purple-600 mt-2">
                  Received: {new Date(selectedSubmission.comment_at).toLocaleString()}
                </p>
              )}
            </div>

            <button
              onClick={() => { setShowFeedbackModal(false); setSelectedSubmission(null); }}
              className="w-full px-4 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 font-medium transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
