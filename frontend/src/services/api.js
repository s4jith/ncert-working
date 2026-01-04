/**
 * API Service - Backend Integration
 * 
 * This file contains all API calls to the FastAPI backend
 * Base URL: http://localhost:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Chat Service - AI Explanations with RAG
 * Integrates with the backend RAG system for annotations and assessment
 */
export const chatService = {
  /**
   * Process annotation with AI (Define, Elaborate, Stick Flow)
   * UNIFIED ENDPOINT - Main function for text annotations
   * @param {string} text - The selected text to process
   * @param {string} action - Action type: "define", "elaborate", or "stick_flow"
   * @param {number} classLevel - User's class level (5-10)
   * @param {string} subject - Subject name
   * @param {number} chapter - Chapter number
   * @returns {Promise<{answer: string, action_type: string, source_count: number}>}
   */
  async processAnnotation(text, action, classLevel, subject, chapter) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/annotation/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          selected_text: text,
          action: action,
          class_level: classLevel,
          subject: subject,
          chapter: chapter,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        answer: data.answer,
        actionType: data.action_type,
        sourceCount: data.source_count,
      };
    } catch (error) {
      console.error("Annotation API Error:", error);
      throw error;
    }
  },

  /**
   * @deprecated Use processAnnotation() instead
   * Get AI explanation for selected text
   */
  async getExplanation(text, mode, classLevel, subject, chapter) {
    return this.processAnnotation(text, mode, classLevel, subject, chapter);
  },

  /**
   * @deprecated Use processAnnotation() with action="stick_flow" instead
   * Get Stick Flow visual diagram
   */
  async getStickFlow(text, classLevel, subject, chapter) {
    return this.processAnnotation(text, "stick_flow", classLevel, subject, chapter);
  },

  /**
   * Student chatbot - Open-ended questions with RAG
   * @param {string} question - Student's question
   * @param {number} classLevel - User's class level (5-10)
   * @param {string} subject - Subject name
   * @param {number} chapter - Chapter number
   * @param {string} mode - Chat mode: "quick" (exam-style) or "deepdive" (comprehensive)
   * @returns {Promise<{answer: string, sources: array}>}
   */
  async studentChat(question, classLevel, subject, chapter, mode = "quick") {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/student`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question,
          class_level: classLevel,
          subject: subject,
          chapter: chapter,
          mode: mode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Student Chat API Error: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        answer: data.answer,
        sources: data.source_chunks || [],
      };
    } catch (error) {
      console.error("Student Chat API Error:", error);
      throw error;
    }
  },

  /**
   * Image-based chat - Upload photo of textbook/diagram/handwritten question
   * Uses Intel OpenVINO OCR to extract text and generate RAG answer
   * @param {File} imageFile - Image file (jpg/png, max 5MB)
   * @param {number} classLevel - User's class level (5-12)
   * @param {string} subject - Subject name
   * @param {number} chapter - Chapter number
   * @param {string} mode - Chat mode: "quick" or "deepdive"
   * @returns {Promise<{answer: string, sources: array, imageAnalysis: object}>}
   */
  async imageChat(imageFile, classLevel, subject, chapter, mode = "quick", userQuery = null) {
    try {
      const formData = new FormData();
      formData.append("image", imageFile);
      formData.append("class_level", classLevel);
      formData.append("subject", subject);
      formData.append("chapter", chapter);
      formData.append("mode", mode);
      if (userQuery) {
        formData.append("user_query", userQuery);
      }

      const response = await fetch(`${API_BASE_URL}/api/chat/image`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Image Chat API Error: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        answer: data.answer,
        sources: data.source_chunks || [],
        imageAnalysis: data.image_analysis || {},
      };
    } catch (error) {
      console.error("Image Chat API Error:", error);
      throw error;
    }
  },
};

/**
 * Assessment Service - Voice Assessment Integration
 */
export const assessmentService = {
  /**
   * Get enhanced assessment questions (15 questions for 10-page interval)
   */
  async getEnhancedQuestions(classLevel, subject, chapter, lessonName, pageRange, studentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/assessment/questions/enhanced`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          class_level: classLevel,
          subject: subject,
          chapter: chapter,
          lesson_name: lessonName,
          page_range: pageRange,
          student_id: studentId,
          force_regenerate: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`Enhanced Questions API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Enhanced Questions API Error:", error);
      throw error;
    }
  },

  /**
   * Get assessment questions from textbook content (RAG-based)
   */
  async getQuestions(classLevel, subject, chapter, numQuestions = 3) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/assessment/questions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          class_level: classLevel,
          subject: subject,
          chapter: chapter,
          num_questions: numQuestions,
        }),
      });

      if (!response.ok) {
        throw new Error(`Assessment API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Assessment Questions API Error:", error);
      throw error;
    }
  },

  /**
   * Evaluate voice assessment answers
   */
  async evaluateAnswers(classLevel, subject, chapter, answers) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/assessment/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          class_level: classLevel,
          subject: subject,
          chapter: chapter,
          answers: answers,
        }),
      });

      if (!response.ok) {
        throw new Error(`Evaluation API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Assessment Evaluation API Error:", error);
      throw error;
    }
  },
};

/**
 * User Stats Service - Dashboard data (progress, streaks, notes)
 */
export const userStatsService = {
  /**
   * Get all dashboard data in one call
   * @param {string} studentId - Student identifier
   * @param {string} subject - Optional subject filter
   * @returns {Promise<{streak, progress, recent_notes, total_notes}>}
   */
  async getDashboardData(studentId, subject = null) {
    try {
      let url = `${API_BASE_URL}/api/user/dashboard/${studentId}`;
      if (subject) {
        url += `?subject=${encodeURIComponent(subject)}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Dashboard API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Dashboard API Error:", error);
      throw error;
    }
  },

  /**
   * Get streak data only
   * @param {string} studentId - Student identifier
   * @returns {Promise<{current_streak, longest_streak, weekly_activity}>}
   */
  async getStreakData(studentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/streak/${studentId}`);

      if (!response.ok) {
        throw new Error(`Streak API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Streak API Error:", error);
      throw error;
    }
  },

  /**
   * Get progress data only
   * @param {string} studentId - Student identifier
   * @param {string} subject - Optional subject filter
   * @returns {Promise<{overall_progress, total_tests, completed_tests, average_score}>}
   */
  async getProgressData(studentId, subject = null) {
    try {
      let url = `${API_BASE_URL}/api/user/progress/${studentId}`;
      if (subject) {
        url += `?subject=${encodeURIComponent(subject)}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Progress API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Progress API Error:", error);
      throw error;
    }
  },

  /**
   * Log user activity for streak tracking
   * @param {string} studentId - Student identifier
   * @param {number} hours - Hours of activity (default 0.5)
   */
  async logActivity(studentId, hours = 0.5) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/user/activity/log?student_id=${studentId}&hours=${hours}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`Activity Log API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Activity Log API Error:", error);
      // Don't throw - activity logging shouldn't break the app
    }
  },
};

