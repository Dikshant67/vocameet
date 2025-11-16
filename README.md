# 🗣️ VocaMeet — Voice-Enabled Meeting Scheduler

## 🚀 Project Overview
**VocaMeet** is a **voice-enabled meeting scheduling platform** that allows users to book appointments with experts using **natural language voice interactions**.

The application consists of three main routes:
- `/` → **Landing Page** — introduction and branding
- `/features` → **Features Page** — overview of platform capabilities
- `/dashboard` → **Dashboard** — main voice agent interaction area

---

## 🏗️ Architecture

### 🖥️ Frontend
- Built with **Next.js** and **React**
- Integrates **LiveKit** for **real-time voice communication**
- Supports:
  - Voice interaction  
  - Audio visualization
  - Live Transcription
- Provides a modern UI for seamless meeting scheduling and voice-based interactions.

---

### ⚙️ Backend
- Developed using **Python (FastAPI)**
- Uses **SQLite** for persistence, managed via **SQLAlchemy ORM**
- Core database modules handle:
  - User and Expert management  
  - Appointment scheduling  
  - Conversation and feedback logging  
  - Authentication and OAuth token storage

Database logic combines:
- ORM models for standard operations  
- A custom `AppDatabase` class for **token handling and specialized queries**

---

## 🧩 Getting Started

### 🖥️ Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```
### ⚙️ Backend Setup
```
cd backend
uv sync
uvicorn app:main --reload
```
 This will 
- Install and sync dependencies using uv

- Start the FastAPI server locally (default: http://127.0.0.1:8000)

- To start the voice meeting agent service, run:
```
python agent.py start
uvicorn app:main
```

Access the application at:
👉 http://localhost:3000

### ⚙️ Configuration
🔐 LiveKit Credentials
Configure LiveKit connection details in .env.local:
```

GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/callback/google
GOOGLE_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=eastus2
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-03-01-preview
NEXTAUTH_SECRET=
```
### 🎨 Customization
You can update platform branding and feature toggles inside:
app-config.ts

## 🌟 Features

- 🗣️ Voice-Based Scheduling	Book appointments using natural language voice commands
- 🔊 Real-Time Communication	LiveKit-powered bi-directional voice streaming
- 👨‍🏫 Expert Management	Manage expert profiles and availability
- 📅 Calendar Integration	Sync with Google Calendar and Outlook
- 💬 Conversation History	Store all user-agent interactions with sentiment analysis
- ⭐ Feedback System	Collect ratings and reviews after appointments

🧱 Notes
- download livekit server from here (https://github.com/livekit/livekit/releases)

The backend database layer implements a dual approach:

Standard ORM for persistent models

A custom AppDatabase class for efficient OAuth and scheduling operations

