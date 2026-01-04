import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function TestManagement() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingSubmissions, setLoadingSubmissions] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  
  // Filters
  const [filterClass, setFilterClass] = useState("");
  const [filterSubject, setFilterSubject] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  
  // Comment modal
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [comment, setComment] = useState("");
  const [savingComment, setSavingComment] = useState(false);

  useEffect(() => {
    fetchTests();
    fetchStats();
  }, [filterClass, filterSubject, filterStatus]);

  const fetchTests = async () => {
    try {
      setLoading(true);
      let url = `${API_URL}/api/tests/admin?`;
      if (filterClass) url += `class_level=${filterClass}&`;
      if (filterSubject) url += `subject=${filterSubject}&`;
      if (filterStatus) url += `status=${filterStatus}&`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch tests");
      const data = await response.json();
      setTests(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/tests/stats/overview`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  };

  const fetchSubmissions = async (testId) => {
    try {
      setLoadingSubmissions(true);
      const response = await fetch(`${API_URL}/api/tests/submissions/${testId}`);
      if (!response.ok) throw new Error("Failed to fetch submissions");
      const data = await response.json();
      setSubmissions(data);
    } catch (err) {
      console.error("Failed to fetch submissions:", err);
      setSubmissions([]);
    } finally {
      setLoadingSubmissions(false);
    }
  };

  const handleTestClick = (test) => {
    setSelectedTest(test);
    fetchSubmissions(test.id);
  };

  const handleDeleteTest = async (testId) => {
    if (!confirm("Are you sure you want to delete this test? This will also delete all submissions.")) return;
    
    try {
      const response = await fetch(`${API_URL}/api/tests/${testId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete test");
      setTests(tests.filter(t => t.id !== testId));
      if (selectedTest?.id === testId) {
        setSelectedTest(null);
        setSubmissions([]);
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const openCommentModal = (submission) => {
    setSelectedSubmission(submission);
    setComment(submission.admin_comment || "");
    setShowCommentModal(true);
  };

  const handleSaveComment = async () => {
    if (!comment.trim()) {
      alert("Please enter a comment");
      return;
    }
    
    setSavingComment(true);
    try {
      const response = await fetch(`${API_URL}/api/tests/submissions/${selectedSubmission.id}/comment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comment: comment.trim() })
      });
      
      if (!response.ok) throw new Error("Failed to save comment");
      
      // Update submission in list
      setSubmissions(submissions.map(s => 
        s.id === selectedSubmission.id 
          ? { ...s, admin_comment: comment, is_reviewed: true }
          : s
      ));
      
      setShowCommentModal(false);
      setSelectedSubmission(null);
      setComment("");
      alert("Comment saved and student notified!");
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setSavingComment(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: "bg-green-100 text-green-700",
      upcoming: "bg-blue-100 text-blue-700",
      closed: "bg-gray-100 text-gray-700"
    };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.closed}`}>{status}</span>;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate("/admin-dashboard")} className="text-white/80 hover:text-white">
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold">Test Management</h1>
                <p className="text-purple-100 text-sm">View tests, submissions, and provide feedback</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/create-test")}
                className="px-4 py-2 bg-white text-purple-600 rounded-lg hover:bg-purple-50 font-medium"
              >
                + Create Test
              </button>
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Admin"}</span>
              <button onClick={() => { logout(); navigate("/"); }} className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition">Logout</button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-xl shadow-sm">
              <p className="text-2xl font-bold text-purple-600">{stats.total_tests}</p>
              <p className="text-sm text-gray-500">Total Tests</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm">
              <p className="text-2xl font-bold text-green-600">{stats.active_tests}</p>
              <p className="text-sm text-gray-500">Active Tests</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm">
              <p className="text-2xl font-bold text-blue-600">{stats.total_submissions}</p>
              <p className="text-sm text-gray-500">Submissions</p>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm">
              <p className="text-2xl font-bold text-orange-600">{stats.pending_review}</p>
              <p className="text-sm text-gray-500">Pending Review</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white p-4 rounded-xl shadow-sm mb-6">
          <div className="flex flex-wrap gap-4">
            <select
              value={filterClass}
              onChange={(e) => setFilterClass(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Classes</option>
              {[5, 6, 7, 8, 9, 10, 11, 12].map(c => (
                <option key={c} value={c}>Class {c}</option>
              ))}
            </select>
            
            <select
              value={filterSubject}
              onChange={(e) => setFilterSubject(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Subjects</option>
              {["Mathematics", "Science", "Social Science", "English", "Hindi", "Physics", "Chemistry", "Biology"].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="upcoming">Upcoming</option>
              <option value="closed">Closed</option>
            </select>
            
            <button
              onClick={() => { setFilterClass(""); setFilterSubject(""); setFilterStatus(""); }}
              className="px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg"
            >
              Clear Filters
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Test List */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Tests ({tests.length})</h2>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-purple-600 mx-auto"></div>
              </div>
            ) : tests.length === 0 ? (
              <div className="bg-white p-8 rounded-xl text-center text-gray-500">
                <p>No tests found</p>
                <button
                  onClick={() => navigate("/create-test")}
                  className="mt-4 text-purple-600 hover:underline"
                >
                  Create your first test
                </button>
              </div>
            ) : (
              tests.map(test => (
                <div
                  key={test.id}
                  onClick={() => handleTestClick(test)}
                  className={`bg-white p-4 rounded-xl shadow-sm cursor-pointer transition hover:shadow-md ${
                    selectedTest?.id === test.id ? "ring-2 ring-purple-500" : ""
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900">{test.title}</h3>
                    {getStatusBadge(test.status)}
                  </div>
                  <div className="text-sm text-gray-500 space-y-1">
                    <p>Class {test.class_level} • {test.subject}</p>
                    <p>{test.submission_count} submissions</p>
                    {test.is_timed && test.start_datetime && (
                      <p className="text-blue-600">Starts: {new Date(test.start_datetime).toLocaleString()}</p>
                    )}
                    {test.is_timed && test.end_datetime && (
                      <p className="text-orange-600">Ends: {new Date(test.end_datetime).toLocaleString()}</p>
                    )}
                  </div>
                  <div className="flex gap-2 mt-3">
                    <a
                      href={`${API_URL}${test.pdf_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                    >
                      📄 View PDF
                    </a>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteTest(test.id); }}
                      className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Submissions Panel */}
          <div className="lg:col-span-2">
            {selectedTest ? (
              <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{selectedTest.title}</h2>
                    <p className="text-gray-500">Class {selectedTest.class_level} • {selectedTest.subject}</p>
                  </div>
                  <a
                    href={`${API_URL}${selectedTest.pdf_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                  >
                    📄 View Test PDF
                  </a>
                </div>

                <h3 className="font-medium text-gray-900 mb-4">
                  Submissions ({submissions.length})
                </h3>

                {loadingSubmissions ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-purple-600 mx-auto"></div>
                  </div>
                ) : submissions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No submissions yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {submissions.map(sub => (
                      <div key={sub.id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900">{sub.student_name}</p>
                            <p className="text-sm text-gray-500">{sub.student_user_id}</p>
                            <p className="text-xs text-gray-400">
                              Submitted: {new Date(sub.submitted_at).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <a
                              href={`${API_URL}${sub.pdf_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                            >
                              📄 View Submission
                            </a>
                            <button
                              onClick={() => openCommentModal(sub)}
                              className={`px-3 py-1 rounded text-sm ${
                                sub.is_reviewed
                                  ? "bg-green-100 text-green-700 hover:bg-green-200"
                                  : "bg-orange-100 text-orange-700 hover:bg-orange-200"
                              }`}
                            >
                              {sub.is_reviewed ? "✅ Edit Comment" : "💬 Add Comment"}
                            </button>
                          </div>
                        </div>
                        
                        {sub.admin_comment && (
                          <div className="mt-3 p-3 bg-green-50 rounded-lg">
                            <p className="text-sm text-green-800">
                              <strong>Your Comment:</strong> {sub.admin_comment}
                            </p>
                            <p className="text-xs text-green-600 mt-1">
                              Sent: {sub.comment_at ? new Date(sub.comment_at).toLocaleString() : "-"}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-500">
                <p className="text-4xl mb-4">📋</p>
                <p>Select a test to view submissions</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Comment Modal */}
      {showCommentModal && selectedSubmission && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-xl font-bold mb-4">Add Feedback for {selectedSubmission.student_name}</h2>
            
            <div className="mb-4">
              <a
                href={`${API_URL}${selectedSubmission.pdf_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                📄 View Student's Submission
              </a>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Comment/Feedback
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={6}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Enter your feedback for the student..."
              />
            </div>
            
            <p className="text-sm text-gray-500 mb-4">
              ℹ️ The student will receive a notification when you save this comment.
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={() => { setShowCommentModal(false); setSelectedSubmission(null); }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveComment}
                disabled={savingComment || !comment.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {savingComment ? "Saving..." : "Save & Notify Student"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
