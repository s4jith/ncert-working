/**
 * User Store - Manages user profile and settings
 * Zustand store for user data including class level, subject preferences, etc.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * User Store
 * 
 * TODO: Backend Integration
 * - Load user profile from API on login
 * - Save preferences to backend
 * - Sync across devices
 */

const useUserStore = create(
  persist(
    (set, get) => ({
      // User Profile
      user: {
        id: null,
        name: "",
        email: "",
        classLevel: 10, // Default to Class 10 (matches our sample questions)
        preferredSubject: "Mathematics", // Default to Mathematics (has RAG support)
        role: null, // 'student' | 'teacher'
        isOnboarded: false,
        username: "",
        avatarSeed: "",
        avatarStyle: "avataaars",
      },

      // Previous Year Academics
      academics: {
        subjects: [], // Array of { name: string, marks: number }
      },

      // Exam Calendar
      calendar: {
        exams: [], // Array of { id: number, subject: string, date: string }
      },

      // Privacy Settings
      privacySettings: {
        showProfileToOthers: true,
        allowNotifications: true,
        shareProgressWithTeacher: true,
        dataCollectionConsent: true,
      },

      // Authentication state
      isAuthenticated: false,

      // Actions
      setUser: (userData) => set({ 
        user: { ...get().user, ...userData }, 
        isAuthenticated: true 
      }),

      setClassLevel: (classLevel) =>
        set((state) => ({
          user: { ...state.user, classLevel },
        })),

      setPreferredSubject: (subject) =>
        set((state) => ({
          user: { ...state.user, preferredSubject: subject },
        })),

      setOnboarded: (isOnboarded) =>
        set((state) => ({
          user: { ...state.user, isOnboarded },
        })),

      // Update profile info
      updateProfile: (profileData) =>
        set((state) => ({
          user: { ...state.user, ...profileData },
        })),

      // Update academics
      updateAcademics: (academicsData) =>
        set((state) => ({
          academics: { ...state.academics, ...academicsData },
        })),

      // Update calendar
      updateCalendar: (calendarData) =>
        set((state) => ({
          calendar: { ...state.calendar, ...calendarData },
        })),

      // Update privacy settings
      updatePrivacySettings: (settings) =>
        set((state) => ({
          privacySettings: { ...state.privacySettings, ...settings },
        })),

      logout: () =>
        set({
          user: {
            id: null,
            name: "",
            email: "",
            classLevel: 6,
            preferredSubject: "Mathematics", // Default to Mathematics (has RAG support)
            role: null,
            isOnboarded: false,
            username: "",
            avatarSeed: "",
            avatarStyle: "avataaars",
          },
          academics: { subjects: [] },
          calendar: { exams: [] },
          privacySettings: {
            showProfileToOthers: true,
            allowNotifications: true,
            shareProgressWithTeacher: true,
            dataCollectionConsent: true,
          },
          isAuthenticated: false,
        }),

      // Get current class level
      getClassLevel: () => get().user.classLevel,

      // Get current subject
      getSubject: () => get().user.preferredSubject,
    }),
    {
      name: "user-storage", // LocalStorage key
      skipHydration: false, // Enable hydration
      partialize: (state) => ({
        user: state.user,
        academics: state.academics,
        calendar: state.calendar,
        privacySettings: state.privacySettings,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useUserStore;
