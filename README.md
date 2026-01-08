# NCERT AI Learning Platform 🎓

A full-stack AI-powered educational platform built with **FastAPI**, **React**, and **Intel OpenVINO** for optimized performance on Intel hardware.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![Intel OpenVINO](https://img.shields.io/badge/Intel-OpenVINO-0071C5?logo=intel&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-000000?logo=pinecone&logoColor=white)

</div>

---

## ✨ Core Features

- **AI-Powered Learning Assistant** with multimodal inputs
- **Multi-role System** (Student, Teacher, Admin)
- **Real-time Performance Analytics**
- **Multilingual Support** (English + Indian languages)
- **Optimized Edge AI** with Intel OpenVINO

---

## 🏗️ Tech Architecture

```text
project/
├── backend/                 # FastAPI + OpenVINO
│   ├── app/                 # 22+ API Routers
│   ├── services/            # 25+ AI Services
│   ├── models/              # OpenVINO Models (Git LFS)
│   └── requirements.txt
│
├── frontend/                # React 19 + Vite
│   ├── src/                 # 22 Pages + Components
│   ├── stores/              # Zustand State Management
│   └── package.json
│
└── docs/                    # Technical Documentation
```

---

## 🚀 Quick Start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your keys
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: `http://localhost:5173`
- API Docs: `http://localhost:8000/docs`

---

## 🔌 Tech Stack

| Backend | Frontend | AI/ML | Database |
|---------|----------|-------|----------|
| FastAPI | React 19 | Intel OpenVINO | MongoDB Atlas |
| Python 3.10+ | Vite | Gemini 2.0 | Pinecone |
| Pydantic | Tailwind | Multilingual RAG | Redis Cache |

---

## ⚡ Performance Features

- **OpenVINO OCR** - Local text recognition
- **Edge LLM Inference** - Reduced API costs
- **Optimized RAG** - Max 2 API calls/query
- **Multi-key Rotation** - Sustainable scaling
- **Caching Layer** - Redis + MongoDB

---

## 📊 API Categories

```text
Core:   /api/chat/, /api/mcq/, /api/books/
Admin:  /api/admin/, /api/tests/
User:   /api/auth/, /api/user/, /api/support/
Intel:  /api/admin/intel-status, /api/optimized-chat/
```

---

## 🔐 Environment Setup

### Backend `.env`:

```text
GEMINI_API_KEY=your_key
PINECONE_API_KEY=your_key
MONGO_URI=your_mongo_uri
```

### Frontend `.env`:

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 🎯 Production Ready

- ✅ Multi-tenant Architecture
- ✅ API Rate Limiting
- ✅ Performance Monitoring
- ✅ Error Logging
- ✅ CORS & Security Headers

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

