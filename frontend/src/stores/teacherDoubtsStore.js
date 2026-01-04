import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Teacher Doubts Store
 * 
 * Manages student doubts submitted to teachers.
 * Stores: studentName, studentId, question, subject
 */

const useTeacherDoubtsStore = create(
  persist(
    (set, get) => ({
      doubts: [],
      isSubmitting: false,
      lastSubmittedAt: null,
      
      // Add a new doubt locally
      addDoubt: (doubt) => {
        const newDoubt = {
          id: Date.now(),
          studentName: doubt.studentName,
          studentId: doubt.studentId,
          question: doubt.question,
          subject: doubt.subject || "General",
          status: "pending",
          createdAt: new Date().toISOString(),
          teacherResponse: null,
          respondedAt: null
        };
        
        set((state) => ({
          doubts: [newDoubt, ...state.doubts],
          lastSubmittedAt: new Date().toISOString()
        }));
        
        return newDoubt;
      },
      
      // Submit doubt (with backend integration placeholder)
      submitDoubt: async (doubtData) => {
        set({ isSubmitting: true });
        
        try {
          // TODO: Backend API call
          // const response = await fetch('/api/doubts', {
          //   method: 'POST',
          //   headers: { 'Content-Type': 'application/json' },
          //   body: JSON.stringify(doubtData)
          // });
          // const result = await response.json();
          
          // For now, just add locally
          const newDoubt = get().addDoubt(doubtData);
          
          set({ isSubmitting: false });
          return { success: true, doubt: newDoubt };
        } catch (error) {
          set({ isSubmitting: false });
          return { success: false, error: error.message };
        }
      },
      
      // Update doubt status
      updateDoubtStatus: (doubtId, status, response = null) => {
        set((state) => ({
          doubts: state.doubts.map((d) =>
            d.id === doubtId
              ? {
                  ...d,
                  status,
                  teacherResponse: response,
                  respondedAt: response ? new Date().toISOString() : null
                }
              : d
          )
        }));
      },
      
      // Delete a doubt
      deleteDoubt: (doubtId) => {
        set((state) => ({
          doubts: state.doubts.filter((d) => d.id !== doubtId)
        }));
      },
      
      // Get doubts by status
      getDoubtsByStatus: (status) => {
        return get().doubts.filter((d) => d.status === status);
      },
      
      // Get pending count
      getPendingCount: () => {
        return get().doubts.filter((d) => d.status === "pending").length;
      },
      
      // Clear all doubts
      clearDoubts: () => {
        set({ doubts: [], lastSubmittedAt: null });
      }
    }),
    {
      name: "teacher-doubts-storage",
      skipHydration: false
    }
  )
);

export default useTeacherDoubtsStore;
