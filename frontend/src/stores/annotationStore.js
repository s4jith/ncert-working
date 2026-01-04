import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

/**
 * Zustand Store for Annotation Management
 *
 * This store manages all annotation-related state including:
 * - Annotations (notes and AI interactions)
 * - Selected text and active panels
 * - UI state for annotation features
 *
 * BACKEND INTEGRATION POINTS:
 * ============================
 * TODO: Replace local state with API calls in the following actions:
 *
 * 1. addNote() - Call POST /api/annotations with note data
 * 2. addAIAnnotation() - Call POST /api/annotations/ai with AI annotation data
 * 3. updateAIResponse() - Call PATCH /api/annotations/:id with updated response
 * 4. deleteAnnotation() - Call DELETE /api/annotations/:id
 * 5. Initialize store - Call GET /api/annotations on app load
 * 6. getAnnotationsByLesson() - Call GET /api/annotations?lessonId=:id
 * 7. getAnnotationsByPage() - Call GET /api/annotations?lessonId=:id&pageNumber=:num
 *
 * Example API service integration:
 * import { annotationService } from '@/services/api';
 *
 * Then replace:
 * setAnnotations((prev) => [...prev, newAnnotation]);
 *
 * With:
 * const savedAnnotation = await annotationService.create(newAnnotation);
 * setAnnotations((prev) => [...prev, savedAnnotation]);
 */

const useAnnotationStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        annotations: [],
        selectedText: null,
        activePanel: null, // 'ai' | 'note' | 'history' | null
        viewingAnnotation: null,

        // Actions
        setSelectedText: (text) => set({ selectedText: text }),

        setActivePanel: (panel) => set({ activePanel: panel }),

        setViewingAnnotation: (annotation) =>
          set({ viewingAnnotation: annotation }),

        // Add a note annotation
        // TODO: Integrate with backend API - POST /api/annotations
        addNote: (data) => {
          const newAnnotation = {
            id: Date.now(), // TODO: Replace with server-generated ID
            type: "note",
            text: data.text,
            heading: data.heading,
            content: data.content,
            pageNumber: data.pageNumber,
            position: data.position,
            timestamp: new Date().toISOString(),
            lessonId: data.lessonId,
          };

          set((state) => ({
            annotations: [...state.annotations, newAnnotation],
            activePanel: null,
            selectedText: null,
          }));

          return newAnnotation;
        },

        // Add an AI annotation
        // TODO: Integrate with backend API - POST /api/annotations/ai
        // Also integrate with AI service to get actual AI responses
        addAIAnnotation: (data) => {
          const newAnnotation = {
            id: Date.now(), // TODO: Replace with server-generated ID
            type: "ai",
            text: data.text,
            action: data.action, // 'simplify' | 'refine' | 'examples' | 'explain'
            response: data.response,
            pageNumber: data.pageNumber,
            position: data.position,
            timestamp: new Date().toISOString(),
            lessonId: data.lessonId,
          };

          set((state) => ({
            annotations: [...state.annotations, newAnnotation],
          }));

          return newAnnotation;
        },

        // Update AI annotation with response
        // TODO: Integrate with backend API - PATCH /api/annotations/:id
        updateAIResponse: (id, response) => {
          set((state) => ({
            annotations: state.annotations.map((ann) =>
              ann.id === id ? { ...ann, response } : ann
            ),
          }));
        },

        // Delete annotation
        // TODO: Integrate with backend API - DELETE /api/annotations/:id
        deleteAnnotation: (id) => {
          set((state) => ({
            annotations: state.annotations.filter((ann) => ann.id !== id),
          }));
        },

        // Get annotations for current lesson
        // TODO: Consider backend pagination - GET /api/annotations?lessonId=:id&page=:num
        getAnnotationsByLesson: (lessonId) => {
          return get().annotations.filter((ann) => ann.lessonId === lessonId);
        },

        // Get annotations by page
        // TODO: Optimize with backend query - GET /api/annotations?lessonId=:id&pageNumber=:num
        getAnnotationsByPage: (lessonId, pageNumber) => {
          return get().annotations.filter(
            (ann) => ann.lessonId === lessonId && ann.pageNumber === pageNumber
          );
        },

        // TODO: Add sync action to fetch all annotations from backend on app load
        // syncAnnotations: async () => {
        //   const annotations = await annotationService.fetchAll();
        //   set({ annotations });
        // },
      }),
      {
        name: "annotation-storage", // LocalStorage key
        // TODO: Remove persist middleware when backend is integrated
        // or keep for offline support with sync mechanism
      }
    )
  )
);

export default useAnnotationStore;
