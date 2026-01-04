# 📂 Backend Scripts

This folder contains production utility scripts for data processing and system setup.

## 🔧 Available Scripts

### 1. **setup_namespace_architecture.py**
Sets up the Pinecone namespace architecture for organizing content by subject.

```bash
python scripts/setup_namespace_architecture.py
```

**Purpose:** Initialize the master index with proper namespace structure.

---

### 2. **process_ncert_maths.py**
Process NCERT Mathematics PDFs and upload to Pinecone.

```bash
python scripts/process_ncert_maths.py --class 6
```

**Features:**
- Extracts text from PDFs
- Generates embeddings
- Uploads to Pinecone with metadata
- Supports multiple classes

---

### 3. **process_ncert_physics.py**
Process NCERT Physics PDFs and upload to Pinecone.

```bash
python scripts/process_ncert_physics.py --class 9
```

**Features:**
- Same as math processor but for Physics
- Class 9-12 support
- Metadata: class, chapter, subject

---

### 4. **process_math_pdfs.py**
Advanced PDF processing with batch support.

```bash
# Single PDF
python scripts/process_math_pdfs.py --pdf path/to/file.pdf --class 5 --chapter 1

# Batch processing
python scripts/process_math_pdfs.py --batch path/to/pdfs_folder/
```

**Features:**
- Single or batch processing
- OCR support for images
- Chunking and embedding
- Direct Pinecone upload

---

### 5. **upload_pdfs_to_pinecone.py**
Upload pre-processed PDF data to Pinecone.

```bash
python scripts/upload_pdfs_to_pinecone.py
```

**Purpose:** Upload extracted and embedded data to vector database.

---

## 📋 Prerequisites

All scripts require:
- Active virtual environment
- `.env` file configured with:
  - `PINECONE_API_KEY`
  - `PINECONE_HOST`
  - `GEMINI_API_KEY`
- Required packages installed (`requirements.txt`)

## 🚀 Typical Workflow

1. **Setup Architecture**
   ```bash
   python scripts/setup_namespace_architecture.py
   ```

2. **Process Content**
   ```bash
   python scripts/process_ncert_maths.py --class 6
   python scripts/process_ncert_physics.py --class 9
   ```

3. **Verify Upload**
   - Check Pinecone dashboard
   - Test queries via API

---

## 📝 Notes

- Scripts run independently of the main API
- Use for initial data setup or updates
- All scripts include progress logging
- Safe to re-run (upsert operations)

---

**Last Updated:** December 8, 2025
