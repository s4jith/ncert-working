import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    StickyNote,
    Plus,
    Search,
    Trash2,
    Edit3,
    BookOpen,
    MessageCircle,
    FileText,
    Calendar,
    ArrowLeft,
    X,
    Save
} from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import useNotesStore from '../stores/notesStore';

/**
 * Notes Page
 * 
 * Displays all user notes with search, filter, add, edit, and delete functionality.
 * Notes are stored locally via notesStore (with TODO for backend integration).
 */

export default function Notes() {
    const navigate = useNavigate();
    const { notes, addNote, updateNote, deleteNote, searchNotes } = useNotesStore();

    const [searchQuery, setSearchQuery] = useState('');
    const [filterSource, setFilterSource] = useState('all');
    const [showAddNote, setShowAddNote] = useState(false);
    const [editingNote, setEditingNote] = useState(null);
    const [newNote, setNewNote] = useState({ title: '', content: '' });

    // Filter and search notes
    const filteredNotes = searchQuery
        ? searchNotes(searchQuery)
        : filterSource === 'all'
            ? notes
            : notes.filter(n => n.source === filterSource);

    // Get source icon
    const getSourceIcon = (source) => {
        switch (source) {
            case 'Book to Bot':
                return <BookOpen className="w-4 h-4" />;
            case 'AI Chat':
                return <MessageCircle className="w-4 h-4" />;
            default:
                return <StickyNote className="w-4 h-4" />;
        }
    };

    // Get source color
    const getSourceColor = (source) => {
        switch (source) {
            case 'Book to Bot':
                return 'bg-emerald-50 text-emerald-600';
            case 'AI Chat':
                return 'bg-blue-50 text-blue-600';
            default:
                return 'bg-amber-50 text-amber-600';
        }
    };

    // Handle add note
    const handleAddNote = () => {
        if (newNote.title.trim() || newNote.content.trim()) {
            addNote({
                title: newNote.title || 'Untitled Note',
                content: newNote.content,
                source: 'Manual'
            });
            setNewNote({ title: '', content: '' });
            setShowAddNote(false);
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
        <DashboardLayout>
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="p-2 hover:bg-gray-100 rounded-lg"
                        >
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-800">Your Notes</h1>
                            <p className="text-gray-500">All your saved notes in one place</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowAddNote(true)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600"
                    >
                        <Plus className="w-5 h-5" />
                        Add Note
                    </button>
                </div>

                {/* Search and Filter */}
                <div className="flex items-center gap-4 mb-6">
                    <div className="flex-1 relative">
                        <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search notes..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 bg-white rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <select
                        value={filterSource}
                        onChange={(e) => setFilterSource(e.target.value)}
                        className="px-4 py-3 bg-white rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Sources</option>
                        <option value="Manual">Manual</option>
                        <option value="Book to Bot">Book to Bot</option>
                        <option value="AI Chat">AI Chat</option>
                    </select>
                </div>

                {/* Notes Grid */}
                {filteredNotes.length === 0 ? (
                    <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                        <StickyNote className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">No Notes Yet</h3>
                        <p className="text-gray-500 mb-6">Start taking notes while learning!</p>
                        <button
                            onClick={() => setShowAddNote(true)}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600"
                        >
                            <Plus className="w-5 h-5" />
                            Create Your First Note
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredNotes.map((note) => (
                            <div
                                key={note.id}
                                className="bg-white rounded-2xl p-5 border border-gray-100 hover:shadow-lg group"
                            >
                                {/* Note Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getSourceColor(note.source)}`}>
                                        {getSourceIcon(note.source)}
                                        {note.source}
                                    </span>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                                        <button
                                            onClick={() => setEditingNote(note)}
                                            className="p-1.5 hover:bg-gray-100 rounded-lg"
                                        >
                                            <Edit3 className="w-4 h-4 text-gray-500" />
                                        </button>
                                        <button
                                            onClick={() => deleteNote(note.id)}
                                            className="p-1.5 hover:bg-red-50 rounded-lg"
                                        >
                                            <Trash2 className="w-4 h-4 text-red-500" />
                                        </button>
                                    </div>
                                </div>

                                {/* Note Content */}
                                <h3 className="font-semibold text-gray-800 mb-2 line-clamp-1">{note.title}</h3>
                                <p className="text-sm text-gray-600 line-clamp-3 mb-4">{note.content}</p>

                                {/* Note Footer */}
                                <div className="flex items-center gap-2 text-xs text-gray-400">
                                    <Calendar className="w-3 h-3" />
                                    {new Date(note.createdAt).toLocaleDateString()}
                                    {note.sourceDetails && (
                                        <span className="ml-2 text-gray-500">• {note.sourceDetails}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Add Note Modal */}
                {showAddNote && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-2xl w-full max-w-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-800">Add New Note</h3>
                                <button onClick={() => setShowAddNote(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                                    <X className="w-5 h-5 text-gray-500" />
                                </button>
                            </div>
                            <input
                                type="text"
                                placeholder="Note title..."
                                value={newNote.title}
                                onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
                                className="w-full px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                            />
                            <textarea
                                placeholder="Write your note here..."
                                value={newNote.content}
                                onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
                                rows={6}
                                className="w-full px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4 resize-none"
                            />
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setShowAddNote(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-xl"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAddNote}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600"
                                >
                                    <Save className="w-4 h-4" />
                                    Save Note
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Edit Note Modal */}
                {editingNote && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-2xl w-full max-w-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-800">Edit Note</h3>
                                <button onClick={() => setEditingNote(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                                    <X className="w-5 h-5 text-gray-500" />
                                </button>
                            </div>
                            <input
                                type="text"
                                placeholder="Note title..."
                                value={editingNote.title}
                                onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
                                className="w-full px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                            />
                            <textarea
                                placeholder="Write your note here..."
                                value={editingNote.content}
                                onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
                                rows={6}
                                className="w-full px-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4 resize-none"
                            />
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setEditingNote(null)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-xl"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleUpdateNote}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600"
                                >
                                    <Save className="w-4 h-4" />
                                    Update Note
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
