import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SUBJECTS = [
  "Mathematics",
  "Science",
  "Social Science", 
  "English",
  "Hindi",
  "Physics",
  "Chemistry",
  "Biology"
];

const CLASSES = [5, 6, 7, 8, 9, 10, 11, 12];

export default function CreateTest() {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    class_level: 9,
    subject: "Mathematics",
    is_timed: false,
    start_datetime: "",
    end_datetime: "",
    duration_minutes: 60
  });
  
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfPreview, setPdfPreview] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== "application/pdf") {
        setError("Please select a PDF file");
        return;
      }
      setPdfFile(file);
      setPdfPreview(file.name);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!pdfFile) {
      setError("Please upload a PDF file for the test");
      return;
    }
    
    if (formData.is_timed) {
      if (!formData.start_datetime || !formData.end_datetime) {
        setError("Please set both start and end times for timed tests");
        return;
      }
      if (new Date(formData.start_datetime) >= new Date(formData.end_datetime)) {
        setError("End time must be after start time");
        return;
      }
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const submitData = new FormData();
      submitData.append("title", formData.title);
      submitData.append("description", formData.description || "");
      submitData.append("class_level", formData.class_level);
      submitData.append("subject", formData.subject);
      submitData.append("is_timed", formData.is_timed);
      submitData.append("created_by", user?.user_id || "admin");
      submitData.append("pdf_file", pdfFile);
      
      if (formData.is_timed) {
        submitData.append("start_datetime", formData.start_datetime);
        submitData.append("end_datetime", formData.end_datetime);
        if (formData.duration_minutes) {
          submitData.append("duration_minutes", formData.duration_minutes);
        }
      }
      
      const response = await fetch(`${API_URL}/api/tests/create`, {
        method: "POST",
        body: submitData
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to create test");
      }
      
      const result = await response.json();
      setSuccess(`Test created successfully! ${result.students_notified} students have been notified.`);
      
      // Reset form
      setFormData({
        title: "",
        description: "",
        class_level: 9,
        subject: "Mathematics",
        is_timed: false,
        start_datetime: "",
        end_datetime: "",
        duration_minutes: 60
      });
      setPdfFile(null);
      setPdfPreview(null);
      
      // Redirect after 2 seconds
      setTimeout(() => {
        navigate("/test-management");
      }, 2000);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-green-600 to-teal-600 text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/admin-dashboard")}
                className="flex items-center gap-2 text-white/80 hover:text-white"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold">Create New Test</h1>
                <p className="text-green-100 text-sm">Upload test PDF for students</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm bg-white/20 px-3 py-1 rounded-full">{user?.email || "Admin"}</span>
              <button onClick={() => { logout(); navigate("/"); }} className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition">Logout</button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {success && (
          <div className="mb-6 bg-green-50 border-l-4 border-green-500 p-4 rounded">
            <p className="text-green-700">✅ {success}</p>
          </div>
        )}
        
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded">
            <p className="text-red-700">❌ {error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-6 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">Test Information</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Test Title *</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="e.g., Mathematics Unit Test - Chapter 1"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                rows={3}
                placeholder="Add any instructions or notes for students..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Class Level *</label>
                <select
                  value={formData.class_level}
                  onChange={(e) => setFormData({ ...formData, class_level: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {CLASSES.map(c => (
                    <option key={c} value={c}>Class {c}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Subject *</label>
                <select
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {SUBJECTS.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* PDF Upload */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">Test Questions (PDF)</h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-green-500 transition">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="pdf-upload"
              />
              <label htmlFor="pdf-upload" className="cursor-pointer">
                {pdfPreview ? (
                  <div className="flex flex-col items-center">
                    <span className="text-4xl mb-2">📄</span>
                    <p className="text-green-600 font-medium">{pdfPreview}</p>
                    <p className="text-sm text-gray-500 mt-1">Click to change file</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <span className="text-4xl mb-2">📤</span>
                    <p className="text-gray-600 font-medium">Click to upload PDF</p>
                    <p className="text-sm text-gray-400 mt-1">Only PDF files are accepted</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Timing Options */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">Timing (Optional)</h2>
            
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_timed"
                checked={formData.is_timed}
                onChange={(e) => setFormData({ ...formData, is_timed: e.target.checked })}
                className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
              />
              <label htmlFor="is_timed" className="text-sm font-medium text-gray-700">
                This is a timed test with specific start and end dates
              </label>
            </div>
            
            {formData.is_timed && (
              <div className="grid grid-cols-2 gap-4 mt-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date & Time *</label>
                  <input
                    type="datetime-local"
                    value={formData.start_datetime}
                    onChange={(e) => setFormData({ ...formData, start_datetime: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Date & Time *</label>
                  <input
                    type="datetime-local"
                    value={formData.end_datetime}
                    onChange={(e) => setFormData({ ...formData, end_datetime: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                  <input
                    type="number"
                    min={10}
                    max={180}
                    value={formData.duration_minutes}
                    onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
              </div>
            )}
            
            {!formData.is_timed && (
              <p className="text-sm text-gray-500 bg-blue-50 p-3 rounded-lg">
                ℹ️ Without timing, this will be a <strong>general test</strong> that students can complete anytime.
              </p>
            )}
          </div>

          {/* Summary */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Test Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <p><span className="text-gray-500">Title:</span> {formData.title || "-"}</p>
              <p><span className="text-gray-500">Class:</span> Class {formData.class_level}</p>
              <p><span className="text-gray-500">Subject:</span> {formData.subject}</p>
              <p><span className="text-gray-500">Type:</span> {formData.is_timed ? "Timed Test" : "General Test"}</p>
              <p><span className="text-gray-500">PDF:</span> {pdfPreview || "Not uploaded"}</p>
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => navigate("/admin-dashboard")}
              className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !pdfFile}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? "Creating Test..." : "Create Test & Notify Students"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
