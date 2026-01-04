import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useUserStore from "../stores/userStore";
import { Button } from "../components/ui/button";
import {
  BookOpen,
  Upload,
  Trash2,
  Eye,
  Database,
  Loader2,
  Plus,
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  XCircle,
  FileText,
  Layers,
  Settings,
  Book,
  GraduationCap,
  FileQuestion
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Hierarchical Book Management Page
 * 
 * Shows books in a tree structure:
 * Subject → Class → Chapters
 * 
 * Data comes from actual Pinecone vectors, not MongoDB
 */

export default function BookManagement() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  
  // State
  const [structure, setStructure] = useState(null); // Hierarchical data from Pinecone
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [pineconeStats, setPineconeStats] = useState(null);
  
  // Expansion state for accordion
  const [expandedSubjects, setExpandedSubjects] = useState({});
  const [expandedClasses, setExpandedClasses] = useState({});
  
  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // { type: 'subject'|'class'|'chapter', subject, classLevel?, chapter? }
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  
  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    title: "",
    subject: "Mathematics",
    class_level: 6,
    chapter_number: 1,
    description: "",
    pdf_file: null
  });
  
  const subjects = ["Mathematics", "Science", "Physics", "Chemistry", "Biology", "Social Science", "English", "Hindi"];
  
  useEffect(() => {
    fetchHierarchicalStructure();
    fetchPineconeStats();
  }, []);
  
  const fetchHierarchicalStructure = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/books/admin/hierarchical-structure`);
      if (response.ok) {
        const data = await response.json();
        setStructure(data.structure);
      } else {
        console.error("Failed to fetch structure");
      }
    } catch (err) {
      console.error("Failed to fetch structure:", err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchPineconeStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/books/admin/pinecone-stats`);
      if (response.ok) {
        const data = await response.json();
        setPineconeStats(data.stats);
      }
    } catch (err) {
      console.error("Failed to fetch Pinecone stats:", err);
    }
  };
  
  const toggleSubject = (subject) => {
    setExpandedSubjects(prev => ({
      ...prev,
      [subject]: !prev[subject]
    }));
  };
  
  const toggleClass = (subject, classLevel) => {
    const key = `${subject}-${classLevel}`;
    setExpandedClasses(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };
  
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.pdf_file) {
      alert("Please select a PDF file");
      return;
    }
    
    if (!uploadForm.title.trim()) {
      alert("Please enter a book title");
      return;
    }
    
    setUploading(true);
    setUploadProgress({ stage: "uploading", message: "Uploading PDF file...", percent: 10 });
    
    try {
      const formData = new FormData();
      formData.append("title", uploadForm.title);
      formData.append("subject", uploadForm.subject);
      formData.append("class_level", uploadForm.class_level);
      formData.append("chapter_number", uploadForm.chapter_number);
      formData.append("description", uploadForm.description);
      formData.append("generate_embeddings", "true");
      formData.append("pdf_file", uploadForm.pdf_file);
      
      setUploadProgress({ stage: "processing", message: "Processing PDF and generating embeddings... This may take several minutes.", percent: 30 });
      
      const response = await fetch(`${API_BASE}/api/books/upload`, {
        method: "POST",
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setUploadProgress({ stage: "complete", message: "Upload complete!", percent: 100 });
        
        alert(`Chapter ${uploadForm.chapter_number} uploaded successfully!\\n\\nEmbeddings generated from ${data.embeddings?.total_pages || 0} pages`);
        setShowUploadModal(false);
        setUploadForm({
          title: "",
          subject: "Mathematics",
          class_level: 6,
          chapter_number: 1,
          description: "",
          pdf_file: null
        });
        setUploadProgress(null);
        fetchHierarchicalStructure();
        fetchPineconeStats();
      } else {
        const error = await response.json();
        setUploadProgress({ stage: "error", message: `Upload failed: ${error.detail}`, percent: 0 });
        alert(`Upload failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Upload failed:", err);
      setUploadProgress({ stage: "error", message: "Upload failed. Please try again.", percent: 0 });
      alert("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };
  
  // Format subject names
  const formatSubjectName = (subject) => {
    return subject.charAt(0).toUpperCase() + subject.slice(1);
  };
  
  // Get delete confirmation text based on target type
  const getDeleteConfirmationText = () => {
    if (!deleteTarget) return "";
    switch (deleteTarget.type) {
      case "subject":
        return `DELETE ${deleteTarget.subject.toUpperCase()}`;
      case "class":
        return `DELETE CLASS ${deleteTarget.classLevel}`;
      case "chapter":
        return `DELETE CHAPTER ${deleteTarget.chapter}`;
      default:
        return "DELETE";
    }
  };
  
  // Get delete description
  const getDeleteDescription = () => {
    if (!deleteTarget) return "";
    switch (deleteTarget.type) {
      case "subject":
        return `This will permanently delete ALL ${formatSubjectName(deleteTarget.subject)} books across all classes and chapters. This action cannot be undone.`;
      case "class":
        return `This will permanently delete ALL chapters of ${formatSubjectName(deleteTarget.subject)} Class ${deleteTarget.classLevel}. This action cannot be undone.`;
      case "chapter":
        return `This will permanently delete ${formatSubjectName(deleteTarget.subject)} Class ${deleteTarget.classLevel} Chapter ${deleteTarget.chapter}. This action cannot be undone.`;
      default:
        return "";
    }
  };
  
  // Open delete modal
  const openDeleteModal = (type, subject, classLevel = null, chapter = null) => {
    setDeleteTarget({ type, subject, classLevel, chapter });
    setDeleteConfirmText("");
    setShowDeleteModal(true);
  };
  
  // Handle delete
  const handleDelete = async () => {
    if (!deleteTarget) return;
    
    const confirmText = getDeleteConfirmationText();
    if (deleteConfirmText !== confirmText) {
      alert(`Please type "${confirmText}" to confirm deletion`);
      return;
    }
    
    setDeleting(true);
    
    try {
      let url = "";
      let confirmationParam = "";
      
      switch (deleteTarget.type) {
        case "subject":
          url = `${API_BASE}/api/books/admin/delete-subject/${deleteTarget.subject.toLowerCase()}`;
          confirmationParam = deleteTarget.subject.toLowerCase();
          break;
        case "class":
          url = `${API_BASE}/api/books/admin/delete-class/${deleteTarget.subject.toLowerCase()}/${deleteTarget.classLevel}`;
          confirmationParam = `Class ${deleteTarget.classLevel}`;
          break;
        case "chapter":
          url = `${API_BASE}/api/books/admin/delete-chapter/${deleteTarget.subject.toLowerCase()}/${deleteTarget.classLevel}/${deleteTarget.chapter}`;
          confirmationParam = `Chapter ${deleteTarget.chapter}`;
          break;
      }
      
      // Add confirmation as query parameter
      url += `?confirmation=${encodeURIComponent(confirmationParam)}`;
      
      const response = await fetch(url, { method: "DELETE" });
      
      if (response.ok) {
        const data = await response.json();
        const deleted = data.deleted || {};
        alert(`Deleted successfully!\n\nVectors deleted from Pinecone: ${deleted.vectors_deleted || 0}\nBooks deleted from MongoDB: ${deleted.books_deleted || 0}`);
        setShowDeleteModal(false);
        setDeleteTarget(null);
        setDeleteConfirmText("");
        fetchHierarchicalStructure();
        fetchPineconeStats();
      } else {
        const error = await response.json();
        alert(`Delete failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Delete failed. Please try again.");
    } finally {
      setDeleting(false);
    }
  };
  
  // Get subject icon
  const getSubjectIcon = (subject) => {
    const iconProps = { className: "w-5 h-5" };
    if (subject.toLowerCase().includes('math')) return <FileText {...iconProps} />;
    if (subject.toLowerCase().includes('phys') || subject.toLowerCase().includes('chem') || subject.toLowerCase().includes('science')) {
      return <Layers {...iconProps} />;
    }
    return <Book {...iconProps} />;
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/admin")}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <div>
                <div className="flex items-center gap-3">
                  <BookOpen className="w-8 h-8" />
                  <h1 className="text-3xl font-bold">Book Management</h1>
                </div>
                <p className="text-purple-100 mt-1">Manage textbooks and AI embeddings</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                onClick={() => fetchHierarchicalStructure()}
                variant="ghost"
                className="bg-white/20 hover:bg-white/30 text-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                onClick={() => setShowUploadModal(true)}
                className="bg-white text-purple-600 hover:bg-purple-50"
              >
                <Plus className="w-4 h-4 mr-2" />
                Upload Book
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Pinecone Stats */}
        {pineconeStats && (
          <div className="bg-gradient-to-r from-green-400 to-emerald-500 rounded-2xl shadow-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6" />
              <h2 className="text-xl font-semibold">Pinecone Vector Database</h2>
            </div>
            
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white/20 rounded-xl p-4 backdrop-blur">
                <div className="text-sm opacity-90 mb-1">Total Vectors</div>
                <div className="text-3xl font-bold">{pineconeStats.total_vector_count?.toLocaleString()}</div>
              </div>
              
              <div className="bg-white/20 rounded-xl p-4 backdrop-blur">
                <div className="text-sm opacity-90 mb-1">Dimension</div>
                <div className="text-3xl font-bold">{pineconeStats.dimension}</div>
              </div>
              
              <div className="bg-white/20 rounded-xl p-4 backdrop-blur">
                <div className="text-sm opacity-90 mb-1">Namespaces</div>
                <div className="text-3xl font-bold">{Object.keys(pineconeStats.namespaces || {}).length}</div>
              </div>
              
              <div className="bg-white/20 rounded-xl p-4 backdrop-blur">
                <div className="text-sm opacity-90 mb-1">Status</div>
                <div className="flex items-center gap-2 mt-2">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-semibold">Connected</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Hierarchical Book Structure */}
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
            <Layers className="w-6 h-6 text-purple-600" />
            Books Library
          </h2>
          
          {!structure || Object.keys(structure).length === 0 ? (
            <div className="text-center py-12">
              <FileQuestion className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No books found in Pinecone</p>
              <p className="text-gray-400 mt-2">Upload your first book to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(structure).map(([subject, subjectData]) => (
                <div key={subject} className="border border-gray-200 rounded-xl overflow-hidden">
                  {/* Subject Header */}
                  <div className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 transition-all">
                    <button
                      onClick={() => toggleSubject(subject)}
                      className="flex items-center gap-3 flex-1"
                    >
                      {expandedSubjects[subject] ? (
                        <ChevronDown className="w-5 h-5 text-purple-600" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-purple-600" />
                      )}
                      {getSubjectIcon(subject)}
                      <span className="font-semibold text-lg text-gray-800">
                        {formatSubjectName(subject)}
                      </span>
                    </button>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-600">
                        {subjectData.total_vectors.toLocaleString()} vectors
                      </span>
                      <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                        {Object.keys(subjectData.classes).length} classes
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openDeleteModal("subject", subject);
                        }}
                        className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                        title="Delete entire subject"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Classes */}
                  {expandedSubjects[subject] && (
                    <div className="bg-white">
                      {Object.entries(subjectData.classes).map(([classKey, classData]) => (
                        <div key={classKey} className="border-t border-gray-100">
                          {/* Class Header */}
                          <div className="w-full flex items-center justify-between p-4 pl-12 hover:bg-gray-50 transition-colors">
                            <button
                              onClick={() => toggleClass(subject, classKey)}
                              className="flex items-center gap-3 flex-1"
                            >
                              {expandedClasses[`${subject}-${classKey}`] ? (
                                <ChevronDown className="w-4 h-4 text-blue-600" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-blue-600" />
                              )}
                              <GraduationCap className="w-5 h-5 text-blue-600" />
                              <span className="font-medium text-gray-700">
                                Class {classData.class_level}
                              </span>
                            </button>
                            <div className="flex items-center gap-4">
                              <span className="text-sm text-gray-500">
                                {classData.vector_count.toLocaleString()} vectors
                              </span>
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                                {classData.chapters.length} chapters
                              </span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openDeleteModal("class", subject, classData.class_level);
                                }}
                                className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                                title="Delete entire class"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          
                          {/* Chapters */}
                          {expandedClasses[`${subject}-${classKey}`] && (
                            <div className="bg-gray-50 p-4 pl-20">
                              <div className="grid grid-cols-6 gap-3">
                                {classData.chapters.map((chapterNum) => (
                                  <div
                                    key={chapterNum}
                                    className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow group relative"
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-2">
                                        <FileText className="w-4 h-4 text-green-600 group-hover:text-green-700" />
                                        <span className="font-medium text-gray-700 group-hover:text-gray-900">
                                          Ch. {chapterNum}
                                        </span>
                                      </div>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          openDeleteModal("chapter", subject, classData.class_level, chapterNum);
                                        }}
                                        className="p-1 text-red-400 hover:text-red-600 hover:bg-red-100 rounded transition-colors opacity-0 group-hover:opacity-100"
                                        title="Delete chapter"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                      </button>
                                    </div>
                                    <div className="mt-1">
                                      <span className="text-xs text-green-600 flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3" />
                                        AI Ready
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-2xl">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <Upload className="w-6 h-6" />
                Upload Book Chapter
              </h2>
              <p className="text-purple-100 mt-1">Upload one chapter at a time</p>
            </div>
            
            <form onSubmit={handleUpload} className="p-6 space-y-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chapter Title *
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
                  placeholder="e.g., Real Numbers"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              
              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject *
                </label>
                <select
                  value={uploadForm.subject}
                  onChange={(e) => setUploadForm({ ...uploadForm, subject: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {subjects.map(subj => (
                    <option key={subj} value={subj}>{subj}</option>
                  ))}
                </select>
              </div>
              
              {/* Class & Chapter */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Class Level *
                  </label>
                  <select
                    value={uploadForm.class_level}
                    onChange={(e) => setUploadForm({ ...uploadForm, class_level: parseInt(e.target.value) })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {[6, 7, 8, 9, 10, 11, 12].map(cls => (
                      <option key={cls} value={cls}>Class {cls}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chapter Number *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={uploadForm.chapter_number}
                    onChange={(e) => setUploadForm({ ...uploadForm, chapter_number: parseInt(e.target.value) })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
              
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="Brief description of the chapter..."
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              {/* PDF File */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  PDF File *
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setUploadForm({ ...uploadForm, pdf_file: e.target.files[0] })}
                  className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 transition-colors cursor-pointer"
                  required
                />
                {uploadForm.pdf_file && (
                  <p className="mt-2 text-sm text-gray-600">
                    Selected: {uploadForm.pdf_file.name}
                  </p>
                )}
              </div>
              
              {/* Upload Progress */}
              {uploadProgress && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <span className="font-medium text-blue-900">{uploadProgress.message}</span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress.percent}%` }}
                    />
                  </div>
                </div>
              )}
              
              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadProgress(null);
                  }}
                  variant="outline"
                  className="flex-1"
                  disabled={uploading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  disabled={uploading}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Chapter
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <div className="bg-gradient-to-r from-red-500 to-red-600 text-white p-6 rounded-t-2xl">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <Trash2 className="w-6 h-6" />
                Confirm Deletion
              </h2>
              <p className="text-red-100 mt-1">
                {deleteTarget.type === "subject" && `Delete entire ${formatSubjectName(deleteTarget.subject)} subject`}
                {deleteTarget.type === "class" && `Delete ${formatSubjectName(deleteTarget.subject)} Class ${deleteTarget.classLevel}`}
                {deleteTarget.type === "chapter" && `Delete ${formatSubjectName(deleteTarget.subject)} Class ${deleteTarget.classLevel} Chapter ${deleteTarget.chapter}`}
              </p>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 text-sm">
                  {getDeleteDescription()}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <span className="font-mono bg-gray-100 px-2 py-1 rounded text-red-600">{getDeleteConfirmationText()}</span> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder={getDeleteConfirmationText()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent font-mono"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeleteTarget(null);
                    setDeleteConfirmText("");
                  }}
                  variant="outline"
                  className="flex-1"
                  disabled={deleting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDelete}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                  disabled={deleting || deleteConfirmText !== getDeleteConfirmationText()}
                >
                  {deleting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Permanently
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
