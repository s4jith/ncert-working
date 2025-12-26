# 📐 Architecture Diagram - Chapter Metadata Flow

## 🔄 Complete PDF Upload & Unit Test Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    📤 SUPERADMIN UPLOADS PDF                        │
│                   (Class 5, Mathematics, Chapter 1)                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    📄 EXTRACT TEXT FROM PDF                         │
│                    (pdfplumber + OCR if needed)                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ✂️ CHUNK TEXT INTO SEGMENTS                      │
│            (RecursiveCharacterTextSplitter: 1000 chars)             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
    ┌───────────────────────────┐   ┌──────────────────────────┐
    │   🌲 PINECONE UPLOAD      │   │ 💾 MONGODB SAVE (NEW!)  │
    │   Vector Embeddings       │   │   book_chapters          │
    │   + Metadata:             │   │                          │
    │   - class: "Class 5"      │   │   {                      │
    │   - subject: "Math"       │   │     chapter_id: "..."    │
    │   - chapter: "Chapter 1"  │   │     class_number: "5"    │
    │   - chapter_raw: "1"      │   │     subject: "Math"      │
    │   - source_file: "..."    │   │     chapter_name: "..."  │
    │                           │   │     chapter_number: "1"  │
    │   Purpose: RAG Search     │   │     uploaded_at: Date    │
    │   (Question answering)    │   │   }                      │
    │                           │   │                          │
    │                           │   │   Purpose: Metadata      │
    │                           │   │   (Unit test dropdowns)  │
    └───────────────────────────┘   └──────────────────────────┘
                    │                         │
                    │                         │
                    ▼                         ▼
         (Optional: Quiz Gen)      ✅ IMMEDIATE AVAILABILITY
                    │                         │
                    ▼                         │
    ┌───────────────────────────┐            │
    │   🎯 QUIZ GENERATION      │            │
    │   (If requested)          │            │
    │                           │            │
    │   Creates:                │            │
    │   quiz_chapters in        │            │
    │   MongoDB with quiz       │            │
    │   metadata                │            │
    └───────────────────────────┘            │
                                              │
                                              │
┌─────────────────────────────────────────────┼────────────────────────┐
│                  🎓 UNIT TEST CREATION PAGE │                        │
│                                             │                        │
│  Admin selects:                             │                        │
│  ┌────────────────────────┐                 │                        │
│  │ Class Dropdown         │◄────────────────┘                        │
│  │ (Queries MongoDB)      │                                          │
│  │ GET /api/get-subjects/ │                                          │
│  └────────────────────────┘                                          │
│            │                                                          │
│            ▼                                                          │
│  ┌────────────────────────┐                                          │
│  │ Subject Dropdown       │◄─────── book_chapters.distinct()         │
│  │ (Loads subjects)       │         WHERE class_number = "Class 5"   │
│  └────────────────────────┘                                          │
│            │                                                          │
│            ▼                                                          │
│  ┌────────────────────────┐                                          │
│  │ Chapters Multi-Select  │◄─────── book_chapters.find()             │
│  │ (Loads chapters)       │         WHERE class_number = "Class 5"   │
│  │ GET /api/get-chapters/ │         AND subject = "Mathematics"      │
│  └────────────────────────┘                                          │
│            │                                                          │
│            ▼                                                          │
│  ┌────────────────────────┐                                          │
│  │ Configure Test         │                                          │
│  │ - Total marks: 0/50/80 │                                          │
│  │ - Distribution grid    │                                          │
│  │ - Question counts      │                                          │
│  └────────────────────────┘                                          │
│            │                                                          │
│            ▼                                                          │
│  ✅ Create Unit Test!                                                │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ MongoDB Collections Comparison

