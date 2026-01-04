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
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  XCircle,
  FileText,
  Layers,
  Settings
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Book Management Page for Admin
 * 
 * Features:
 * - View all uploaded books
 * - Upload new books (PDF + metadata)
 * - Delete books (from MongoDB + Pinecone)
 * - Sync existing books from frontend
 * - View Pinecone stats
 */

export default function BookManagement() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  
  // State
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null); // {stage, message, percent}
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSubject, setFilterSubject] = useState("all");
  const [filterClass, setFilterClass] = useState("all");
  const [pineconeStats, setPineconeStats] = useState(null);
  const [syncing, setSyncing] = useState(false);
  
  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    title: "",
    subject: "Mathematics",
    class_level: 6,
    chapter_number: 1,
    description: "",
    pdf_file: null
  });
  
  // Subjects and classes for filters
  const subjects = ["Mathematics", "Science", "Physics", "Chemistry", "Biology", "Social Science", "English", "Hindi"];
  const classes = [5, 6, 7, 8, 9, 10, 11, 12];
  
  useEffect(() => {
    fetchBooks();
    fetchPineconeStats();
  }, []);
  
  const fetchBooks = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/books/admin/list`);
      if (response.ok) {
        const data = await response.json();
        setBooks(data.books || []);
      } else if (response.status === 500) {
        // If list fails, try to fix missing fields first
        console.log("List failed, attempting to fix missing fields...");
        await handleFixMissingFields(true);
        // Try fetching again
        const retryResponse = await fetch(`${API_BASE}/api/books/admin/list`);
        if (retryResponse.ok) {
          const data = await retryResponse.json();
          setBooks(data.books || []);
        }
      }
    } catch (err) {
      console.error("Failed to fetch books:", err);
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
      
      setUploadProgress({ stage: "processing", message: "Processing PDF and generating embeddings... This may take several minutes for large books.", percent: 30 });
      
      const response = await fetch(`${API_BASE}/api/books/upload`, {
        method: "POST",
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setUploadProgress({ stage: "complete", message: "Upload complete!", percent: 100 });
        
        const embeddingInfo = data.embeddings 
          ? `\n\nEmbeddings: ${data.embeddings.embedding_count || 0} vectors created from ${data.embeddings.total_pages || 0} pages`
          : "";
        
        alert(`Book uploaded successfully!${embeddingInfo}`);
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
        fetchBooks();
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
  
  const handleDelete = async (bookId, bookTitle) => {
    if (!confirm(`Are you sure you want to delete "${bookTitle}"?\nThis will also remove embeddings from Pinecone.`)) {
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/api/books/${bookId}?delete_embeddings=true`, {
        method: "DELETE"
      });
      
      if (response.ok) {
        alert("Book deleted successfully!");
        fetchBooks();
        fetchPineconeStats();
      } else {
        const error = await response.json();
        alert(`Delete failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Delete failed. Please try again.");
    }
  };
  
  const handleSyncExisting = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/api/books/admin/sync-existing`, {
        method: "POST"
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(data.message);
        fetchBooks();
      } else {
        const error = await response.json();
        alert(`Sync failed: ${error.detail}`);
      }
    } catch (err) {
      console.error("Sync failed:", err);
      alert("Sync failed. Please try again.");
    } finally {
      setSyncing(false);
    }
  };
  
  const handleFixMissingFields = async (silent = false) => {
    if (!silent) setSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/api/books/admin/fix-missing-fields`, {
        method: "POST"
      });
      
      if (response.ok) {
        const data = await response.json();
        if (!silent) alert(data.message);
        fetchBooks();
        return true;
      } else {
        const error = await response.json();
        if (!silent) alert(`Fix failed: ${error.detail}`);
        return false;
      }
    } catch (err) {
      console.error("Fix failed:", err);
      if (!silent) alert("Fix failed. Please try again.");
      return false;
    } finally {
      if (!silent) setSyncing(false);
    }
  };
  
  const handleRegenerateEmbeddings = async (bookId, bookTitle) => {
    if (!confirm(`Regenerate embeddings for "${bookTitle}"?\n\nThis will process the PDF again and may take several minutes.`)) {
      return;
    }
    
    // Find the book and mark it as processing in UI
    setBooks(prev => prev.map(b => 
      b.id === bookId ? { ...b, processing_status: 'processing' } : b
    ));
    
    try {
      const response = await fetch(`${API_BASE}/api/books/${bookId}/regenerate-embeddings`, {
        method: "POST"
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`Embeddings regenerated!\n\n${data.details?.embedding_count || 0} vectors created from ${data.details?.total_pages || 0} pages.`);
        fetchBooks();
        fetchPineconeStats();
      } else {
        const error = await response.json();
        alert(`Failed: ${error.detail}`);
        fetchBooks();
      }
    } catch (err) {
      console.error("Regenerate failed:", err);
      alert("Failed to regenerate embeddings.");
      fetchBooks();
    }
  };
  
  // Filter books
  const filteredBooks = books.filter(book => {
    const matchesSearch = book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         book.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSubject = filterSubject === "all" || book.subject === filterSubject;
    const matchesClass = filterClass === "all" || book.class_level === parseInt(filterClass);
    return matchesSearch && matchesSubject && matchesClass;
  });
  
  // Get unique subjects from books
  const uniqueSubjects = [...new Set(books.map(b => b.subject))];
  const uniqueClasses = [...new Set(books.map(b => b.class_level))].sort((a, b) => a - b);
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/admin")}
                className="p-2 hover:bg-white/10 rounded-lg transition"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <BookOpen className="w-6 h-6" />
                  Book Management
                </h1>
                <p className="text-purple-200 text-sm">Manage textbooks and AI embeddings</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                onClick={() => handleFixMissingFields(false)}
                disabled={syncing}
                variant="outline"
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
                title="Fix any books with missing required fields"
              >
                {syncing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Settings className="w-4 h-4 mr-2" />}
                Fix Data
              </Button>
              <Button
                onClick={handleSyncExisting}
                disabled={syncing}
                variant="outline"
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                {syncing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                Sync Existing
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
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Pinecone Stats Card */}
        {pineconeStats && (
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-6 text-white mb-6">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6" />
              <h2 className="text-lg font-semibold">Pinecone Vector Database</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/20 rounded-xl p-4">
                <p className="text-green-100 text-sm">Total Vectors</p>
                <p className="text-2xl font-bold">{pineconeStats.total_vector_count?.toLocaleString() || 0}</p>
              </div>
              <div className="bg-white/20 rounded-xl p-4">
                <p className="text-green-100 text-sm">Dimension</p>
                <p className="text-2xl font-bold">{pineconeStats.dimension || 768}</p>
              </div>
              <div className="bg-white/20 rounded-xl p-4">
                <p className="text-green-100 text-sm">Namespaces</p>
                <p className="text-2xl font-bold">{Object.keys(pineconeStats.namespaces || {}).length}</p>
              </div>
              <div className="bg-white/20 rounded-xl p-4">
                <p className="text-green-100 text-sm">Status</p>
                <p className="text-lg font-bold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" /> Connected
                </p>
              </div>
            </div>
            {pineconeStats.namespaces && Object.keys(pineconeStats.namespaces).length > 0 && (
              <div className="mt-4">
                <p className="text-green-100 text-sm mb-2">Namespace Details:</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(pineconeStats.namespaces).map(([name, data]) => (
                    <span key={name} className="bg-white/20 px-3 py-1 rounded-full text-sm">
                      {name}: {data.vector_count?.toLocaleString() || 0} vectors
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Search and Filters */}
        <div className="bg-white rounded-xl p-4 shadow-sm mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search books..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <select
              value={filterSubject}
              onChange={(e) => setFilterSubject(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Subjects</option>
              {uniqueSubjects.map(subject => (
                <option key={subject} value={subject}>{subject}</option>
              ))}
            </select>
            
            <select
              value={filterClass}
              onChange={(e) => setFilterClass(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Classes</option>
              {uniqueClasses.map(cls => (
                <option key={cls} value={cls}>Class {cls}</option>
              ))}
            </select>
            
            <Button
              onClick={fetchBooks}
              variant="outline"
              size="icon"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Books Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        ) : filteredBooks.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center">
            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">No Books Found</h3>
            <p className="text-gray-500 mb-6">
              {books.length === 0 
                ? "Upload your first book or sync existing books from the system."
                : "No books match your search criteria."
              }
            </p>
            {books.length === 0 && (
              <div className="flex justify-center gap-3">
                <Button onClick={handleSyncExisting} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Sync Existing
                </Button>
                <Button onClick={() => setShowUploadModal(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Upload Book
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredBooks.map(book => (
              <div 
                key={book.id} 
                className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition"
              >
                {/* Book Header */}
                <div className="bg-gradient-to-r from-purple-500 to-indigo-500 p-4 text-white">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg line-clamp-1">{book.title}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="bg-white/20 px-2 py-0.5 rounded text-xs">{book.subject}</span>
                        <span className="bg-white/20 px-2 py-0.5 rounded text-xs">Class {book.class_level}</span>
                        {book.chapter_number && (
                          <span className="bg-white/20 px-2 py-0.5 rounded text-xs">Ch. {book.chapter_number}</span>
                        )}
                      </div>
                    </div>
                    <FileText className="w-8 h-8 opacity-50" />
                  </div>
                </div>
                
                {/* Book Body */}
                <div className="p-4">
                  <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                    {book.description || "No description available"}
                  </p>
                  
                  {/* Status */}
                  <div className="flex items-center gap-2 mb-4">
                    {book.processing_status === 'processing' ? (
                      <span className="flex items-center gap-1 text-blue-600 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Processing embeddings...
                      </span>
                    ) : book.has_embeddings ? (
                      <span className="flex items-center gap-1 text-green-600 text-sm">
                        <CheckCircle className="w-4 h-4" />
                        AI Ready ({book.embedding_count} embeddings)
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-600 text-sm">
                        <XCircle className="w-4 h-4" />
                        No AI embeddings
                      </span>
                    )}
                  </div>
                  
                  {/* Chapters */}
                  {book.chapters && book.chapters.length > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center gap-1 text-gray-500 text-sm mb-2">
                        <Layers className="w-4 h-4" />
                        {book.chapters.length} Chapters
                      </div>
                    </div>
                  )}
                  
                  {/* Actions */}
                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={() => window.open(`${API_BASE}${book.pdf_url}`, '_blank')}
                      variant="outline"
                      size="sm"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      View
                    </Button>
                    <Button
                      onClick={() => handleRegenerateEmbeddings(book.id, book.title)}
                      variant="outline"
                      size="sm"
                      disabled={book.processing_status === 'processing'}
                      className={!book.has_embeddings ? "text-amber-600 hover:bg-amber-50" : ""}
                    >
                      {book.processing_status === 'processing' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <RefreshCw className="w-4 h-4 mr-1" />
                          {book.has_embeddings ? "Refresh" : "Generate"}
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={() => handleDelete(book.id, book.title)}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50 hover:border-red-200"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {/* Footer */}
                <div className="px-4 py-3 bg-gray-50 text-xs text-gray-500">
                  Added: {new Date(book.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
      
      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 relative max-h-[90vh] overflow-y-auto">
            <button 
              onClick={() => setShowUploadModal(false)}
              className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
            >
              <XCircle className="w-5 h-5 text-gray-500" />
            </button>
            
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-purple-100 rounded-xl">
                <Upload className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-800">Upload New Book</h2>
                <p className="text-sm text-gray-500">Add a textbook to the library</p>
              </div>
            </div>
            
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Book Title *
                </label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
                  placeholder="e.g., Mathematics - Chapter 1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject *
                  </label>
                  <select
                    value={uploadForm.subject}
                    onChange={(e) => setUploadForm({ ...uploadForm, subject: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    required
                  >
                    {subjects.map(subject => (
                      <option key={subject} value={subject}>{subject}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Class Level *
                  </label>
                  <select
                    value={uploadForm.class_level}
                    onChange={(e) => setUploadForm({ ...uploadForm, class_level: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    required
                  >
                    {classes.map(cls => (
                      <option key={cls} value={cls}>Class {cls}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chapter # *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={uploadForm.chapter_number}
                    onChange={(e) => setUploadForm({ ...uploadForm, chapter_number: parseInt(e.target.value) })}
                    placeholder="1"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="Brief description of the book content..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  PDF File *
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-purple-500 transition cursor-pointer">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setUploadForm({ ...uploadForm, pdf_file: e.target.files[0] })}
                    className="hidden"
                    id="pdf-upload"
                    required
                  />
                  <label htmlFor="pdf-upload" className="cursor-pointer">
                    {uploadForm.pdf_file ? (
                      <div className="flex items-center justify-center gap-2 text-purple-600">
                        <FileText className="w-8 h-8" />
                        <span>{uploadForm.pdf_file.name}</span>
                      </div>
                    ) : (
                      <>
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-gray-500">Click to select PDF file</p>
                        <p className="text-xs text-gray-400 mt-1">or drag and drop</p>
                      </>
                    )}
                  </label>
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  onClick={() => { setShowUploadModal(false); setUploadProgress(null); }}
                  variant="outline"
                  className="flex-1"
                  disabled={uploading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={uploading}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Book
                    </>
                  )}
                </Button>
              </div>
              
              {/* Upload Progress Section */}
              {uploadProgress && (
                <div className={`mt-4 p-4 rounded-lg ${
                  uploadProgress.stage === 'error' ? 'bg-red-50 border border-red-200' :
                  uploadProgress.stage === 'complete' ? 'bg-green-50 border border-green-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-center gap-3 mb-2">
                    {uploadProgress.stage === 'error' ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : uploadProgress.stage === 'complete' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    )}
                    <span className={`font-medium ${
                      uploadProgress.stage === 'error' ? 'text-red-700' :
                      uploadProgress.stage === 'complete' ? 'text-green-700' :
                      'text-blue-700'
                    }`}>
                      {uploadProgress.stage === 'uploading' && 'Uploading...'}
                      {uploadProgress.stage === 'processing' && 'Processing PDF...'}
                      {uploadProgress.stage === 'complete' && 'Complete!'}
                      {uploadProgress.stage === 'error' && 'Error'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{uploadProgress.message}</p>
                  {uploadProgress.stage !== 'error' && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-500 ${
                          uploadProgress.stage === 'complete' ? 'bg-green-500' : 'bg-blue-500'
                        }`}
                        style={{ width: `${uploadProgress.percent}%` }}
                      />
                    </div>
                  )}
                </div>
              )}
            </form>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-blue-900 text-sm mb-2">
                <strong>📚 Chapter Organization:</strong> Upload one chapter at a time. All chapters for a subject (e.g., all Chemistry chapters from Class 6-12) are stored together for comprehensive AI retrieval.
              </p>
              <p className="text-blue-700 text-xs">
                <strong>⚡ Processing:</strong> Automatic text extraction, OCR, image analysis, and embedding generation. Large PDFs may take 5-10 minutes.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
