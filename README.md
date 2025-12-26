# NCERT Doubt-Solver v2.0

Multilingual NCERT Doubt-Solver using OPEA-based RAG Pipeline

## 🚀 Quick Start

```powershell
.\START.ps1
```

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
ncert-working/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── services/       # RAG, LLM, OCR
│   │   └── db/             # Pinecone + MongoDB
│   ├── .env                # Configuration
│   └── requirements.txt
├── frontend/               # React + Vite
│   └── src/
│       ├── pages/          # UI screens
│       └── components/     # Reusable UI
└── docs/                   # Documentation
```

## 🔧 Configuration

Edit `backend/.env`:
```env
PINECONE_API_KEY=your-key
MONGODB_URI=mongodb+srv://...
GEMINI_API_KEY=your-key
```

## 🎯 Features

- ✅ RAG Pipeline with Pinecone
- ✅ Multi-LLM (Gemini/OpenAI/Local)
- ✅ Multilingual (EN, HI, UR)
- ✅ JWT Authentication
- ✅ Quiz System
- ✅ Modern React UI
