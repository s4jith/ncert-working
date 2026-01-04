import { useState, useEffect } from "react";
import { FileText, ChevronRight, BookOpen, Loader2 } from "lucide-react";
import { notesService } from "../../services/api";
import useUserStore from "../../stores/userStore";

/**
 * NotesDeckCard Component
 * 
 * Displays saved notes from lessons/PDFs.
 * Fetches real data from MongoDB via backend API.
 */

export default function NotesDeckCard() {
  const { user } = useUserStore();
  const [notes, setNotes] = useState([]);
  const [totalNotes, setTotalNotes] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNotes = async () => {
      const studentId = user.id || "guest";

      try {
        setLoading(true);
        const data = await notesService.getNotes(studentId, {
          subject: user.preferredSubject
        });
        
        // Format notes for display
        const formattedNotes = (data.notes || []).slice(0, 5).map(note => ({
          id: note.id,
          title: note.heading || note.note_content?.substring(0, 30) || "Untitled",
          lesson: `${note.subject} Ch ${note.chapter}`,
          date: formatDate(note.created_at),
          subject: note.subject
        }));
        
        setNotes(formattedNotes);
        setTotalNotes(data.total || 0);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch notes:", err);
        setError(err.message);
        setNotes([]);
        setTotalNotes(0);
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
  }, [user.id, user.preferredSubject]);

  const formatDate = (dateStr) => {
    if (!dateStr) return "Recent";
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-lime-500" />
          <h3 className="text-lg font-semibold text-gray-800">Notes Deck</h3>
        </div>
        <span className="text-sm text-gray-400">{totalNotes} notes</span>
      </div>

      <div className="space-y-2">
        {notes.length === 0 ? (
          <p className="text-center text-gray-400 py-4">
            No saved notes yet. Start reading and highlighting!
          </p>
        ) : (
          notes.map((note) => (
            <button
              key={note.id}
              className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors text-left group"
            >
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: '#b4ff06' }}
              >
                <FileText className="w-5 h-5 text-gray-800" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 truncate">{note.title}</p>
                <p className="text-xs text-gray-400">{note.lesson} • {note.date}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" />
            </button>
          ))
        )}
      </div>

      {totalNotes > 5 && (
        <button className="w-full mt-3 py-2 text-sm text-lime-600 hover:text-lime-700 font-medium transition-colors">
          View All {totalNotes} Notes →
        </button>
      )}

      {error && (
        <p className="text-xs text-amber-500 mt-2 text-center">
          Could not load notes
        </p>
      )}
    </div>
  );
}
