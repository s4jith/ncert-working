import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function StudentManagement() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [newCredentials, setNewCredentials] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterActive, setFilterActive] = useState("all");
  const [saving, setSaving] = useState(false);

  // Updated form with age and mobile (no preferred_subject - students access all subjects)
  const [formData, setFormData] = useState({
    name: "",
    age: 14,
    email: "",
    mobile: "",
    class_level: 10
  });

  useEffect(() => {
    fetchStudents();
  }, [filterActive]);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      setError(null);
      let url = `${API_URL}/api/admin/students?limit=100`;
      if (filterActive !== "all") url += `&is_active=${filterActive === "active"}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch students");
      const data = await response.json();
      setStudents(data);
    } catch (err) {
      setError(err.message);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const response = await fetch(`${API_URL}/api/admin/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formData.name,
          age: formData.age,
          email: formData.email,
          mobile: formData.mobile,
          class_level: formData.class_level
        })
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to add student");
      }
      
      const newStudent = await response.json();
      
      // Show credentials modal with generated ID and password
      if (newStudent.generated_credentials) {
        setNewCredentials(newStudent.generated_credentials);
        setShowCredentialsModal(true);
      }
      
      setStudents([newStudent, ...students]);
      setShowAddModal(false);
      resetForm();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEditStudent = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const response = await fetch(`${API_URL}/api/admin/students/${selectedStudent.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: formData.name,
          age: formData.age,
          email: formData.email,
          mobile: formData.mobile,
          class_level: formData.class_level
        })
      });
      if (!response.ok) throw new Error("Failed to update student");
      const updated = await response.json();
      setStudents(students.map(s => s.id === selectedStudent.id ? updated : s));
      setShowEditModal(false);
      setSelectedStudent(null);
      resetForm();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteStudent = async (studentId) => {
    if (!confirm("Are you sure you want to delete this student?")) return;
    try {
      const response = await fetch(`${API_URL}/api/admin/students/${studentId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete student");
      setStudents(students.filter(s => s.id !== studentId));
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const handleToggleActive = async (student) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/students/${student.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !student.is_active })
      });
      if (!response.ok) throw new Error("Failed to update student");
      setStudents(students.map(s => s.id === student.id ? { ...s, is_active: !s.is_active } : s));
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const handleResetPassword = async (student) => {
    if (!confirm(`Reset password for ${student.name}?`)) return;
    try {
      const response = await fetch(`${API_URL}/api/admin/students/${student.id}/reset-password`, {
        method: "POST"
      });
      if (!response.ok) throw new Error("Failed to reset password");
      const result = await response.json();
      setNewCredentials({
        user_id: student.user_id,
        password: result.new_password,
        note: result.note
      });
      setShowCredentialsModal(true);
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      age: 14,
      email: "",
      mobile: "",
      class_level: 10
    });
  };

  const openEditModal = (student) => {
    setSelectedStudent(student);
    setFormData({
      name: student.name,
      age: student.age || 14,
      email: student.email,
      mobile: student.mobile || "",
      class_level: student.class_level
    });
    setShowEditModal(true);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const filteredStudents = students.filter(s =>
    s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.user_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button onClick={() => navigate("/admin-dashboard")} className="p-2 hover:bg-white/20 rounded-lg transition">
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold">Student Management</h1>
                <p className="text-blue-100 text-sm">Add, edit, and manage students</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Admin"}</span>
              <button onClick={handleLogout} className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <p className="text-red-700 text-sm">⚠️ Could not connect to backend: {error}</p>
            <p className="text-red-600 text-xs mt-1">Please ensure the backend server is running on port 8000</p>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <p className="text-3xl font-bold text-blue-600">{students.length}</p>
            <p className="text-sm text-gray-600">Total Students</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <p className="text-3xl font-bold text-green-600">{students.filter(s => s.is_active).length}</p>
            <p className="text-sm text-gray-600">Active</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <p className="text-3xl font-bold text-yellow-600">{students.filter(s => s.is_onboarded).length}</p>
            <p className="text-sm text-gray-600">Onboarded</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm">
            <p className="text-3xl font-bold text-red-600">{students.filter(s => !s.is_active).length}</p>
            <p className="text-sm text-gray-600">Inactive</p>
          </div>
        </div>

        {/* Actions Bar */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="flex gap-4 w-full md:w-auto">
              <input
                type="text"
                placeholder="Search by name, email, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-72"
              />
              <select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
            >
              ➕ Add Student
            </button>
          </div>
        </div>

        {/* Students Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading from database...</p>
            </div>
          ) : students.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500 text-lg mb-4">No students found in the database.</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Add Your First Student
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Age</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Class</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mobile</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredStudents.map((student) => (
                    <tr key={student.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                            {student.name?.charAt(0) || "?"}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{student.name}</p>
                            <p className="text-xs text-gray-500">{student.is_onboarded ? "✓ Onboarded" : "⏳ Not onboarded"}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">{student.user_id}</code>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{student.age || "-"}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">Class {student.class_level}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{student.email}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{student.mobile || "-"}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleToggleActive(student)}
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            student.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                          }`}
                        >
                          {student.is_active ? "Active" : "Inactive"}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEditModal(student)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                            title="Edit"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => handleResetPassword(student)}
                            className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition"
                            title="Reset Password"
                          >
                            🔑
                          </button>
                          <button
                            onClick={() => handleDeleteStudent(student.id)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                            title="Delete"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Add Student Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Add New Student</h2>
            <p className="text-sm text-gray-600 mb-4 bg-blue-50 p-3 rounded">
              💡 User ID and Password will be auto-generated based on name and age.<br/>
              <strong>Format:</strong> ID = name + age + number, Password = name + age
            </p>
            <form onSubmit={handleAddStudent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Student Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Sajith"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age *</label>
                  <input
                    type="number"
                    required
                    min="5"
                    max="25"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="14"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Class *</label>
                  <select
                    value={formData.class_level}
                    onChange={(e) => setFormData({ ...formData, class_level: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border rounded-lg"
                  >
                    {[5, 6, 7, 8, 9, 10, 11, 12].map((l) => (
                      <option key={l} value={l}>Class {l}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gmail Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="sajith123@gmail.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number *</label>
                <input
                  type="tel"
                  required
                  minLength="10"
                  maxLength="15"
                  value={formData.mobile}
                  onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1234567890"
                />
              </div>
              
              {/* Preview of generated credentials */}
              {formData.name && formData.age && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-600">
                    <strong>Preview:</strong><br/>
                    User ID: <code>{formData.name.toLowerCase().replace(/\s/g, '')}{formData.age}1</code> (approx)<br/>
                    Password: <code>{formData.name.toLowerCase().replace(/\s/g, '')}{formData.age}</code>
                  </p>
                </div>
              )}
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowAddModal(false); resetForm(); }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Creating..." : "Add Student"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Student Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-xl font-bold mb-4">Edit Student</h2>
            <form onSubmit={handleEditStudent} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                  <input
                    type="number"
                    min="5"
                    max="25"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Class</label>
                  <select
                    value={formData.class_level}
                    onChange={(e) => setFormData({ ...formData, class_level: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border rounded-lg"
                  >
                    {[5, 6, 7, 8, 9, 10, 11, 12].map((l) => (
                      <option key={l} value={l}>Class {l}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile</label>
                <input
                  type="tel"
                  value={formData.mobile}
                  onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setSelectedStudent(null); resetForm(); }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Credentials Modal */}
      {showCredentialsModal && newCredentials && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <div className="text-center mb-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">✅</span>
              </div>
              <h2 className="text-xl font-bold text-green-600">Student Created Successfully!</h2>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div>
                <p className="text-sm text-gray-500">User ID (Login ID)</p>
                <div className="flex items-center gap-2">
                  <code className="text-lg font-bold bg-white px-3 py-1 rounded border flex-1">{newCredentials.user_id}</code>
                  <button
                    onClick={() => copyToClipboard(newCredentials.user_id)}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    📋 Copy
                  </button>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Password</p>
                <div className="flex items-center gap-2">
                  <code className="text-lg font-bold bg-white px-3 py-1 rounded border flex-1">{newCredentials.password}</code>
                  <button
                    onClick={() => copyToClipboard(newCredentials.password)}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    📋 Copy
                  </button>
                </div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mt-4 bg-yellow-50 p-3 rounded">
              ⚠️ <strong>Important:</strong> {newCredentials.note}
            </p>
            
            <button
              onClick={() => { setShowCredentialsModal(false); setNewCredentials(null); }}
              className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
