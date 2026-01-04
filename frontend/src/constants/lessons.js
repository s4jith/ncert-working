/**
 * Lessons Configuration
 * 
 * Contains chapter information for different subjects.
 * Currently we have PDFs in /public folder for:
 * - Mathematics (fegp1XX.pdf) - Has backend RAG support
 * - Social Science (fees1XX.pdf) - PDFs only, no backend RAG yet
 * 
 * TODO: Move this to backend API
 * Replace static data with dynamic API call: GET /api/lessons
 */

// Mathematics Chapters (Class 6) - HAS BACKEND RAG SUPPORT
export const MATH_LESSONS = [
  {
    id: 1,
    number: 1,
    title: "Patterns in Mathematics",
    description: "Exploring patterns in numbers, shapes, and their relationships.",
    pdfUrl: "/fegp101.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 2,
    number: 2,
    title: "Lines and Angles",
    description: "Understanding different types of lines, angles, and their properties.",
    pdfUrl: "/fegp102.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 3,
    number: 3,
    title: "Number Play",
    description: "Playing with numbers, divisibility rules, and number patterns.",
    pdfUrl: "/fegp103.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 4,
    number: 4,
    title: "Data Handling and Presentation",
    description: "Collecting, organizing, and representing data using graphs and charts.",
    pdfUrl: "/fegp104.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 5,
    number: 5,
    title: "Prime Time",
    description: "Understanding prime numbers, factors, and multiples.",
    pdfUrl: "/fegp105.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 6,
    number: 6,
    title: "Perimeter and Area",
    description: "Calculating perimeter and area of various shapes.",
    pdfUrl: "/fegp106.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 7,
    number: 7,
    title: "Fractions",
    description: "Understanding fractions, equivalent fractions, and operations.",
    pdfUrl: "/fegp107.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 8,
    number: 8,
    title: "Playing with Constructions",
    description: "Geometric constructions using compass and ruler.",
    pdfUrl: "/fegp108.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 9,
    number: 9,
    title: "Symmetry",
    description: "Exploring symmetry in shapes and patterns.",
    pdfUrl: "/fegp109.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
  {
    id: 10,
    number: 10,
    title: "The Other Side of Zero",
    description: "Introduction to negative numbers and integers.",
    pdfUrl: "/fegp110.pdf",
    subject: "Mathematics",
    classLevel: 6,
  },
];

// Social Science Chapters (Class 6) - PDFs available, no backend RAG yet
export const SOCIAL_SCIENCE_LESSONS = [
  {
    id: 1,
    number: 1,
    title: "Locating Places on the Earth",
    description: "Directions on maps, latitude, longitude, time zones, and the International Date Line.",
    pdfUrl: "/fees101.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 2,
    number: 2,
    title: "Oceans and Continents",
    description: "Identification of continents, oceans, climate, and their effect on patterns of life.",
    pdfUrl: "/fees102.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 3,
    number: 3,
    title: "Landforms and Life",
    description: "Types of landforms, their features, and how they shape livelihoods.",
    pdfUrl: "/fees103.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 4,
    number: 4,
    title: "Timeline and Sources of History",
    description: "Measuring time in history and recognizing sources and life of early humans.",
    pdfUrl: "/fees104.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 5,
    number: 5,
    title: "The Beginning of Indian Civilization",
    description: "Distinctive features of important towns (e.g., Harappa) and continuity of civilization.",
    pdfUrl: "/fees105.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 6,
    number: 6,
    title: "India, That Is Bharat",
    description: "Roots of India's name, unity in diversity, and heritage.",
    pdfUrl: "/fees106.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 7,
    number: 7,
    title: "India's Cultural Roots",
    description: "Tracing the roots and traditions that shaped Indian society.",
    pdfUrl: "/fees107.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 8,
    number: 8,
    title: "Unity in Diversity",
    description: "How diversity enriches our country through food, festivals, textiles, and epics.",
    pdfUrl: "/fees108.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 9,
    number: 9,
    title: "Family and Community",
    description: "Importance and role of family and community in nation-building.",
    pdfUrl: "/fees109.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 10,
    number: 10,
    title: "Grassroot Democracy (Governance)",
    description: "Levels and parts of governance, power sharing, and the Constitution.",
    pdfUrl: "/fees110.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 11,
    number: 11,
    title: "Grassroot Democracy – Local Government in Rural Areas",
    description: "Functioning of rural administration and local self-government.",
    pdfUrl: "/fees111.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 12,
    number: 12,
    title: "Grassroot Democracy – Local Government in Urban Areas",
    description: "Role of urban local bodies and civic administration.",
    pdfUrl: "/fees112.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 13,
    number: 13,
    title: "The Value of Work",
    description: "Difference between economic and non-economic activity, value of community work.",
    pdfUrl: "/fees113.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
  {
    id: 14,
    number: 14,
    title: "Economic Activities Around Us",
    description: "Production, trade, consumption, and differentiating economic sectors.",
    pdfUrl: "/fees114.pdf",
    subject: "Social Science",
    classLevel: 6,
  },
];

// Get lessons by subject
export function getLessonsBySubject(subject) {
  switch (subject) {
    case "Mathematics":
      return MATH_LESSONS;
    case "Social Science":
      return SOCIAL_SCIENCE_LESSONS;
    default:
      return []; // Return empty array - no fallback to avoid showing wrong subject content
  }
}

// Export SAMPLE_LESSONS as MATH_LESSONS for backward compatibility
// Since we have RAG support for Mathematics, use it as default
export const SAMPLE_LESSONS = MATH_LESSONS;

// Available subjects with RAG support
export const SUBJECTS_WITH_RAG = ["Mathematics"];

// All available subjects
export const ALL_SUBJECTS = ["Mathematics", "Social Science"];
