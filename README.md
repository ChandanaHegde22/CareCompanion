# 🏥 CareCompanion – AI-Powered Elderly Care & Emotional Support

<div align="center">

![CareCompanion Banner](https://img.shields.io/badge/CareCompanion-AI%20Elderly%20Care-6C63FF?style=for-the-badge&logo=heart&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red?style=for-the-badge&logo=streamlit)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-orange?style=for-the-badge&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A production-ready, full-stack AI assistant designed specifically for elderly individuals.**  
Provides emotional companionship, medication management, medical document Q&A, emergency alerts, and much more.

</div>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Running the App](#-running-the-app)
- [Docker Deployment](#-docker-deployment)
- [Testing](#-testing)
- [Screenshots](#-screenshots)
- [API Reference](#-api-reference)
- [Future Scope](#-future-scope)

---

## 🌟 Project Overview

CareCompanion is a **Master's-level AI engineering project** that combines cutting-edge language models, retrieval-augmented generation (RAG), voice interaction, and real-time emergency detection into a single, beautiful Streamlit application tailored for elderly users.

### Why CareCompanion?

- 👴 **Elder-first UX** – Large fonts, simple navigation, warm colours, gentle language
- 🤖 **AI Companion** – Powered by Google Gemini 2.0 Flash with long-term memory
- 📋 **Medical RAG** – Answers questions from uploaded health reports with zero hallucination
- 🚨 **Emergency Detection** – Real-time keyword + AI detection with SMS/email alerts
- 💊 **Medicine Tracker** – Full adherence monitoring and reminders
- 🎙️ **Voice Interface** – Speak naturally, get voiced responses
- 🌐 **Multilingual** – English, Hindi, Kannada support

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  app.py ─── pages/ ─── assets/style.css                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Services Layer                            │
│  auth ─ chat ─ mood ─ medicine ─ reminder ─ emergency       │
│  memory ─ notes ─ caregiver                                 │
└──────────┬───────────────┬───────────────────┬─────────────┘
           │               │                   │
┌──────────▼──────┐ ┌──────▼───────┐ ┌────────▼──────────────┐
│   Google Gemini │ │  FAISS + RAG │ │   SQLite Database     │
│   2.0 Flash AI  │ │  Sentence    │ │   + APScheduler       │
│   (Chat/Mood/   │ │  Transformers│ │   + Twilio SMS        │
│   Emergency)    │ │  (Embeddings)│ │   + gTTS/STT          │
└─────────────────┘ └──────────────┘ └───────────────────────┘
```

### Data Flow – Medical RAG

```
Upload PDF/DOCX/TXT
       │
       ▼
Document Processor (pdfplumber / PyMuPDF / python-docx)
       │
       ▼
Text Chunker (500 chars, 60 overlap)
       │
       ▼
Sentence Transformer Embeddings (all-MiniLM-L6-v2, 384-dim)
       │
       ▼
FAISS Index (per-user, persisted to disk)
       │
User Query ──▶ Embed Query ──▶ FAISS Search (top-k=5)
                                     │
                                     ▼
                          Gemini 2.0 Flash (RAG Prompt)
                                     │
                                     ▼
                          Answer + Citations (no hallucination)
```

---

## ✨ Features

| Module | Features |
|--------|----------|
| 🔐 **Auth** | Register, Login, Profile, Password change, Session management |
| 💬 **AI Chat** | Gemini-powered, context memory, mood detection, emergency detection, TTS |
| 🎭 **Mood Tracker** | AI mood analysis, daily logging, weekly/monthly Plotly charts |
| 💊 **Medicines** | Add/edit/delete, dosage tracking, adherence %, daily schedule |
| ⏰ **Reminders** | Routine tasks, calendar view, completion tracking, quick presets |
| 📋 **Medical RAG** | PDF/DOCX/TXT upload, FAISS retrieval, Gemini Q&A with citations |
| 🎙️ **Voice** | Push-to-talk STT, TTS playback, multilingual (EN/HI/KN) |
| 🚨 **Emergency** | Real-time detection, SOS buttons, SMS/email alerts, contact management |
| 👥 **Caregiver** | Dashboard, patient linking, adherence overview, mood graphs |
| 📊 **Analytics** | Comprehensive Plotly dashboards for all health metrics |
| 📝 **Notes** | Health diary, voice notes, search, templates, TTS playback |
| ⚙️ **Settings** | Language, theme, voice speed, notifications, data export |
| 🧠 **AI Memory** | Long-term memory for people, preferences, routines, medical info |

---

## 📁 Project Structure

```
CareCompanion/
├── app.py                    # 🚀 Main entry point
├── config.py                 # ⚙️ Configuration & env vars
├── requirements.txt          # 📦 Dependencies
├── Dockerfile                # 🐳 Docker configuration
├── .env.example              # 🔑 Environment template
├── README.md                 # 📖 This file
│
├── database/
│   ├── connection.py         # SQLite context manager
│   └── schema.py             # Full DB schema + init
│
├── authentication/
│   └── auth.py               # Password hashing + session
│
├── services/
│   ├── auth_service.py       # User auth & profile ops
│   ├── chat_service.py       # Gemini AI chat
│   ├── mood_service.py       # Mood detection & logging
│   ├── medicine_service.py   # Medicine CRUD & adherence
│   ├── reminder_service.py   # Reminder CRUD & completion
│   ├── emergency_service.py  # Emergency logging & alerts
│   ├── memory_service.py     # AI long-term memory
│   ├── notes_service.py      # Notes management
│   └── caregiver_service.py  # Caregiver dashboard
│
├── rag/
│   ├── document_processor.py # PDF/DOCX/TXT extraction
│   ├── embedder.py           # Sentence Transformer embeddings
│   ├── retriever.py          # FAISS index management
│   └── rag_chain.py          # Complete RAG pipeline
│
├── speech/
│   ├── stt.py                # Speech-to-Text (SpeechRecognition)
│   └── tts.py                # Text-to-Speech (gTTS)
│
├── scheduler/
│   └── reminder_scheduler.py # APScheduler background jobs
│
├── utils/
│   ├── helpers.py            # General utilities
│   ├── validators.py         # Input validation
│   ├── translator.py         # deep-translator (EN/HI/KN)
│   └── emergency_detector.py # Keyword + pattern detection
│
├── prompts/
│   ├── companion_prompt.py   # AI companion system prompt
│   ├── mood_prompt.py        # Mood analysis prompt
│   ├── rag_prompt.py         # Medical RAG prompt
│   └── emergency_prompt.py   # Emergency response prompt
│
├── pages/
│   ├── home.py               # Dashboard
│   ├── chat.py               # AI Chat
│   ├── mood.py               # Mood Tracker
│   ├── medicines.py          # Medicine Manager
│   ├── reminders.py          # Reminders
│   ├── rag_assistant.py      # Medical Q&A
│   ├── voice.py              # Voice Assistant
│   ├── emergency.py          # Emergency Center
│   ├── caregiver.py          # Caregiver Dashboard
│   ├── analytics.py          # Health Analytics
│   ├── notes.py              # Notes & Diary
│   ├── settings.py           # Settings
│   └── profile.py            # Profile & Memory
│
├── assets/
│   └── style.css             # Custom CSS theme
│
├── tests/
│   ├── test_auth.py          # Auth unit tests
│   ├── test_mood.py          # Mood unit tests
│   ├── test_medicine.py      # Medicine unit tests
│   ├── test_emergency.py     # Emergency unit tests
│   └── test_rag.py           # RAG pipeline tests
│
├── uploads/                  # User uploaded documents
├── vector_store/             # FAISS indices (per user)
└── logs/                     # Application logs
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Frontend** | Streamlit 1.36+ |
| **AI Model** | Google Gemini 2.0 Flash |
| **RAG Framework** | LangChain + FAISS-CPU |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **Database** | SQLite (WAL mode) |
| **Speech-to-Text** | SpeechRecognition + Google Web Speech API |
| **Text-to-Speech** | gTTS (Google Text-to-Speech) |
| **Scheduler** | APScheduler (BackgroundScheduler) |
| **Charts** | Plotly |
| **PDF Parsing** | pdfplumber + PyMuPDF |
| **DOCX Parsing** | python-docx |
| **Auth** | bcrypt (rounds=12) |
| **Translation** | deep-translator (Google backend) |
| **SMS Alerts** | Twilio |
| **Testing** | pytest + pytest-mock |
| **Deployment** | Docker |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key (free at [ai.google.dev](https://ai.google.dev))
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CareCompanion.git
cd CareCompanion
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `pyaudio` may require additional system packages:
> - Ubuntu/Debian: `sudo apt-get install portaudio19-dev`
> - macOS: `brew install portaudio`
> - Windows: Install from wheel at https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### 4. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Optional for SMS alerts
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google AI Studio API Key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `DATABASE_PATH` | `database/carecompanion.db` | SQLite file path |
| `VECTOR_STORE_PATH` | `vector_store/` | FAISS index directory |
| `UPLOADS_PATH` | `uploads/` | Document upload directory |
| `TWILIO_ACCOUNT_SID` | *(optional)* | Twilio SID for SMS |
| `TWILIO_AUTH_TOKEN` | *(optional)* | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | *(optional)* | Twilio sender number |
| `MAX_UPLOAD_MB` | `20` | Max document upload size |

---

## 🚀 Running the App

```bash
streamlit run app.py
```

The app will be available at **http://localhost:8501**

### First Run

1. Open http://localhost:8501
2. Click **"📝 Register"** and create an account
3. Log in with your credentials
4. Navigate to **⚙️ Settings** to set your language and theme
5. Start chatting with your AI companion!

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t carecompanion:latest .
```

### Run Container

```bash
docker run -d \
  --name carecompanion \
  -p 8501:8501 \
  -e GEMINI_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/database \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/vector_store:/app/vector_store \
  carecompanion:latest
```

### Docker Compose (recommended)

```yaml
version: '3.8'
services:
  carecompanion:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=gemini-2.0-flash
    volumes:
      - ./data/db:/app/database
      - ./data/uploads:/app/uploads
      - ./data/vectors:/app/vector_store
      - ./data/logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
docker-compose up -d
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_auth.py -v
pytest tests/test_mood.py -v
pytest tests/test_emergency.py -v
pytest tests/test_medicine.py -v
pytest tests/test_rag.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Authentication | 18 | ~95% |
| Mood Service | 17 | ~90% |
| Medicine Service | 16 | ~92% |
| Emergency Detection | 22 | ~94% |
| RAG Pipeline | 14 | ~85% |

---

## 📸 Screenshots

> *Screenshots would go here in a real deployment*

| Page | Description |
|------|-------------|
| 🏠 Home | Welcome dashboard with today's summary |
| 💬 Chat | AI companion with conversation bubbles |
| 🎭 Mood | Mood picker + Plotly charts |
| 💊 Medicines | Daily schedule + adherence progress |
| 📋 Medical Q&A | Document upload + cited AI answers |
| 🚨 Emergency | SOS buttons + contact notification |
| 📊 Analytics | Full health analytics dashboard |

---

## 🔌 API Reference

### Core Services

#### `chat_service.send_message()`
```python
result = send_message(
    user_id=1,
    message="How should I take my medicine?",
    language="en",
    session_history=[]
)
# Returns: {"success": bool, "response": str, "is_emergency": bool}
```

#### `rag_chain.answer_medical_query()`
```python
result = answer_medical_query(user_id=1, query="What is my blood pressure?")
# Returns: {"success": bool, "answer": str, "sources": list, "chunks_used": int}
```

#### `emergency_detector.detect_emergency()`
```python
result = detect_emergency("I fell down and can't get up")
# Returns: {"is_emergency": True, "emergency_type": "fall", "severity": "medium"}
```

---

## 🔮 Future Scope

| Feature | Priority | Status |
|---------|----------|--------|
| 🧠 Advanced AI Memory (vector-based) | High | Planned |
| 📱 Mobile App (React Native) | High | Planned |
| 🔔 Push Notifications (Firebase) | High | Planned |
| 🎯 Personalized Health Recommendations | Medium | Planned |
| 🏥 EHR Integration (HL7/FHIR) | Medium | Research |
| 📊 Wearable Device Integration | Medium | Research |
| 🤝 Telemedicine Integration | Medium | Planned |
| 🌍 More Languages (Tamil, Telugu, Bengali) | Medium | Planned |
| 🎮 Cognitive Games for Mental Health | Low | Planned |
| 🔒 End-to-End Encryption | High | Planned |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License – see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**CareCompanion** — Built as a Masters-level AI Engineering Project  
Demonstrating: Gemini AI · RAG · FAISS · Streamlit · SQLite · APScheduler · gTTS

---

<div align="center">

**Made with ❤️ for the elderly community**

*CareCompanion — Because every grandparent deserves a caring AI companion*

</div>
