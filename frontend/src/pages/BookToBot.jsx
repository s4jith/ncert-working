import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PDFViewer from "../features/pdf/PDFViewer";
import LessonNavigation from "../features/lessons/LessonNavigation";
import UserSettingsPanel from "../components/UserSettingsPanel";
import ChatbotPanel from "../components/dashboard/ChatbotPanel";
import { SUBJECTS_WITH_RAG } from "../constants/lessons";
import { Menu, X, Settings, MessageCircle, AlertTriangle, ArrowLeft, BookOpen, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import useUserStore from "../stores/userStore";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * BookToBot Component
 *
 * PDF viewer interface with lesson navigation and AI chatbot.
 * Dynamically loads lessons/books from MongoDB based on user's class level.
 * Student can only select subject (class is fixed based on profile).
 * 
 * AI features (chatbot, annotations) only work for subjects with embeddings in Pinecone.
 */

function BookToBot() {
  const navigate = useNavigate();
  const { user, setPreferredSubject } = useUserStore();

  // State for available subjects and lessons from DB
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingLessons, setLoadingLessons] = useState(false);
  
  // UI State
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);

  // Check if current subject has AI/RAG support
  const hasAISupport = currentLesson?.has_ai_support || SUBJECTS_WITH_RAG.includes(user.preferredSubject);

  // Fetch available subjects for student's class level
  useEffect(() => {
    fetchAvailableSubjects();
  }, [user.classLevel]);

  // Fetch lessons when subject changes
  useEffect(() => {
    if (user.preferredSubject) {
      fetchLessons(user.preferredSubject);
    }
  }, [user.preferredSubject, user.classLevel]);

  const fetchAvailableSubjects = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/books/student/subjects?class_level=${user.classLevel}`);
      
      if (response.ok) {
        const data = await response.json();
        const subjects = data.subjects || [];
        setAvailableSubjects(subjects);
        
        // If no subjects from DB, show empty state
        if (subjects.length === 0) {
          setLessons([]);
          setCurrentLesson(null);
        } else {
          // Check if user's preferred subject is available
          const subjectNames = subjects.map(s => s.name);
          if (!subjectNames.includes(user.preferredSubject)) {
            // Switch to first available subject
            setPreferredSubject(subjectNames[0]);
          }
        }
      } else {
        // API failed - show empty state, don't use static fallback
        setLessons([]);
        setCurrentLesson(null);
      }
    } catch (err) {
      console.error("Failed to fetch subjects:", err);
      // Error - show empty state, don't use static fallback
      setLessons([]);
      setCurrentLesson(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchLessons = async (subject) => {
    try {
      setLoadingLessons(true);
      const response = await fetch(
        `${API_BASE}/api/books/student/lessons?class_level=${user.classLevel}&subject=${encodeURIComponent(subject)}`
      );
      
      if (response.ok) {
        const data = await response.json();
        const fetchedLessons = data.lessons || [];
        
        // Convert relative PDF URLs to absolute URLs
        const lessonsWithAbsoluteUrls = fetchedLessons.map(lesson => ({
          ...lesson,
          pdfUrl: lesson.pdfUrl?.startsWith('http') ? lesson.pdfUrl : `${API_BASE}${lesson.pdfUrl}`
        }));
        
        // Always use fetched lessons - never fall back to static data
        setLessons(lessonsWithAbsoluteUrls);
        setCurrentLesson(lessonsWithAbsoluteUrls.length > 0 ? lessonsWithAbsoluteUrls[0] : null);
      } else {
        // API failed - show empty state
        setLessons([]);
        setCurrentLesson(null);
      }
    } catch (err) {
      console.error("Failed to fetch lessons:", err);
      // Error - show empty state
      setLessons([]);
      setCurrentLesson(null);
    } finally {
      setLoadingLessons(false);
    }
  };

  const handleLessonSelect = (lesson) => {
    setCurrentLesson(lesson);
  };

  const handleSubjectChange = (subject) => {
    setPreferredSubject(subject);
  };

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading books...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar - Lesson Navigation */}
      <div
        className={`flex-shrink-0 transition-all duration-300 ease-in-out ${
          sidebarOpen ? "w-80" : "w-0"
        } overflow-hidden border-r`}
      >
        <div className="h-full flex flex-col">
          {/* Subject Selector - Only show available subjects from DB */}
          <div className="p-4 border-b bg-muted/30">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">Select Subject</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {availableSubjects.length > 0 ? (
                availableSubjects.map((subject) => (
                  <Button
                    key={subject.name}
                    variant={user.preferredSubject === subject.name ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleSubjectChange(subject.name)}
                    className="text-xs"
                  >
                    {subject.name}
                    {subject.has_ai_support && (
                      <span className="ml-1 text-[10px] bg-green-500/20 text-green-700 px-1 rounded">AI</span>
                    )}
                  </Button>
                ))
              ) : (
                ["Mathematics", "Social Science"].map((subject) => (
                  <Button
                    key={subject}
                    variant={user.preferredSubject === subject ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleSubjectChange(subject)}
                    className="text-xs"
                  >
                    {subject}
                  </Button>
                ))
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Class {user.classLevel} • {lessons.length} Lessons Available
            </p>
          </div>
          
          {/* Lessons List */}
          {loadingLessons ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <LessonNavigation
              lessons={lessons}
              currentLesson={currentLesson}
              onLessonSelect={handleLessonSelect}
            />
          )}
        </div>
      </div>

      {/* Main Content - PDF Viewer */}
      <div className="flex-1 flex flex-col">
        {/* AI Support Warning Banner */}
        {!hasAISupport && (
          <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <p className="text-sm text-amber-800">
              AI features are not available for {user.preferredSubject} yet.
              Switch to a subject with AI support for full features.
            </p>
          </div>
        )}

        {/* Header */}
        <div className="px-6 py-4 border-b bg-card flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/dashboard')}
            className="hover:bg-primary/10 gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </Button>

          <div className="w-px h-6 bg-border" />

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hover:bg-primary/10"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          <div className="flex-1">
            <h1 className="text-2xl font-bold text-primary">
              {currentLesson?.title || "Select a lesson"}
            </h1>
            {currentLesson?.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {currentLesson.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right mr-2">
              <p className="text-xs text-muted-foreground">Class {user.classLevel}</p>
              <p className="text-xs font-medium">{user.preferredSubject}</p>
            </div>

            <Button
              variant="default"
              size="sm"
              onClick={() => setChatbotOpen(true)}
              className="bg-primary hover:bg-primary/90"
              disabled={!hasAISupport}
            >
              <MessageCircle className="h-4 w-4 mr-2" />
              AI Chat
            </Button>

            <Button
              variant="outline"
              size="icon"
              onClick={() => setSettingsOpen(true)}
              className="hover:bg-primary/10"
            >
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* PDF Viewer */}
        <div className="flex-1 overflow-hidden">
          {currentLesson ? (
            <PDFViewer
              pdfUrl={currentLesson.pdfUrl}
              currentLesson={currentLesson}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <BookOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-lg font-medium text-muted-foreground">No lessons available</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Select a different subject or contact your admin
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <UserSettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />

      <ChatbotPanel
        isOpen={chatbotOpen}
        onClose={() => setChatbotOpen(false)}
      />
    </div>
  );
}

export default BookToBot;