/**
 * Notes Service - User saved notes
 */
export const notesService = {
  /**
   * Get notes for a student
   * @param {string} studentId - Student identifier
   * @param {object} filters - Optional filters (class_level, subject, chapter)
   * @returns {Promise<{notes: array, total: number}>}
   */
  async getNotes(studentId, filters = {}) {
    try {
      let url = `${API_BASE_URL}/api/notes/${studentId}`;
      const params = new URLSearchParams();

      if (filters.class_level) params.append("class_level", filters.class_level);
      if (filters.subject) params.append("subject", filters.subject);
      if (filters.chapter) params.append("chapter", filters.chapter);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Notes API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Notes API Error:", error);
      throw error;
    }
  },

  /**
   * Create a new note
   * @param {object} noteData - Note data
   * @returns {Promise<Note>}
   */
  async createNote(noteData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notes/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(noteData),
      });

      if (!response.ok) {
        throw new Error(`Create Note API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Create Note API Error:", error);
      throw error;
    }
  },
};

/**
 * Test Service - AI and Staff Tests
 */
export const testService = {
  // ==================== TOPIC-BASED TEST SELECTION ====================

  /**
   * Get available subjects for a class level
   * @param {number} classLevel - Class level (5-12)
   * @returns {Promise<array>} - List of subjects with chapter/question counts
   */
  async getAvailableSubjects(classLevel) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/subjects/${classLevel}`);
      if (!response.ok) throw new Error(`Subjects API Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Get Subjects Error:", error);
      return [];
    }
  },

  /**
   * Get chapters for a subject
   * @param {number} classLevel - Class level
   * @param {string} subject - Subject name
   * @returns {Promise<array>} - List of chapters with topic/question counts
   */
  async getChaptersForSubject(classLevel, subject, studentId = null) {
    try {
      const params = studentId ? `?student_id=${studentId}` : '';
      const response = await fetch(
        `${API_BASE_URL}/api/test/chapters/${classLevel}/${encodeURIComponent(subject)}${params}`
      );
      if (!response.ok) throw new Error(`Chapters API Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Get Chapters Error:", error);
      return [];
    }
  },

  /**
   * Get topics for a chapter with student performance
   * @param {number} classLevel - Class level
   * @param {string} subject - Subject name
   * @param {number} chapterNumber - Chapter number
   * @param {string} studentId - Student ID for performance data
   * @returns {Promise<array>} - Topics with student scores and recommendations
   */
  async getTopicsForChapter(classLevel, subject, chapterNumber, studentId = null) {
    try {
      const params = studentId ? `?student_id=${studentId}` : '';
      const response = await fetch(
        `${API_BASE_URL}/api/test/topics/${classLevel}/${encodeURIComponent(subject)}/${chapterNumber}${params}`
      );
      if (!response.ok) throw new Error(`Topics API Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Get Topics Error:", error);
      return [];
    }
  },

  /**
   * Get personalized topic recommendations for student
   * @param {number} classLevel - Class level
   * @param {string} subject - Subject name
   * @param {string} studentId - Student ID
   * @param {number} limit - Max recommendations
   * @returns {Promise<array>} - Recommended topics based on weak areas
   */
  async getRecommendations(classLevel, subject, studentId, limit = 5) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/test/recommendations/${classLevel}/${encodeURIComponent(subject)}/${studentId}?limit=${limit}`
      );
      if (!response.ok) throw new Error(`Recommendations API Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Get Recommendations Error:", error);
      return [];
    }
  },

  // ==================== AI TEST SESSION ====================

  /**
   * Start a topic-based AI test
   * @param {object} params - Test parameters
   * @returns {Promise<{session_id, questions, time_limit}>}
   */
  async startTopicTest(params) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: params.studentId,
          class_level: params.classLevel || 10,
          subject: params.subject,
          chapter_number: params.chapter_number,
          topic_id: params.topic_id,
          num_questions: params.num_questions || 5,
          difficulty: params.difficulty || "mixed"
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Start Test Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Start Topic Test Error:", error);
      throw error;
    }
  },

  /**
   * Submit a single answer during test
   * @param {string} sessionId - Session ID
   * @param {string} questionId - Question ID
   * @param {number} questionNumber - Question number
   * @param {string} answer - Student's answer
   * @returns {Promise<{status: string}>}
   */
  async submitAnswer(sessionId, questionId, questionNumber, answer) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: questionId,
          question_number: questionNumber,
          answer: answer,
        }),
      });

      if (!response.ok) throw new Error(`Submit Answer Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Submit Answer Error:", error);
      throw error;
    }
  },

  /**
   * Complete test and get RAG-based evaluation
   * @param {string} sessionId - Session ID
   * @param {string} studentId - Student ID
   * @returns {Promise<{score, evaluations, feedback, strengths, improvements}>}
   */
  async completeTest(sessionId, studentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
        }),
      });

      if (!response.ok) throw new Error(`Complete Test Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Complete Test Error:", error);
      throw error;
    }
  },

  /**
   * Start Test V2 - Supports on-demand generation
   * @param {object} params - Test parameters
   * @returns {Promise<{session_id, questions, time_limit}>}
   */
  async startTestV2(params) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/start-v3`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: params.studentId,
          class_level: params.classLevel || 10,
          subject: params.subject,
          chapter_number: params.chapter_number,
          topic_id: params.topic_id || "all",
          num_questions: params.num_questions || 15,
          total_marks: params.total_marks || 25,
          difficulty: params.difficulty || "mixed",
          auto_generate: params.auto_generate || true
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Start Test V2 Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Start Test V2 Error:", error);
      throw error;
    }
  },

  /**
   * Check if questions are available for a chapter
   * @param {number} classLevel
   * @param {string} subject
   * @param {number} chapterNumber
   * @returns {Promise<{available, count, difficulty_distribution}>}
   */
  async checkQuestionsAvailable(classLevel, subject, chapterNumber) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/test/check-questions/${classLevel}/${encodeURIComponent(subject)}/${chapterNumber}`
      );
      if (!response.ok) throw new Error(`Check Questions Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Check Questions Error:", error);
      return { available: false, count: 0 };
    }
  },

  /**
   * Get student analytics
   * @param {string} studentId
   * @param {number} classLevel
   * @param {string} subject
   * @returns {Promise<object>}
   */
  async getStudentAnalytics(studentId, classLevel = 10, subject = null) {
    try {
      const params = new URLSearchParams();
      params.append("class_level", classLevel);
      if (subject) params.append("subject", subject);

      const response = await fetch(
        `${API_BASE_URL}/api/test/analytics/${studentId}?${params.toString()}`
      );
      if (!response.ok) throw new Error(`Analytics API Error: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error("Get Analytics Error:", error);
      return null;
    }
  },

  // ==================== LEGACY AI TEST ENDPOINTS (kept for compatibility) ====================

  /**
   * Get AI tests available
   * @param {string} subject - Optional subject filter
   * @param {number} chapter - Optional chapter filter
   * @param {string} studentId - Student ID for best scores
   * @returns {Promise<array>}
   */
  async getAITests(subject = null, chapter = null, studentId = null) {
    try {
      const params = new URLSearchParams();
      if (subject) params.append("subject", subject);
      if (chapter) params.append("chapter", chapter);
      if (studentId) params.append("student_id", studentId);

      const url = `${API_BASE_URL}/api/test/ai-tests${params.toString() ? '?' + params.toString() : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`AI Tests API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("AI Tests API Error:", error);
      return [];
    }
  },

  /**
   * Start an AI test session (legacy)
   * @param {string} testId - Test ID
   * @param {string} studentId - Student ID
   * @returns {Promise<{session_id, questions, time_limit}>}
   */
  async startAITest(testId, studentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/ai-tests/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test_id: testId, student_id: studentId }),
      });

      if (!response.ok) {
        throw new Error(`Start AI Test API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Start AI Test API Error:", error);
      throw error;
    }
  },

  /**
   * Submit a single answer during AI test (legacy)
   * @param {string} sessionId - Session ID
   * @param {number} questionNumber - Question number
   * @param {string} answer - Student's answer
   * @returns {Promise<{status: string}>}
   */
  async submitAIAnswer(sessionId, questionNumber, answer) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/ai-tests/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question_number: questionNumber,
          answer: answer,
        }),
      });

      if (!response.ok) {
        throw new Error(`Submit Answer API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Submit Answer API Error:", error);
      throw error;
    }
  },

  /**
   * Complete AI test and get results (legacy)
   * @param {string} sessionId - Session ID
   * @param {string} studentId - Student ID
   * @returns {Promise<{score, feedback, question_results, topics_to_review}>}
   */
  async completeAITest(sessionId, studentId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/ai-tests/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Complete AI Test API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Complete AI Test API Error:", error);
      throw error;
    }
  },

  /**
   * Get staff-assigned tests for a student
   * @param {string} subject - Optional subject filter (not used, kept for compatibility)
   * @param {number} chapter - Optional chapter filter (not used, kept for compatibility)
   * @param {string} studentId - Student ID for getting tests for their class
   * @returns {Promise<array>}
   */
  async getStaffTests(subject = null, chapter = null, studentId = null) {
    try {
      if (!studentId) {
        console.error("Student ID is required");
        return [];
      }

      const url = `${API_BASE_URL}/api/tests/student/${studentId}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Staff Tests API Error: ${response.statusText}`);
      }

      const data = await response.json();

      // Backend returns array directly
      if (Array.isArray(data)) {
        return data.map(test => ({
          id: test.id,
          title: test.title,
          description: test.description,
          subject: test.subject,
          class_level: test.class_level,
          pdf_filename: test.pdf_filename,
          pdf_url: test.pdf_url,
          start_date: test.start_datetime,  // Map from start_datetime
          due_date: test.end_datetime,      // Map from end_datetime
          created_at: test.created_at,
          created_by: test.created_by,
          status: test.status || 'active',
          is_timed: test.is_timed,
          has_submitted: test.has_submitted,
          submission_id: test.submission_id,
          submission_date: test.submission_date,
          has_feedback: test.has_feedback
        }));
      }

      return [];
    } catch (error) {
      console.error("Staff Tests API Error:", error);
      return [];
    }
  },

  /**
   * Download question paper PDF
   * @param {string} filename - PDF filename
   * @returns {string} - Download URL
   */
  getQuestionPaperUrl(filename) {
    return `${API_BASE_URL}/api/tests/pdf/${filename}`;
  },

  /**
   * Upload answer sheet for a staff test
   * @param {string} testId - Test ID
   * @param {string} studentId - Student ID
   * @param {File} file - PDF file to upload
   * @returns {Promise<{success, submission_id, message}>}
   */
  async uploadAnswerSheet(testId, studentId, file) {
    try {
      const formData = new FormData();
      formData.append("submission_file", file);
      formData.append("test_id", testId);
      formData.append("student_id", studentId);

      const response = await fetch(`${API_BASE_URL}/api/tests/submit`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload Answer API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Upload Answer API Error:", error);
      throw error;
    }
  },

  /**
   * Get test analytics for a student
   * @param {string} studentId - Student ID
   * @param {number} classLevel - Class level
   * @param {string} subject - Optional subject filter
   * @returns {Promise<{total_tests_taken, average_score, topic_breakdown, performance_history}>}
   */
  async getTestAnalytics(studentId, classLevel = 10, subject = null) {
    try {
      const params = new URLSearchParams();
      params.append("class_level", classLevel);
      if (subject) params.append("subject", subject);

      const response = await fetch(`${API_BASE_URL}/api/test/analytics/${studentId}?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Test Analytics API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Test Analytics API Error:", error);
      return null;
    }
  },

  /**
   * Get question bank statistics
   * @returns {Promise<{total_subjects, total_chapters, total_questions, breakdown}>}
   */
  async getQuestionBankStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/test/question-bank/stats`);

      if (!response.ok) {
        throw new Error(`Question Bank Stats API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Question Bank Stats API Error:", error);
      return null;
    }
  },
};

/**
 * Utility: Check backend health
 */
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error("Backend health check failed:", error);
    return false;
  }
};

export default {
  chatService,
  assessmentService,
  userStatsService,
  notesService,
  testService,
  healthCheck,
};
