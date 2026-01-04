import { useState } from 'react';
import { X, Plus, Trash2, Edit3, Save, StickyNote } from 'lucide-react';
import useNotesStore from '../../stores/notesStore';

/**
 * StickyNotesCard Component
 * 
 * A funky, colorful sticky notes widget with hot pink, blue, and dark colors.
 * Displays recent notes as sticky note cards with add/edit functionality.
 */

// Funky color palette for sticky notes
const stickyColors = [
  { bg: 'bg-pink-500', text: 'text-white', shadow: 'shadow-pink-500/30' },
  { bg: 'bg-blue-500', text: 'text-white', shadow: 'shadow-blue-500/30' },
  { bg: 'bg-slate-100', text: 'text-white', shadow: 'shadow-slate-800/30' },
  { bg: 'bg-fuchsia-500', text: 'text-white', shadow: 'shadow-fuchsia-500/30' },
  { bg: 'bg-cyan-500', text: 'text-white', shadow: 'shadow-cyan-500/30' },
  { bg: 'bg-violet-600', text: 'text-white', shadow: 'shadow-violet-600/30' },
];

export default function StickyNotesCard() {
  const { notes, addNote, updateNote, deleteNote } = useNotesStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [newNote, setNewNote] = useState({ title: '', content: '' });

  // Get color based on note index
  const getColor = (index) => stickyColors[index % stickyColors.length];

  // Get recent notes (max 6)
  const recentNotes = notes.slice(0, 6);

  // Handle add note
  const handleAddNote = () => {
    if (newNote.title.trim() || newNote.content.trim()) {
      addNote({
        title: newNote.title || 'Quick Note',
        content: newNote.content,
        source: 'Sticky Note'
      });
      setNewNote({ title: '', content: '' });
      setShowAddModal(false);
    }
  };

  // Handle update note
  const handleUpdateNote = () => {
    if (editingNote) {
      updateNote(editingNote.id, {
        title: editingNote.title,
        content: editingNote.content
      });
      setEditingNote(null);
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-100 via-slate-300 to-slate-200 rounded-2xl p-6 border border-slate-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-grey-100 to-red-500 flex items-center justify-center">
            <StickyNote className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-black">Sticky Notes</h3>
            <p className="text-xs text-slate-400">{notes.length} notes</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="p-2 bg-gradient-to-r from-aliceblue-100 to-blue-500 rounded-lg text-white hover:opacity-90"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* Notes Grid */}
      {recentNotes.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-700 flex items-center justify-center">
            <StickyNote className="w-8 h-8 text-slate-500" />
          </div>
          <p className="text-slate-400 mb-3">No sticky notes yet</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-pink-200 to-blue-100 text-white text-sm font-medium rounded-lg hover:opacity-90"
          >
            Create Your First Note
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {recentNotes.map((note, index) => {
            const color = getColor(index);
            return (
              <div
                key={note.id}
                className={`${color.bg} ${color.text} ${color.shadow} rounded-xl p-4 shadow-lg group relative cursor-pointer hover:scale-105 transition-transform`}
                style={{ minHeight: '120px' }}
              >
                {/* Delete button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteNote(note.id);
                  }}
                  className="absolute top-2 right-2 p-1 bg-white/20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="w-3 h-3" />
                </button>

                {/* Edit button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingNote(note);
                  }}
                  className="absolute top-2 right-8 p-1 bg-white/20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Edit3 className="w-3 h-3" />
                </button>

                {/* Content */}
                <h4 className="font-bold text-sm mb-2 line-clamp-1">{note.title}</h4>
                <p className="text-xs opacity-80 line-clamp-3">{note.content}</p>

                {/* Folded corner effect */}
                <div className="absolute bottom-0 right-0 w-4 h-4 bg-white/10 rounded-tl-lg" />
              </div>
            );
          })}
        </div>
      )}

      {/* Add Note Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/10 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl w-full max-w-md p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-black">New Sticky Note</h3>
              <button onClick={() => setShowAddModal(false)} className="p-2 hover:bg-slate-700 rounded-lg">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <input
              type="text"
              placeholder="Note title..."
              value={newNote.title}
              onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
              className="w-full px-4 py-3 bg-slate-100 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-pink-500 text-white placeholder-slate-400 mb-4"
            />
            <textarea
              placeholder="Write your note..."
              value={newNote.content}
              onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 bg-slate-200 rounded-xl border border-slate-100 focus:outline-none focus:ring-2 focus:ring-pink-500 text-white placeholder-slate-400 mb-4 resize-none"
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-slate-400 hover:bg-slate-200 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleAddNote}
                className="px-4 py-2 bg-gradient-to-r from-aliceblue-100 to-blue-500 text-black rounded-xl font-medium hover:opacity-90 flex items-center gap-2"
              >
                <Save className="w-4 h-4 text-blue-100" />
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Note Modal */}
      {editingNote && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl w-full max-w-md p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Edit Note</h3>
              <button onClick={() => setEditingNote(null)} className="p-2 hover:bg-slate-700 rounded-lg">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <input
              type="text"
              placeholder="Note title..."
              value={editingNote.title}
              onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
              className="w-full px-4 py-3 bg-slate-700 rounded-xl border border-slate-600 focus:outline-none focus:ring-2 focus:ring-pink-500 text-white placeholder-slate-400 mb-4"
            />
            <textarea
              placeholder="Write your note..."
              value={editingNote.content}
              onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
              rows={4}
              className="w-full px-4 py-3 bg-slate-700 rounded-xl border border-slate-600 focus:outline-none focus:ring-2 focus:ring-pink-500 text-white placeholder-slate-400 mb-4 resize-none"
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setEditingNote(null)}
                className="px-4 py-2 text-slate-400 hover:bg-slate-700 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateNote}
                className="px-4 py-2 bg-gradient-to-r from-aliceblue-100 to-blue-500 text-white rounded-xl font-medium hover:opacity-90 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