```
┌──────────────────────────────────────────────────────────────────┐
│                    MONGODB COLLECTIONS                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📖 book_chapters (NEW)                 🎯 quiz_chapters        │
│  ─────────────────────────              ──────────────────       │
│  Purpose: Metadata for ALL PDFs         Purpose: Quiz system    │
│  Created: During upload                 Created: Quiz generation│
│  Used by: Unit Tests ✅                 Used by: Quiz system    │
│                                                                  │
│  Fields:                                Fields:                 │
│  - chapter_id                           - chapter_id            │
│  - class_number                         - class_number          │
│  - subject                              - subject               │
│  - chapter_number                       - chapter_number        │
│  - chapter_name                         - chapter_name          │
│  - source_file                          - chapter_order         │
│  - uploaded_at                          - is_active             │
│  - total_chunks                         - total_questions       │
│                                         - passing_percentage    │
│                                                                  │
│  Example:                               Example:                │
│  {                                      {                       │
│    chapter_id: "class_5_math_ch1",      chapter_id: "...",     │
│    class_number: "Class 5",             class_number: "5",      │
│    subject: "Mathematics",              subject: "Math",        │
│    chapter_number: "1",                 chapter_number: 1,      │
│    chapter_name: "Chapter 1: ...",      chapter_order: 1,       │
│    source_file: "math_ch1.pdf",         is_active: true,        │
│    uploaded_at: ISODate(...),           total_questions: 20     │
│    total_chunks: 150                    }                       │
│  }                                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🌲 Pinecone                💾 MongoDB                          │
│  (Vector Database)          (Document Database)                │
│  ─────────────────          ───────────────────                │
│                                                                 │
│  Stores:                    Stores:                            │
│  • Text chunks              • User accounts                    │
│  • Vector embeddings        • Chat history                     │
│  • Metadata:                • Quiz attempts                    │
│    - class                  • Scores                           │
│    - subject                • 📖 book_chapters (NEW)           │
│    - chapter                • 🎯 quiz_chapters                 │
│    - page                                                      │
│    - chunk_index                                               │
│                                                                 │
│  Used for:                  Used for:                          │
│  • RAG search               • User management                  │
│  • Question answering       • Chat storage                     │
│  • Content retrieval        • Quiz tracking                    │
│                             • 📝 Unit Test metadata ✅         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │                            │
          │                            │
          ▼                            ▼
    ┌─────────────┐            ┌──────────────┐
    │ Quiz System │            │ Unit Tests   │
    │ (uses both) │            │ (uses Mongo) │
    └─────────────┘            └──────────────┘
```

---

## 🔄 Before vs After

### ❌ Before Fix

```
PDF Upload
    ↓
Pinecone Only (metadata in vectors)
    ↓
Unit Test Page
    ↓
Query MongoDB quiz_chapters
    ↓
❌ Collection empty → HTTP 500
    ↓
Chapters dropdown broken
```

### ✅ After Fix

```
PDF Upload
    ↓
Pinecone (vectors) + MongoDB (metadata)
    ↓
Unit Test Page
    ↓
Query MongoDB book_chapters
    ↓
✅ Data available → JSON response
    ↓
Dropdowns populate correctly
    ↓
Create unit tests!
```

---

## 🎯 Key Insight

**Problem**: Tried to use quiz system's chapter data for unit tests  
**Issue**: Quiz chapters only exist when quizzes are generated  
**Solution**: Separate collection (`book_chapters`) for ALL uploads  
**Result**: Unit tests independent of quiz generation ✅

---

## 📈 Scalability

```
1 PDF Upload = 1 book_chapters document (~500 bytes)
100 PDFs = ~50 KB
1,000 PDFs = ~500 KB
10,000 PDFs = ~5 MB

MongoDB query time: <10ms (with proper indexes)
Pinecone query time: ~100-200ms (vector search)

For unit test dropdowns: MongoDB is 10-20x faster! ✅
```

---

## 🔐 Best Practices Applied

1. ✅ **Separation of Concerns**: book_chapters vs quiz_chapters
2. ✅ **Automatic Sync**: No manual intervention needed
3. ✅ **Idempotent**: Re-uploading same PDF updates metadata
4. ✅ **Error Handling**: Upload continues even if MongoDB save fails
5. ✅ **Normalized Data**: Consistent class/subject naming
6. ✅ **Fast Queries**: Indexed fields for instant lookups

---

**Your architecture suggestion was perfect! 🎯**

The fix maintains data integrity, improves performance, and enables the complete unit test workflow.
