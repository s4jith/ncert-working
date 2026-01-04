import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Notes Store
 * 
 * Manages user notes stored locally with persistence.
 * Notes can be saved from the Book to Bot feature when annotating text.
 * 
 * TODO: Backend Integration
 * - Replace localStorage persistence with API calls
 * - POST /api/notes/create - Create a new note
 * - GET /api/notes/user/{userId} - Fetch all notes for a user
 * - PUT /api/notes/{noteId} - Update a note
 * - DELETE /api/notes/{noteId} - Delete a note
 * - GET /api/notes/recent/{userId}?limit=3 - Get recent notes for dashboard
 */

const useNotesStore = create(
  persist(
    (set, get) => ({
      // Array of notes - each note has: id, title, content, source, createdAt, updatedAt
      notes: [],

      // Add a new note
      // TODO: Replace with API call - POST /api/notes/create
      addNote: (note) => {
        const newNote = {
          id: Date.now().toString(),
          title: note.title || 'Untitled Note',
          content: note.content,
          source: note.source || 'Manual', // e.g., 'Book to Bot', 'Manual', 'AI Chat'
          sourceDetails: note.sourceDetails || null, // e.g., book name, page number
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        set((state) => ({
          notes: [newNote, ...state.notes],
        }));
        return newNote;
      },

      // Update an existing note
      // TODO: Replace with API call - PUT /api/notes/{noteId}
      updateNote: (noteId, updates) => {
        set((state) => ({
          notes: state.notes.map((note) =>
            note.id === noteId
              ? { ...note, ...updates, updatedAt: new Date().toISOString() }
              : note
          ),
        }));
      },

      // Delete a note
      // TODO: Replace with API call - DELETE /api/notes/{noteId}
      deleteNote: (noteId) => {
        set((state) => ({
          notes: state.notes.filter((note) => note.id !== noteId),
        }));
      },

      // Get recent notes (for dashboard display)
      // TODO: Replace with API call - GET /api/notes/recent/{userId}?limit=3
      getRecentNotes: (limit = 3) => {
        const { notes } = get();
        return notes.slice(0, limit);
      },

      // Search notes by title or content
      searchNotes: (query) => {
        const { notes } = get();
        const lowerQuery = query.toLowerCase();
        return notes.filter(
          (note) =>
            note.title.toLowerCase().includes(lowerQuery) ||
            note.content.toLowerCase().includes(lowerQuery)
        );
      },

      // Get notes by source
      getNotesBySource: (source) => {
        const { notes } = get();
        return notes.filter((note) => note.source === source);
      },

      // Clear all notes
      clearAllNotes: () => {
        set({ notes: [] });
      },
    }),
    {
      name: 'brainwave-notes-storage', // localStorage key
    }
  )
);

export default useNotesStore;
