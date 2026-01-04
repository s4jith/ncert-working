import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function StaffTests() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterSubject, setFilterSubject] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => { fetchTests(); }, []);

  const fetchTests = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/api/admin/tests?limit=100`);
      if (!response.ok) throw new Error("Failed to fetch tests");
      const data = await response.json();
      setTests(data);
    } catch (err) {
      setError(err.message);
      setTests([]); // No mock data
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (testId, currentStatus) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/tests/${testId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !currentStatus })
      });
      if (!response.ok) throw new Error("Failed to update test");
      setTests(tests.map(t => t.id === testId ? { ...t, is_active: !currentStatus } : t));
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const handleDeleteTest = async (testId) => {
    if (!confirm("Are you sure you want to delete this test?")) return;
    try {
      const response = await fetch(`${API_URL}/api/admin/tests/${testId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete test");
      setTests(tests.filter(t => t.id !== testId));
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const filteredTests = tests.filter(test => {
    if (filterSubject !== "all" && test.subject !== filterSubject) return false;
    if (filterStatus === "active" && !test.is_active) return false;
    if (filterStatus === "inactive" && test.is_active) return false;
    if (searchTerm && !test.title?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const subjects = [...new Set(tests.map(t => t.subject).filter(Boolean))];
  const handleLogout = () => { logout(); navigate("/"); };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-gradient-to-r from-green-600 to-teal-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate("/admin-dashboard")} className="p-2 hover:bg-white/20 rounded-lg transition"> Back</button>
              <div><h1 className="text-2xl font-bold">Test Management</h1><p className="text-green-100 text-sm">Create and manage tests - Live Data</p></div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Staff"}</span>
              <button onClick={handleLogout} className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition">Logout</button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-red-700 text-sm"> Could not connect to backend: {error}</p>
            <p className="text-red-600 text-xs mt-1">Please ensure the backend server is running on port 8000</p>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl shadow-sm"><p className="text-3xl font-bold text-blue-600">{tests.length}</p><p className="text-sm text-gray-600">Total Tests</p></div>
          <div className="bg-white p-4 rounded-xl shadow-sm"><p className="text-3xl font-bold text-green-600">{tests.filter(t => t.is_active).length}</p><p className="text-sm text-gray-600">Active</p></div>
          <div className="bg-white p-4 rounded-xl shadow-sm"><p className="text-3xl font-bold text-yellow-600">{tests.reduce((sum, t) => sum + (t.questions?.length || t.total_questions || 0), 0)}</p><p className="text-sm text-gray-600">Total Questions</p></div>
          <div className="bg-white p-4 rounded-xl shadow-sm"><p className="text-3xl font-bold text-purple-600">{subjects.length}</p><p className="text-sm text-gray-600">Subjects</p></div>
        </div>

        {/* Actions Bar */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="flex gap-4 w-full md:w-auto flex-wrap">
              <input type="text" placeholder="Search tests..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 w-full md:w-48" />
              <select value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)} className="px-4 py-2 border rounded-lg">
                <option value="all">All Subjects</option>
                {subjects.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="px-4 py-2 border rounded-lg">
                <option value="all">All Status</option><option value="active">Active</option><option value="inactive">Inactive</option>
              </select>
            </div>
            <button onClick={() => navigate("/create-test")} className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2"><span></span> Create Test</button>
          </div>
        </div>

        {/* Tests Grid */}
        {loading ? (
          <div className="bg-white rounded-xl p-8 text-center"><div className="animate-spin rounded-full h-12 w-12 border-t-4 border-green-600 mx-auto"></div><p className="mt-4 text-gray-600">Loading from database...</p></div>
        ) : tests.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <div className="text-6xl mb-4"></div>
            <p className="text-gray-500 text-lg mb-4">No tests found in the database.</p>
            <button onClick={() => navigate("/create-test")} className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">Create Your First Test</button>
          </div>
        ) : filteredTests.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <p className="text-gray-500 text-lg">No tests match your filters.</p>
            <button onClick={() => { setSearchTerm(""); setFilterSubject("all"); setFilterStatus("all"); }} className="mt-4 text-green-600 hover:underline">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTests.map((test) => (
              <div key={test.id} className="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition">
                <div className={`h-2 ${test.is_active ? "bg-green-500" : "bg-gray-300"}`}></div>
                <div className="p-5">
                  <div className="flex justify-between items-start mb-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${test.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>{test.is_active ? "Active" : "Inactive"}</span>
                    <span className="text-xs text-gray-500">{test.duration_minutes || 30} min</span>
                  </div>
                  <h3 className="font-bold text-gray-900 mb-2 line-clamp-2">{test.title}</h3>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">{test.subject}</span>
                    <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">Class {test.class_level}</span>
                    <span className="text-xs bg-orange-50 text-orange-700 px-2 py-1 rounded">Ch {test.chapter}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mb-4">
                    <p> {test.questions?.length || test.total_questions || 0} Questions</p>
                    <p> {test.total_marks || 0} Marks</p>
                    <p> {test.attempts || 0} Attempts</p>
                    <p> {test.pass_percentage || 40}% Pass</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleToggleActive(test.id, test.is_active)} className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${test.is_active ? "bg-yellow-100 text-yellow-700 hover:bg-yellow-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}>{test.is_active ? "Deactivate" : "Activate"}</button>
                    <button onClick={() => handleDeleteTest(test.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition" title="Delete"></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
